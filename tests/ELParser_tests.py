import unittest
import logging
from random import random
from test_context import ELParser
from ELParser.ELParser import t_ELFACT, t_ELPAIR, t_ELARRAY

#Parser returns a ParseResult, which is an array of actual parse data structures

gen_n = lambda: int(random()*20)

class ELParser_Tests(unittest.TestCase):

    def setUp(self):
        self.parser = ELParser.ROOT
    def tearDown(self):
        self.parser = None
 
    def test_simple(self):
        """ Check the parser works in a minimal case """
        result = self.parser.parseString('.this.is.a.test')[0]
        self.assertIsInstance(result,t_ELFACT)

    def test_n_facts(self):
        """ check that n facts are parsed together """
        n_facts = gen_n()
        fact_string = ".this.is.a.test"
        all_facts = "\n".join([fact_string for x in range(n_facts)])
        results = self.parser.parseString(all_facts)
        self.assertEqual(len(results),n_facts)

    def test_results_are_ELFACTS(self):
        """ check that the returned type is a t_ELFACT """
        fact_string = ".this.is.a.test\n.this.is.another.test"
        results = self.parser.parseString(fact_string)
        self.assertIsInstance(results[0],t_ELFACT)
        self.assertIsInstance(results[1],t_ELFACT)

    def test_results_contain_data(self):
        """ check that a parsed result contains the correct amount of data in its data field """
        fact_length = gen_n()
        test_fact = ".test".join(["" for x in range(fact_length)])
        results = self.parser.parseString(test_fact)
        #-1 because you're comparing to the *connections* not the actual elements in the empty array
        self.assertEqual(len(results[0].data),fact_length-1)

    def test_results_array_is_none_when_no_array(self):
        """ check the t_ELFact.array entry is none when appropriate """
        test_fact = ".this.is.a.test"
        results = self.parser.parseString(test_fact)
        self.assertIsNone(results[0].array)
        
    def test_results_contain_array(self):
        """ check that the parsed result correctly gets an array in a fact """
        test_fact = ".this.is.an.array.[1,2,3,4,5]"
        results = self.parser.parseString(test_fact)
        self.assertIsNotNone(results[0].array)
        self.assertEqual(results[0].array.array,[1,2,3,4,5])

    def test_empty_array(self):
        """ check that an array can be empty """
        test_fact = ".this.is.an.empty.array.[]"
        results = self.parser.parseString(test_fact)
        self.assertIsNotNone(results[0].array)
        self.assertEqual(len(results[0].array.array),0)
        
    def test_multi_line_array(self):
        """ check that an array can be on multiple lines """
        test_fact = """.this.is.a.multiline.array.[
        1,
        2,
        3
        ]"""
        results = self.parser.parseString(test_fact)
        self.assertIsNotNone(results[0].array)
        self.assertEqual(len(results[0].array.array),3)
        
        
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
