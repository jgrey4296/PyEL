"""
	BASIC testing of the ELTrie
"""
import unittest
import IPython
import logging
from random import random
from test_context import ELParser
from ELParser.ELTrie import ELTrie
from ELParser import ELBaseData as ELBD


base_root = ELBD.ELROOT(ELBD.EL.DOT)
root_fact = ELBD.ELFACT([base_root])

class ELParser_Tests(unittest.TestCase):
    
    def setUp(self):
        self.trie = ELTrie()
    def tearDown(self):
        self.trie = None
 
    def test_simple(self):
        """ Check the trie is constructed """
        self.assertIsNotNone(self.trie)
        self.assertTrue(self.trie)
        
    #Test Adding
    def test_adding_1(self):
        base_pair = ELBD.ELPAIR(ELBD.EL.DOT,"test")
        fact_string = ELBD.ELFACT([base_pair for x in range(3)])
        self.trie.add_fact(fact_string)
        

    #Test adding an array

    #Check an array leaf can only be a leaf 
        
    #Test testing
    
    #Test removing

    #Test Exclusions

    #Test getting
        
        
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
