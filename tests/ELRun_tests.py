"""
	BASIC testing of the ELParser
"""
import unittest
import logging as root_logger
import IPython
from random import random
from test_context import ielpy
from ielpy import ELPARSE
from ielpy import ELBaseData as ELBD
from ielpy import ELExceptions as ELE
from ielpy import ELRuntime as ELR
from fractions import Fraction

#Parser returns a ParseResult, which is an array of actual parse data structures

gen_n = lambda: 1 + int(random()*20)

class ELRun_Tests(unittest.TestCase):

    def setUp(self):
        self.runtime = ELR()

    def tearDown(self):
        self.runtime = None

    #TODO: probability, utility, conditions, printing
    def test_trie_run(self):
        """
        Run from root to a leaf
        """
        self.runtime("""
        .first, 
        .first.conditions.[],
        .first.statemods.[],
        .first.performance!"This is a test",
        .first.weight!1
        .first.rules.[]

        """)
        output = self.runtime.trie_run('.')
        self.assertEqual(output,
                         #deterministic output
                         )
        
    #Additional Tests:
    #Non-deterministic path
    #variable binding / string interpolation
    #Weights, 
        
    def test_tree_run(self):
        """
        Run from root with abl-like motions
        """
        None

    #Sequences, parallelism,
    #Fallbacks
    #Slip-Stack?
        
    def test_fsm_run(self):
        """
        Run to arbitrary states using events
        """
        None

    #events, states, cycles, state

        
    def test_selection_run(self):
        """
        Run an action filtered by conditions

        """
        None

    def test_institution_run(self):
        """
        Test institutions that use all the above
        Monad-Transformer?
        """
        None
        


    


if __name__ == "__main__":
    LOGLEVEL = root_logger.DEBUG
    LOG_FILE_NAME = "ELRuntime_tests.log"
    root_logger.basicConfig(filename=LOG_FILE_NAME, level=LOGLEVEL, filemode='w')
    console = root_logger.StreamHandler()
    console.setLevel(root_logger.WARNING)
    root_logger.getLogger('').addHandler(console)
    logging = root_logger.getLogger(__name__)
    #root_logger.disable(root_logger.INFO)
    ##############################
    unittest.main()
