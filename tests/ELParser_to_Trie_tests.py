"""
Basic testing of running the parser into the trie
"""
import unittest
import IPython
import logging as root_logger
from random import random
from test_context import ELParser
from ELParser import ELParser
from ELParser.ELTrie import ELTrie
from ELParser import ELBaseData as ELBD
from fractions import Fraction

class ELParser_to_Trie_tests(unittest.TestCase):

    def setUp(self):
        self.parser = ELParser.ELPARSE
        self.trie = ELTrie()

    def tearDown(self):
        self.parser = None
        self.trie = None

    def test_simple(self):
        """ check the creation of the parser and trie """
        self.assertIsNotNone(self.trie)
        self.assertIsNotNone(self.parser)
        self.assertIsInstance(self.trie,ELTrie)

    def test_parse(self):
        """ parse a simple string, add it to the trie """
        fact_string = ".this.is.a.test"
        parsed_string = self.parser.parseString(fact_string)[0]
        successOrFail = self.trie.push(parsed_string)
        self.assertTrue(successOrFail)
        retrieved = self.trie.get(self.parser.parseString(".this.is.a")[0])
        self.assertEqual(retrieved,"a")
        self.assertTrue("test" in retrieved)

    def test__n_facts(self):
        """ parse a number of facts and add them all """
        fact_string = ".this.is.a.test\n.this.is.another.test\n.this.is.yet.another.test"
        parsed_strings = self.parser.parseString(fact_string)
        for s in parsed_strings:
            success = self.trie.push(s)
            self.assertTrue(success)
        #now test:
        retrieved = self.trie.get(self.parser.parseString('.this.is')[0])
        self.assertEqual(retrieved,'is')
        self.assertTrue('a' in retrieved)
        self.assertTrue('another' in retrieved)
        self.assertTrue('yet' in retrieved)
        


       
if __name__ == "__main__":
    LOGLEVEL = root_logger.DEBUG
    LOG_FILE_NAME = "ELParser_Trie_tests.log"
    root_logger.basicConfig(filename=LOG_FILE_NAME, level=LOGLEVEL, filemode='w')
    console = root_logger.StreamHandler()
    console.setLevel(root_logger.INFO)
    root_logger.getLogger('').addHandler(console)
    logging = root_logger.getLogger(__name__)
    root_logger.disable(root_logger.CRITICAL)
    ##############################
    
    unittest.main()
