"""
	A Trie based runtime for EL
"""
import logging as root_logger
logging = root_logger.getLogger(__name__)


from enum import Enum
from collections import namedtuple
from fractions import Fraction
from random import choice
import IPython
import ELParser
from ELParser import ELParser, ELTrie
from ELParser import ELBaseData as ELBD
from ELParser import ELExceptions as ELE
from ELParser.ELCompFunctions import get_COMP_FUNC, get_ARITH_FUNC


class ELRuntime:
    """ The Unified EL Runtime,
    Parses strings into IRs, which are acted upon.
    """

    def __init__(self):
        self.parser = ELParser.ELPARSE
        self.trie = ELTrie.ELTrie()
        #Rule dictionary using hash(repr(rule))
        self.rules = {}
        #list of tuples (asserted, retracted) for each action?
        self.history = []
        #2d stack of binding possibilities
        #ie: bindings[0] = set({}) where each {} is a set of bindings
        self.bindings = [[{}]]

    def __call__(self,string):
        """ Parse a string, act accordingly with the results """
        parsed_representations = self.parser(string)
        #todo: return a {status: bool, data: [] } obj
        actResults = []
        for r in parsed_representations:
            actResults.append(self.act(r))
            
        if len(actResults) == 0:
            return None
        if len(actResults) == 1:
            return actResults[0]
        else:
            return actResults

    def add_stack(self):
        current = self.bindings[-1]
        copied = [x.copy() for x in current]
        self.bindings.append(copied)

    def replace_stack(self,frame):
        self.bindings[-1] = frame

    def top_stack(self):
        return self.bindings[-1]
        
    def pop_stack(self):
        self.bindings.pop()
    
    def run(self):
        """ run the simulation """
        None
        
    def act(self,action):
        """ Given an action (one of ELBDs action types),
        perform it
        """
        result = None
        #Perform based on parsed type
        if isinstance(action,ELBD.ELFACT):
            #Fact: Assert /retract
            if action.negated:
                logging.debug("Hit a negation, retracting")
                result = self.fact_retract(action)
            else:
                logging.debug("Hit an assertion")
                result = self.fact_assert(action)
        elif isinstance(action,ELBD.ELRULE):
            result = self.run_rule(action)
        elif isinstance(action,ELBD.ELBIND):
            #Binding, update current stack
            self.set_binding(action.var,action.root)
        elif isinstance(action,ELBD.ELARITH_FACT):
            #todo: enact arithmetic on the fact /binding
            None
        elif isinstance(action,ELBD.ELQUERY):
            #Don't replace vars with bindings, populate them
            logging.info("Querying")
            self.add_stack()
            result = self.fact_query(action, self.top_stack())[0]
            self.pop_stack()
            logging.info('Query Result: {}'.format(result))

        return result

    def act_on_array(self, actions): #todo
        """ Given a collection of actions, perform each """
        if any([not isinstance(x,ELBD.ELAction) for x in actions]):
            raise Exception("An Action is invalid")


    def fact_assert(self,fact):
        """ Add a fact """
        #todo: bind?
        #bindings are ELVAR -> ELPAIR in f(fact)->fact
        
        self.trie.push(fact)
        if isinstance(fact[-1].value, ELBD.ELRULE):
            self.add_rule(fact.short_str(), fact[-1].value)

    def fact_retract(self,fact):
        """ Remove a fact """
        #todo: fill out bindings?
        self.trie.pop(fact)
        if isinstance(fact[-1].value, ELBD.ELRULE):
            self.remove_rule(fact.short_str())
        
    def fact_query(self,query, bindingFrame=None):
        if bindingFrame is None:
            bindingFrame = self.top_stack()
        """ Test a fact, BE CAREFUL IT MODIFES THE TOP OF THE VAR STACK  """
        if not isinstance(query,ELBD.ELQUERY):
            raise ELE.ELConsistencyException('Querying requires the use of a query')

        current_frame = bindingFrame
        if len(current_frame) == 0:
            return ELBD.ELFail()
        #fill in any variables from the current bindings
        bound = [query.bind(x) for x in current_frame]
        #then query
        results = [self.trie.query(x) for x in bound]
        #then integrate into bindings:
        successes = [x for x in results if x == True]
        updated_frame = [bindPair[1] for x in successes for bindPair in x.bindings]

        #a frame is valid if it has at least ELSuccess(none,{}) in it
        if len(updated_frame) > 0:        
            return (successes, updated_frame)
        else:
            return (ELBD.ELFail(), current_frame)

    def run_rule(self,rule):
        """ Given a rule, check its conditions then queue its results """
        returnVal = ELBD.ELFail()
        try:
            self.add_stack()
            current_frame = self.top_stack()
            successes = []
            for condition in rule.conditions:
                successes, current_frame = self.fact_query(condition, current_frame)
                if isinstance(successes, ELBD.ELFail):
                    raise ELE.ELRuleException()

            # passing_bindings :: [ {} ]
            passing_bindings = current_frame
            #get the comparison functions, as a tuple 
            comp_tuple = self.format_comparisons(rule)
            compared_bindings = self.filter_by_comparisons(comp_tuple, passing_bindings)
            if len(compared_bindings) == 0:
                raise ELE.ELRuleException()

            
            #select a still viable rule
            #todo: add variability here. utility, curves, distributions,
            #round_robins? state?
            selection = choice(compared_bindings)

            #perform modifications to bindings
            

            
            #todo: make the parser check for unbound variables before adding to runtime
            for action in rule.actions:
                bound_action = action.bind(selection)
                self.act(bound_action)

            returnVal = ELBD.ELSuccess()
        except ELE.ELRuleException:
            None
        finally:
            #then pop the frame off
            self.pop_stack()
        return returnVal

    def format_comparisons(self, rule):
        #get the bindings from the rule
        retrieved = [(comp, get_COMP_FUNC(comp.op)) for comp in rule.binding_comparisons]
        return retrieved
    

    def filter_by_comparisons(self, comparison_tuples, potential_bindings):
        #potential_bindings :: [ {} ]
        #for each binding
        compared_bindings = potential_bindings
        for comp, func in comparison_tuples:
            compared_bindings = [x for x in compared_bindings if self.run_function(x, func, comp)]
        return compared_bindings
        
    def run_function(self, binding, func, comparison):
        #get values from bindings:
        if comparison.b1.value not in binding or comparison.b2.value not in binding :
            raise ELE.ELConsistencyException('Comparison being run without the necessary bindings')
        #todo: have a 'get variable from binding' function to take into account array access?
        val1 = binding[comparison.b1.value]
        val2 = binding[comparison.b2.value]
        if comparison.op == ELBD.ELCOMP.NEAR:
            if isinstance(comparison.nearVal, ELBD.ELVAR):
                nearVal = binding[comparison.nearVal.value]
            else:
                nearVal = comparison.nearVal

            return func(val1, nearVal, val2)
        else:
            return func(val1, val2)

    
    def format_string(self,format_string):
        """ Given a format_string, use defined variables in the runtime
        to fill it in """
        #todo: Take a string of "this is a $x test", and replace $x with the variable val
        None

    def subtree_query(self, interface_string):
        """ Verify the trie location fulfills the defined interface """
        None

    def subtree_application(self, subtree_application):
        """ Apply the subtree to the given location """
        None

    #Rule store:
    def add_rule(self,name,rule):
        if name in self.rules:
            raise ELE.ELConsistencyException('{} already stored as a rule already'.format(name))
        self.rules[name] = rule        

    def remove_rule(self,name):
        if name in self.rules:
            del self.rules[name]

    def get_rule(self,name):
        if name not in self.rules:
            raise ELE.ELConsistencyException('{} : Getting a rule, but its not in the dict'.format(name))
        return self.rules[name]
            
    #history:
    def add_change(self,changes):
        None
    def rewind_change(self,changes):
        None
    
        
    #### METRICS
    def max_depth(self):
        None
    def num_leaves(self):
        None
    def num_rules(self):
        None
    def num_assertions(self):
        None
    def num_retractions(self):
        None
        
    #EXPORTING
    def export_to_string(self):
        """ TODO: print out every leaf path of the trie """
        None
