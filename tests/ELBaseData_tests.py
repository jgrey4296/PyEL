"""
	BASIC testing of the ELParser
"""
import unittest
import logging as root_logger
import IPython
from random import random
from test_context import ELParser
from ELParser import ELParser
from ELParser import ELBaseData as ELBD
from ELParser import ELExceptions as ELE
from fractions import Fraction

#Parser returns a ParseResult, which is an array of actual parse data structures

gen_n = lambda: 2 + int(random()*20)

class ELBaseData_Tests(unittest.TestCase):

    def test_Fact_binding(self):
        testFact = ELBD.ELFACT(r=True).var('b').var('c').vterm('d')
        bindingDict = ELBD.ELBindingSlice(
            {'b': ELBD.ELBindingEntry('b',None,'blah'),
             'c': ELBD.ELBindingEntry('c', None, 'crickey'),
             'd': ELBD.ELBindingEntry('d', None, 'dimwit') })
        bound = testFact.bind(bindingDict)
        self.assertEqual(str(testFact), '.$b.$c.$d')
        self.assertEqual(repr(testFact), '| ROOT.VAR(b).VAR(c).VAR(d) || |')
        self.assertNotEqual(repr(testFact), repr(bound))
        self.assertEqual(str(bound), '.blah.crickey.dimwit')
        self.assertEqual(repr(bound), "| ROOT.'blah'.'crickey'.'dimwit' || |")

    def test_fact_string_str(self):
        None

    def test_fact_string_repr(self):
        None
        
    def test_fact_variable_str(self):
        None

    def test_fact_variable_repr(self):
        None

    def test_rule_str(self):
        None

    def test_rule_repr(self):
        None

    
        
    
        
if __name__ == "__main__":
    LOGLEVEL = root_logger.DEBUG
    LOG_FILE_NAME = "ELBaseData_tests.log"
    root_logger.basicConfig(filename=LOG_FILE_NAME, level=LOGLEVEL, filemode='w')
    console = root_logger.StreamHandler()
    console.setLevel(root_logger.INFO)
    root_logger.getLogger('').addHandler(console)
    logging = root_logger.getLogger(__name__)
    #root_logger.disable(root_logger.CRITICAL)
    ##############################

    unittest.main()
