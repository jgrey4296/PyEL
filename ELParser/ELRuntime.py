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
        #Stack of dictionaries of bindings and their values
        self.bindings = [{}]

    def __call__(self,string):
        """ Parse a string, act accordingly with the results """
        parsed_representations = self.parser(string)
        actResults = []
        for r in parsed_representations:
            actResults.append(self.act(r))
        return actResults

            
    def query_b(self,string):
        """ Utility for querying to get a boolean result """
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
            self.push_frame()
            result = self.run_rule(action)
            self.pop_frame()
        elif isinstance(action,ELBD.ELBIND):
            #Binding, update current stack
            self.set_binding(action.var,action.root)
        elif isinstance(action,ELBD.ELARITH_FACT):
            #todo: enact arithmetic on the fact /binding
                        
            None
        elif isinstance(action,ELBD.ELQUERY):
            #Don't replace vars with bindings, populate them
            logging.info("Querying")
            result = self.fact_query(action)
            logging.info('Query Result: {}'.format(result))

        return result

    def act_on_array(self, actions): #todo
        """ Given a collection of actions, perform each """
        if any([not isinstance(x,ELBD.ELAction) for x in actions]):
            raise Exception("An Action is invalid")


    def fact_assert(self,fact):
        """ Add a fact """
        #todo: fill out bindings
        #bindings are ELVAR -> ELPAIR in f(fact)->fact
        
        self.trie.push(fact)
        if isinstance(fact[-1].value, ELBD.ELRULE):
            self.add_rule(fact.short_str(), fact[-1].value)

    def fact_retract(self,fact):
        """ Remove a fact """
        #todo: fill out bindings
        self.trie.pop(fact)
        if isinstance(fact[-1].value, ELBD.ELRULE):
            self.remove_rule(fact.short_str())
        
    def fact_query(self,fact):
        """ Test a fact,  """
        if not isinstance(fact,ELBD.ELQUERY):
            raise ELE.ELConsistencyException('Querying requires the use of a query')
        #todo: split into sections [root - var_n, var_n+1 - var_n',var_'+1..]
        
        
        #For each section, test then aggregate

        #test first section, get results
        #make new fact strings, replacing VAR with ELPAIRs
        #combine with next section, repeat

        #then return only the total passing tree of bindings
        return self.trie.query(fact)

    def run_rule(self,rule):
        """ Given a rule, check its conditions then queue its results """
        truthiness = False
        condition_truths_and_bindings = [self.fact_query(x) for x in rule.conditions]
        #filter for consistency between conditions
        
        #add retrieved values from conditions as bindings

        #perform comparisons

        
        if truthiness:
            for action in rule.actions:
                #binding occurs as part of assertion/retraction,
                #BUT make sure the right frame is on
                self.act(action)
                #then pop the frame off

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
            
    #Bindings
    def push_frame(self,frame={}):
        self.bindings.append(frame)

    def pop_frame(self):
        if len(self.bindings) > 1:
            self.bindings.pop()

    def set_binding(self,var,val):
        """ Stores the fact string location of a value
        Bindings are essentially pointers into the trie
        """
        if not isinstance(val, ELBD.ELFACT):
            raise Exception('Bindings are the path to the value')
        self.bindings[-1][var.value] = val

    def get_binding(self,var):
        #from top to bottom, find the first var that fits
        local_copy = self.bindings.copy()
        local_copy.reverse()
        returnVal = None
        for frame in local_copy:
            if var.value in frame:
                returnVal = frame[var.value]
                break
        return returnVal

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
