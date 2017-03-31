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
            result = self.fact_query(action)
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
        
    def fact_query(self,query):
        """ Test a fact,  """
        if not isinstance(query,ELBD.ELQUERY):
            raise ELE.ELConsistencyException('Querying requires the use of a query')

        current_frame = self.top_stack()
        if len(current_frame) == 0:
            return ELBD.ELFail()
        #fill in any variables from the current bindings
        bound = [query.bind(x) for x in current_frame]
        #then query
        results = [self.trie.query(x) for x in bound]
        #then integrate into bindings:
        successes = [x for x in results if x == True]
        updated_frame = [bindPair[1] for x in successes for bindPair in x.bindings]
        self.replace_stack(updated_frame)

        
        if len(updated_frame) > 0:        
            return successes
        else:
            return ELBD.ELFail()

    def run_rule(self,rule):
        """ Given a rule, check its conditions then queue its results """
        self.add_stack()
        truthiness = False
        condition_truths_and_bindings = [self.fact_query(x) for x in rule.conditions]
        if len(condition_truths_and_bindings) == 0 or isinstance(condition_truths_and_bindings[-1], ELBD.ELFail):
            self.pop_stack()
            return
        
        final_bindings = self.top_stack()
        #add retrieved values from conditions as bindings

        #perform comparisons

        #select a still viable rule
        selection = choice(final_bindings)
        
        #todo: make the parser check for unbound variables before adding to runtime
        for action in rule.actions:
            bound_action = action.bind(selection)
            self.act(bound_action)
        #then pop the frame off
        self.pop_stack()

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
