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
from . import ELParser, ELTrie
from . import ELBaseData as ELBD
from . import ELExceptions as ELE
from . ELCompFunctions import get_COMP_FUNC, get_ARITH_FUNC


class ELRuntime:
    """ The Unified EL Runtime,
    Parses strings into IRs, which are acted upon.
    """

    def __init__(self):
        self.parser = ELParser.ELPARSE
        self.trie = ELTrie.ELTrie()
        #list of tuples (asserted, retracted) for each action?
        self.history = []
        #bindings :: stack<ELBindingFrame>
        self.bindings = ELBD.ELBindingStack()

    def execute(self, etype, data):
        return_val = []
        if etype is ELBD.ELEXT.TRIE:
            return_val = self.execute_as_trie(data)
        elif etype is ELBD.ELEXT.TREE:
            None
        elif etype is ELBD.ELEXT.FSM:
            None
        elif etype is ELBD.ELEXT.SEL:
            None
        elif etype is ELBD.ELEXT.INS:
            None
        else:
            raise ELE.ELNotImplementedException()

        return return_val

    def execute_as_trie(self, data):
        """
        Data{ root: '.a.start.string?, }
        Assumes structure where each node has a 'next' child,
        .node.next.[...],
        .node.conditions.[]
        .node.mods.[]
        .node.performance."blah"
        .node.weight!n
        .node.rules...
        ....
        """

        output = ["Start"]
        state = []
        #Get the starting node
        current = self(data['root'])
        
        while len(current) > 0:
            #perform any statemods
            
            #Add text to the output
            
            #pick a child
            potential_children = current.keys()
            chosen = choice(potential_children)
            current = current[chosen]
            

        #perform the leaf

        
        return output
        
    def perform_node(self,node):
        """
        .node.next.[...],
        .node.preconditions.[]
        .node.statemods...
        .node.performance."blah"
        .node.bindings.[] <- or is this implicit?
        .node.weight!n
        .node.rules...
        """

    
        
    def __call__(self,string):
        """ Parse a string, act accordingly with the results """
        parsed_representations = self.parser(string)
        #todo: return a {status: bool, data: [] } obj
        actResults = []
        for r in parsed_representations:
            expanded = r.expand()
            for x in expanded:
                actResults.append(self.act(x))
            
        if len(actResults) == 0:
            return None
        if len(actResults) == 1:
            return actResults[0]
        else:
            return actResults

    #Binding state operations:
    def add_level(self):
        self.bindings.add_level()

    def replace_stack(self,frame):
        self.bindings[-1] = frame

    def top_stack(self):
        return self.bindings.top()
        
    def pop_stack(self):
        self.bindings.pop()

    #Simulation functions:
    def run(self):
        """ run the simulation """
        None


    #Action functions:
    def act(self,action):
        """ Given an action (one of ELBDs action types),
        perform it
        """
        #Store in the history
        self.history.append(action)
        
        result = None
        #Perform based on parsed type
        if isinstance(action,ELBD.ELFACT):
            #Fact: Assert /retract
            if isinstance(action[-1], ELBD.ELQUERY):
                #Don't replace vars with bindings, populate them
                logging.debug("Querying")
                self.add_level()
                success, frame = self.fact_query(action, self.top_stack())
                result = success
                self.pop_stack()
                logging.debug('Query Result: {}'.format(result))
            elif action.negated:
                logging.debug("Hit a negation, retracting")
                result = self.fact_retract(action)
            else:
                logging.debug("Hit an assertion")
                result = self.fact_assert(action)
        elif isinstance(action,ELBD.ELBIND):
            raise ELE.ELRuntimeException("Not Implemented")
            #self.set_binding(action.var,action.root)
        elif isinstance(action,ELBD.ELARITH_FACT):
            #Get the designated leaf.
            node = self.trie[action.data]
            action.apply(node)
        else:
            raise ELE.ELRuntimeException("Unrecognised Action: {}".format(action))
        return result

    
    def act_on_array(self, actions): #todo
        """ Given a collection of actions, perform each """
        assert False
        if any([not isinstance(x,ELBD.ELAction) for x in actions]):
            raise Exception("An Action is invalid")


    #Fact operations:
    def fact_assert(self,fact):
        """ Add a fact """
        return_val = self.trie.push(fact)
        return return_val
            
    def fact_retract(self,fact):
        """ Remove a fact """
        return_val = self.trie.pop(fact)
        return return_val
            
    def fact_query(self,query, bindingFrame=None):
        """ Test a fact, BE CAREFUL IT MODIFES THE TOP OF THE VAR STACK  """
        logging.debug('Recieved Query: {}'.format(query))
        if bindingFrame is None:
            bindingFrame = self.top_stack()
        assert isinstance(bindingFrame, ELBD.ELBindingFrame)
        assert isinstance(query[-1], ELBD.ELQUERY)
        
        current_frame = bindingFrame
        if len(current_frame) == 0:
            logging.debug("Nothing in the current frame")
            return (ELBD.ELFail(), None)
        #fill in any variables from the current bindings
        bound_queries = [query.bind(slice) for slice in current_frame]
        logging.debug('Bound: {}'.format(bound_queries))
        
        #then query
        results = [self.trie.query(query) for query in bound_queries]
        logging.debug("Trie Query results: {}".format(results))
        
        #then integrate into bindings:
        successes = [success for success in results if bool(success) is True]
        logging.debug("Trie Query Successes: {}".format(successes))
        
        #Flatten the frame
        updated_frame = ELBD.ELBindingFrame([bind_slice for success in successes for bind_slice in success.bindings])

        #a frame is valid if it has at least ELSuccess(none,{}) in it
        if len(updated_frame) > 0:
            #successes[1] has no real meaning, its just a success
            return (successes[0], updated_frame)
        else:
            return (ELBD.ELFail(), current_frame)

    def run_rule(self,rule):
        """ Given a rule, check its conditions then queue its results """
        logging.info("Running Rule: {}".format(rule))
        return_val = ELBD.ELFail()
        try:
            self.add_level()
            current_frame = self.top_stack()
            for condition in rule.conditions:
                is_successful, current_frame = self.fact_query(condition, current_frame)
                if not is_successful:
                    raise ELE.ELRuleException()

            # passing_bindings :: ELBindingFrame
            passing_bindings = current_frame
            
            #get the comparison functions, as a tuple 
            comp_tuple = self.format_comparisons(rule)
            compared_bindings = self.filter_by_comparisons(comp_tuple, passing_bindings)
            
            #if filtered the rule down to nothing
            if len(compared_bindings) == 0:
                raise ELE.ELRuleException()
            
            #select a still viable rule
            #todo: add variability here. utility, curves, distributions,
            #round_robins? state?
            selection = choice(compared_bindings)

            #perform modifications to bindings (regex?)
            
            #todo: make the parser check for unbound variables before adding to runtime?  or should that be covered by the parser?
            for action in rule.actions:

                if action.hasForAllBinding():
                    bound_actions = [action.bind(selection, x) \
                                     for x in compared_bindings]
                    logging.debug("Bound actions: {}".format(bound_actions))
                else:
                    bound_actions = [action.bind(selection)]

                for act in bound_actions:
                    self.act(act)

            return_val = ELBD.ELSuccess()
        except ELE.ELRuleException:
            logging.warning("ELRule Exception occurred")
            return_val = ELBD.ELFail()
        finally:
            #then pop the frame off
            self.pop_stack()
        return return_val

    #Rule Utilities:
    def format_comparisons(self, rule):
        #get the bindings from the rule
        retrieved = [(comp, get_COMP_FUNC(comp.op)) for comp in rule.binding_comparisons]
        return retrieved
    

    def filter_by_comparisons(self, comparison_tuples, potential_bindings):
        assert isinstance(potential_bindings, ELBD.ELBindingFrame)
        compared_bindings = potential_bindings
        for comp, func in comparison_tuples:
            compared_bindings = ELBD.ELBindingFrame([slice for slice in compared_bindings if self.run_function(slice, func, comp)])
        ## compared_bindings :: ELBD.ELBindingFrame
        return compared_bindings
        
    def run_function(self, binding, func, comparison):
        #get values from bindings:
        if comparison.b1.value not in binding or \
           (isinstance(comparison.b2, ELBD.ELVAR) and comparison.b2.value not in binding):
            raise ELE.ELConsistencyException('Comparison being run without the necessary bindings')
        val1 = comparison.b1.get_val(binding)
        if isinstance(comparison.b2, ELBD.ELVAR):
            val2 = comparison.b2.get_val(binding)
        else:
            val2 = comparison.b2
        if comparison.op == ELBD.ELCOMP.NEAR:
            if isinstance(comparison.nearVal, ELBD.ELVAR):
                nearVal = comparison.nearVal.get_val(binding)
            else:
                nearVal = comparison.nearVal

            return func(val1, nearVal, val2)
        else:
            return func(val1, val2)


    #String Operations:
    def format_string(self,format_string):
        """ Given a format_string, use defined variables in the runtime
        to fill it in """
        #todo: Take a string of "this is a $x test", and replace $x with the variable val
        None

    #subtree Operations:
    def subtree_query(self, interface_string):
        """ Verify the trie location fulfills the defined interface """
        None

    def subtree_application(self, subtree_application):
        """ Apply the subtree to the given location """
        None

            
    #history:
    def add_change(self,changes):
        None
    def rewind_change(self,changes):
        None
    
        
    #### METRICS
    def max_depth(self):
        return self.trie.dfs_for_metrics()['maxDepth']

    def num_leaves(self):
        return len(self.trie.dfs_for_metrics()['leaves'])
        
    def num_assertions(self):
        return len([x for x in self.history if isinstance(x, ELBD.ELFACT) and not x.negated])
        
    def num_retractions(self):
        return len([x for x in self.history if isinstance(x, ELBD.ELFACT)  and x.negated])
        
        
    #EXPORTING
    def __str__(self):
        leaves = self.trie.dfs_for_metrics()['leaves']
        strings = [str(x) for x in leaves]
        return "\n".join(strings)

