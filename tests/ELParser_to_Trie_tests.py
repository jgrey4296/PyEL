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
        parsed_string = self.parser(fact_string)[0]
        successOrFail = self.trie.push(parsed_string)
        self.assertTrue(successOrFail)
        retrieved = self.trie.get(self.parser(".this.is.a")[0])
        self.assertEqual(retrieved,"a")
        self.assertTrue("test" in retrieved)

    def test__n_facts(self):
        """ parse a number of facts and add them all """
        fact_string = ".this.is.a.test\n.this.is.another.test\n.this.is.yet.another.test"
        parsed_strings = self.parser(fact_string)
        for s in parsed_strings:
            success = self.trie.push(s)
            self.assertTrue(success)
        #now test:
        retrieved = self.trie.get(self.parser('.this.is')[0])
        self.assertEqual(retrieved,'is')
        self.assertTrue('a' in retrieved)
        self.assertTrue('another' in retrieved)
        self.assertTrue('yet' in retrieved)

    def test_empty_array(self):
        fact_string = ".this.is.an.empty.array.[]"
        #add
        result = self.trie.push(self.parser(fact_string)[0])
        self.assertTrue(result)
        retrieved = self.trie.get(self.parser('.this.is.an.empty.array')[0])
        self.assertEqual(retrieved,'array')
        
    def test_non_empty_array(self):
        fact_string = ".this.is.an.array.[1,2,3,4]"
        result = self.trie.push(self.parser(fact_string)[0])
        self.assertTrue(result)
        retrieved = self.trie.get(self.parser('.this.is.an.array')[0])
        self.assertEqual(retrieved,'array')
        self.assertEqual(retrieved[0],[1,2,3,4])

    def test_fraction_array(self):
        fact_string = ".this.is.an.array.[1/2,3/4,5/6]"
        result = self.trie.push(self.parser(fact_string)[0])
        retrieved = self.trie.get(self.parser('.this.is.an.array')[0])
        compareTo = [Fraction(1,2),Fraction(3,4),Fraction(5,6)]
        self.assertEqual(retrieved[0],compareTo)

    def test_fact_with_string(self):
        fact_string = """.this.is."a longer test".blah"""
        result = self.trie.push(self.parser(fact_string)[0])
        self.assertTrue(result)
        retrieved = self.trie.get(self.parser('.this.is')[0])
        self.assertEqual(retrieved,'is')
        self.assertIn('a longer test',retrieved)
        retrieved2 = self.trie.get(self.parser('.this.is."a longer test"')[0])
        self.assertEqual(retrieved2,'a longer test')
        self.assertIn('blah',retrieved2)

    def test_fact_sequence(self):
        """ Check an array of facts is parsed and integrated appropriately """
        fact_string = ".this.is.a.test.[.a.b.c, .d.e.f]"
        retrieval_string = ".this.is.a.test"
        parsed = self.parser(fact_string)
        added = self.trie.push(parsed[0])
        retrieved = self.trie.get(self.parser(retrieval_string)[0])
        self.assertEqual(len(retrieved[0]),2)
        self.assertIsInstance(retrieved[0][0],ELBD.ELFACT)
        self.assertIsInstance(retrieved[0][1],ELBD.ELFACT)

    def test_fact_sequence_re_add(self):
        """ Check that a fact stored in an array is valid to be re-added """
        fact_string = ".this.is.a.test.[.a.b.c, .d.e.f]"
        retrieval_string = ".this.is.a.test"
        second_retrieval = ".a.b"
        parsed = self.parser(fact_string)
        added = self.trie.push(parsed[0])
        retrieved = self.trie.get(self.parser(retrieval_string)[0])
        first_fact = retrieved[0][0]
        re_added = self.trie.push(first_fact)
        second_retrieved = self.trie.get(self.parser(second_retrieval)[0])
        self.assertEqual(second_retrieved,'b')
        self.assertIn('c',second_retrieved)

    def test_modifying_retrieved_data_doesnt_change_trie(self):
        """ Trie data should be safe from accidental modification """
        fact_string = ".this.is.a.test"
        retrieval_string = ".this.is.a"
        self.trie.push(self.parser(fact_string)[0])
        retrieved = self.trie.get(self.parser(retrieval_string)[0])
        self.assertIn('test',retrieved)
        retrieved.children[0] = 'blah'
        self.assertNotIn('test',retrieved)
        retrieved_2 = self.trie.get(self.parser(retrieval_string)[0])
        self.assertIn('test',retrieved_2)
        
    def test_exclusion_semantics_1(self):
        """ Testing non-exclusive additions """
        test_fact = ".this.is.a.fact\n.this.is.a.second"
        retrieval_string = ".this.is.a"
        parsed = self.parser(test_fact)
        for f in parsed:
            self.trie.push(f)
        retrieved = self.trie.get(self.parser(retrieval_string)[0])
        self.assertIn('fact',retrieved)
        self.assertIn('second',retrieved)

    def test_exclusion_semantics_2(self):
        """ Test exclusion upcasting """
        base_facts = ".this.is.a.fact\n.this.is.a.second"
        retrieval_string = ".this.is.a"
        for f in self.parser(base_facts):
            self.trie.push(f)
        exclusion_fact = ".this.is.a!exclusive"
        self.trie.push(self.parser(exclusion_fact)[0])
        retrieved = self.trie.get(self.parser(retrieval_string)[0])
        self.assertEqual('a',retrieved)
        self.assertIn('exclusive',retrieved)
        self.assertNotIn('fact',retrieved)
        self.assertNotIn('second',retrieved)

    def test_exclusion_semantics_3(self):
        """ Test exclusion re-definition """
        base_fact = ".this.is.an!exclusion"
        update_string = ".this.is.an!other"
        retrieval_string = ".this.is.an"
        self.trie.push(self.parser(base_fact)[0])
        retrieved = self.trie.get(self.parser(retrieval_string)[0])
        self.assertIn('exclusion',retrieved)
        self.trie.push(self.parser(update_string)[0])
        updated = self.trie.get(self.parser(retrieval_string)[0])
        self.assertIn('other',updated)
        self.assertNotIn('exclusion',updated)

    def test_exclsuion_semantics_3(self):
        """ test exlcusion down-casting """
        base_fact = ".this.is.an!exclusion"
        update_string = ".this.is.an.other\n.this.is.an.else"
        retrieval_string = ".this.is.an"
        self.trie.push(self.parser(base_fact)[0])
        retrieved_1 = self.trie.get(self.parser(retrieval_string)[0])
        self.assertIn('exclusion',retrieved_1)
        for f in self.parser(update_string):
            self.trie.push(f)
        retrieved_2 = self.trie.get(self.parser(retrieval_string)[0])
        self.assertIn('other',retrieved_2)
        self.assertIn('else',retrieved_2)
        self.assertNotIn('exclusion',retrieved_2)

    def test_number_usage_post_retrieval(self):
        """ make sure numbers can be used when retrieved from the trie """
        base_facts = ".this.is.a.test.5\n.this.is.some.other!10"
        retrieval_string_1 = ".this.is.a.test"
        retrieval_string_2 = ".this.is.some.other"
        for f in self.parser(base_facts):
            self.trie.push(f)
        retrieved_1 = self.trie.get(self.parser(retrieval_string_1)[0])
        retrieved_2 = self.trie.get(self.parser(retrieval_string_2)[0])
        added = retrieved_1[0] + retrieved_2[0]
        self.assertEqual(added,15)
        subbed = retrieved_2[0] - retrieved_1[0]
        self.assertEqual(subbed,5)
                                    
    def test_empty_rule(self):
        """ Check rules are stored in the trie appropriately """
        base_fact = ".this.is.a.rule.{ [] -> [] }"
        retrieval_string = ".this.is.a.rule"
        isAdded = self.trie.push(self.parser(base_fact)[0])
        self.assertTrue(isAdded)
        retrieved = self.trie.get(self.parser(retrieval_string)[0])
        self.assertEqual(retrieved[0],self.parser(base_fact)[0][-1].value)

    def test_simple_rule(self):
        """ Check that a simple rule is stored appropriately """
        base_fact = ".this.is.a.rule.{ .a.b.c -> .a.b.d }"
        retrieval_string = ".this.is.a.rule"
        isAdded = self.trie.push(self.parser(base_fact)[0])
        self.assertTrue(isAdded)
        retrieved = self.trie.get(self.parser(retrieval_string)[0])
        self.assertEqual(retrieved[0],self.parser(base_fact)[0][-1].value)

    
    ##rule with bindings
    ##rule with comparisons
    ##rule with actions
    ##unbalanced bindings
    ##negatable facts
        
    ##rule with arith actions
    ##rule with var arith actions
    ##rule with near operator


    #BIND statements not applicable
       
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
