"""
	BASIC testing of the ELParser
"""
import unittest
import logging
from random import random
from test_context import ELParser
from ELParser import ELParser
from ELParser import ELBaseData as ELBD
from fractions import Fraction

#Parser returns a ParseResult, which is an array of actual parse data structures

gen_n = lambda: 1 + int(random()*20)

class ELParser_Tests(unittest.TestCase):

    def setUp(self):
        self.parser = ELParser.ROOT
    def tearDown(self):
        self.parser = None
 
    def test_simple(self):
        """ Check the parser works in a minimal case """
        result = self.parser.parseString('.this.is.a.test')[0]
        self.assertIsInstance(result,ELBD.ELFACT)

    def test_n_facts(self):
        """ check that n facts are parsed together """
        n_facts = gen_n()
        fact_string = ".this.is.a.test"
        all_facts = "\n".join([fact_string for x in range(n_facts)])
        results = self.parser.parseString(all_facts)
        self.assertEqual(len(results),n_facts)

    def test_results_are_ELFACTS(self):
        """ check that the returned type is a ELBD.ELFACT """
        fact_string = ".this.is.a.test\n.this.is.another.test"
        results = self.parser.parseString(fact_string)
        self.assertIsInstance(results[0],ELBD.ELFACT)
        self.assertIsInstance(results[1],ELBD.ELFACT)

    def test_results_contain_data(self):
        """ check that a parsed result contains the correct amount of data in its data field """
        fact_length = gen_n()
        test_fact = ".test".join(["" for x in range(fact_length)])
        results = self.parser.parseString(test_fact)
        #-1 because you're comparing to the *connections* not the actual elements in the empty array
        self.assertEqual(len(results[0].data),fact_length)

    def test_results_contain_array(self):
        """ check that the parsed result correctly gets an array in a fact """
        test_fact = ".this.is.an.array.[1,2,3,4,5]"
        results = self.parser.parseString(test_fact)
        self.assertEqual(len(results[0].data),6)
        self.assertIsInstance(results[0].data[-1],ELBD.ELTERM)
        self.assertEqual(results[0].data[-1].value,[1,2,3,4,5])

    def test_empty_array(self):
        """ check that an array can be empty """
        test_fact = ".this.is.an.empty.array.[]"
        results = self.parser.parseString(test_fact)
        #length is 7, num of '.' + terminal
        self.assertEqual(len(results[0].data),7)
        self.assertIsInstance(results[0].data[-1],ELBD.ELTERM)
        self.assertEqual(len(results[0].data[-1].value),0)
        
    def test_multi_line_array(self):
        """ check that an array can be on multiple lines """
        test_fact = """.this.is.a.multiline.array.[
        1,
        2,
        3
        ]"""
        results = self.parser.parseString(test_fact)
        self.assertEqual(len(results[0].data),7)
        self.assertIsInstance(results[0].data[-1],ELBD.ELTERM)
        #Checking LENGTH:
        self.assertEqual(len(results[0].data[-1].value),3)
        #Checking CONTENT:
        self.assertEqual(results[0].data[-1].value,[1,2,3])

    def test_fact_with_string_inside(self):
        """ check facts can have strings inside them """
        test_fact = '.this.is.a."string fact"'
        results = self.parser.parseString(test_fact)
        self.assertEqual(results[0].data[-1].value,'"string fact"')

    def test_fact_with_string_sub_values(self):
        """ check that a string fact can continue having sub values """
        test_fact = '.this.is."a test".with.subvalues'
        results = self.parser.parseString(test_fact)
        self.assertEqual(len(results[0].data),6)

    def test_fact_with_exclusion_operator(self):
        """ Check the ! exclusion operator works in facts """
        test_fact = ".this.is.an!exclusive.fact"
        results = self.parser.parseString(test_fact)
        self.assertEqual(len(results[0].data),6)
        self.assertEqual(results[0].data[3].elop,ELBD.EL.EX)

    def test_fact_with_string_including_ex_op(self):
        """ check that an ! in a string doesn't interfere """
        test_fact = '.this.is."a !test"'
        results = self.parser.parseString(test_fact)
        self.assertEqual(len(results[0].data),4)
        self.assertEqual(results[0].data[-1].value,'"a !test"')

    def test_fact_with_number(self):
        """ check that facts can include numbers """
        test_fact = '.a.b.5'
        results = self.parser.parseString(test_fact)
        self.assertEqual(results[0].data[-1].value,5)

    def test_fact_with_negative_number(self):
        """ check that numbers in facts can be negative """
        test_fact = '.a.b.-5'
        results = self.parser.parseString(test_fact)
        self.assertEqual(results[0].data[-1].value,-5)

    def test_fact_with_underscore_number(self):
        """ check that numbers can be formatted to be read """
        test_fact = '.a.b.5_000_000'
        results = self.parser.parseString(test_fact)
        self.assertEqual(results[0].data[-1].value,5000000)

    def test_fact_with_number_array(self):
        """ check that numbers can be in arrays """
        test_fact ='.a.b.[1,2,3]'
        results = self.parser.parseString(test_fact)
        self.assertEqual(results[0].data[-1].value,[1,2,3])

    def test_fact_with_underscore_negative_number(self):
        """ check that formatted numbers can be negative """
        test_fact = ".a.b.-12_000_000"
        results = self.parser.parseString(test_fact)
        self.assertEqual(results[0].data[-1].value,-12000000)

    def test_facts_can_be_fractions(self):
        """ check that numbers in facts can be fractions """
        test_fact = ".a.b.1/5"
        results = self.parser.parseString(test_fact)
        self.assertIsInstance(results[0].data[-1].value,Fraction)

    def test_facts_can_be_decimals(self):
        """ check that numbers can be decimals """
        test_fact = ".a.b.1d5"
        results = self.parser.parseString(test_fact)
        self.assertEqual(results[0].data[-1].value,1.5)

    def test_numbers_can_have_sub_facts(self):
        """ make sure numbers dont have to be leaves """
        test_fact = ".a.b.5.c"
        results = self.parser.parseString(test_fact)
        self.assertEqual(len(results[0].data),5)
        self.assertEqual(results[0].data[-1].value,'c')

    def test_comments_are_ignored(self):
        """ make sure comments are ignored """
        test_fact = ".a.b.c\n#blahhhhh\n.c.d.e"
        results = self.parser.parseString(test_fact)
        self.assertEqual(len(results),2)

    
        
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
