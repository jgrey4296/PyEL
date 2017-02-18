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
        self.parser = ELParser.ROOT
        self.trie = ELTrie.ELTrie()
        self.history = []

    def act(self,action):
        """ Given an action (one of ELBDs action types),
        perform it
        """
        if not isinstance(action,ELBD.ELAction):
            raise Exception("Action is invalid")


    def act_on_array(self, actions):
        """ Given a collection of actions, perform each """
        if any([not isinstance(x,ELBD.ELAction) for x in actions]):
            raise Exception("An Action is invalid")


    def act_add_fact(self,fact):
        """ Add a fact """
        None

    def act_remove_fact(self,fact):
        """ Remove a fact """
        None
        
    def act_test_fact(self,fact):
        """ Test a fact """
        None

    def act_run_rule(self,rule):
        """ Given a rule, check its conditions then queue its results """
        None

    def act_rule_rules(self,rule):
        """ Given a set of rules, run them all """
        None

    def act_set_bindings(self,binding_strings):
        """ Given a binding string, set the runtime variables """
        None

    def act_format_string(self,format_string):
        """ Given a format_string, use defined variables in the runtime
        to fill it in """
        None

    def act_verify_interface(self, interface_string):
        """ Verify the trie location fulfills the defined interface """
        None

    def act_apply_subtree(self, subtree_application):
        """ Apply the subtree to the given location """
        None
    

