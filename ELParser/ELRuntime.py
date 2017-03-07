"""
	A Trie based runtime for EL
"""
import logging as root_logger
logging = root_logger.getLogger(__name__)


from enum import Enum
from collections import namedtuple
from fractions import Fraction
import IPython
import ELParser
from ELParser import ELParser, ELTrie
from ELParser import ELBaseData as ELBD


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
        #Stack of dictionaries of bindings and their values
        self.bindings = []

    def __call__(self,string):
        """ Parse a string, act accordingly with the results """
        parsed_representations = self.parser(string)
        actResults = []
        for r in parsed_representations:
            actResults.append(self.act(r))
        return actResults

            
    def query(self,string):
        parsed = self.parser(string)
        results = [self.fact_query(x) for x in parsed]
        return all(results)

            
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
            #Rule... enact?
            None
        elif isinstance(action,ELBD.ELBIND):
            #Binding, update current stack
            None
        elif isinstance(action,ELBD.ELARITH_FACT):
            #enact arithmetic on the fact /binding
            None
        elif isinstance(action,ELBD.ELQUERY):
            #Query
            logging.debug("Querying")
            result = self.fact_query(action)

        return result

    def act_on_array(self, actions):
        """ Given a collection of actions, perform each """
        if any([not isinstance(x,ELBD.ELAction) for x in actions]):
            raise Exception("An Action is invalid")


    def fact_assert(self,fact):
        """ Add a fact """
        self.trie.push(fact)

    def fact_retract(self,fact):
        """ Remove a fact """
        self.trie.pop(fact)
        
    def fact_query(self,fact):
        """ Test a fact """
        return self.trie.query(fact)

    def run_rule(self,rule):
        """ Given a rule, check its conditions then queue its results """
        None

    def set_binding(self,binding):
        """ Given a binding string, set the runtime variables """
        None
        
    def format_string(self,format_string):
        """ Given a format_string, use defined variables in the runtime
        to fill it in """
        None

    def subtree_query(self, interface_string):
        """ Verify the trie location fulfills the defined interface """
        None

    def subtree_application(self, subtree_application):
        """ Apply the subtree to the given location """
        None

    #Rule store:
    def add_rule(self,rule):
        None

    def remove_rule(self,rule):
        None

    #Bindings
    def push_frame(self):
        None

    def pop_frame(self):
        None

    def set_binding(self,var,val):
        None

    def get_binding(self,var,val):
        None

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
        None
