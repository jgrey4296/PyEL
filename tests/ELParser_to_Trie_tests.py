"""
Basic testing of running the parser into the trie
"""
import unittest
import IPython
import logging as root_logger
from random import random
from test_context import ielpy
from ielpy import ELParser
from ielpy.ELTrie import ELTrie
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
        self.assertTrue(self.trie.query(self.parser('.this.is.a.test?')[0]))

    def test__n_facts(self):
        """ parse a number of facts and add them all """
        fact_string = ".this.is.a.test\n.this.is.another.test\n.this.is.yet.another.test"
        parsed_strings = self.parser(fact_string)
        for s in parsed_strings:
            success = self.trie.push(s)
            self.assertTrue(success)
        #now test:
        self.assertTrue(self.trie.query(self.parser('.this.is.a.test?')[0]))
        self.assertTrue(self.trie.query(self.parser('.this.is.another.test?')[0]))
        self.assertTrue(self.trie.query(self.parser('.this.is.yet.another.test?')[0]))


    def test_empty_array(self):
        fact_string = ".this.is.an.empty.array.[]"
        #add
        facts = self.parser(fact_string)[0].expand()
        for x in facts:
            result = self.trie.push(x)
            self.assertTrue(result)
        self.assertTrue(self.trie.query(self.parser('.this.is.an.empty.array?')[0]))
        
    def test_non_empty_array(self):
        fact_string = ".this.is.an.array.[1,2,3,4]"
        expanded = self.parser(fact_string)[0].expand()
        for x in expanded:
            self.trie.push(x)
        
        self.assertTrue(self.trie.query(self.parser('.this.is.an.array.1?')[0]))
        self.assertTrue(self.trie.query(self.parser('.this.is.an.array.2?')[0]))
        self.assertTrue(self.trie.query(self.parser('.this.is.an.array.3?')[0]))
        self.assertTrue(self.trie.query(self.parser('.this.is.an.array.4?')[0]))
        self.assertFalse(self.trie.query(self.parser('.this.is.an.array.5?')[0]))


    def test_fraction_array(self):
        fact_string = ".this.is.an.array.[1/2,3/4,5/6]"
        expanded = self.parser(fact_string)[0].expand()
        for x in expanded:
            self.trie.push(x)
            
        self.assertTrue(self.trie.query(self.parser('.this.is.an.array.1/2?')[0]))
        self.assertTrue(self.trie.query(self.parser('.this.is.an.array.3/4?')[0]))
        self.assertTrue(self.trie.query(self.parser('.this.is.an.array.5/6?')[0]))


    def test_fact_with_string(self):
        fact_string = """.this.is."a longer test".blah"""
        result = self.trie.push(self.parser(fact_string)[0])
        self.assertTrue(result)
        self.assertTrue(self.trie.query(self.parser('.this.is."a longer test".blah?')[0]))

    def test_fact_sequence(self):
        """ Check an array of facts is parsed and integrated appropriately """
        fact_string = ".this.is.a.test.[.a.b.c, .d.e.f]"
        parsed = self.parser(fact_string)
        expanded = parsed[0].expand()
        for x in expanded:
            self.trie.push(x)
            as_query = x.query()
            self.assertTrue(self.trie.query(as_query))


    def test_fact_sequence_re_add(self):
        """ Check that a fact stored in an array is valid to be re-added """
        fact_string = self.parser(".this.is.a.test.[.a.b.c, .d.e.f]")[0]
        expanded = fact_string.expand()
        for x in expanded:
            self.trie.push(x)

        f1 = self.parser(".this.is.a.test?")[0]
        self.assertTrue(self.trie.query(f1))
        f2 = self.parser(".this.is.a.test.a.b.c?")[0]
        self.assertTrue(self.trie.query(f2))
        f3 = self.parser(".this.is.a.test.d.e.f?")[0]
        self.assertTrue(self.trie.query(f3))


        

        
    def test_modifying_retrieved_data_doesnt_change_trie(self):
        """ Trie data should be safe from accidental modification """
        #TODO
        None
                
    def test_exclusion_semantics_1(self):
        """ Testing non-exclusive additions """
        test_fact = ".this.is.a.fact\n.this.is.a.second"
        retrieval_string = ".this.is.a"
        parsed = self.parser(test_fact)
        for f in parsed:
            self.trie.push(f)
        self.assertTrue(self.trie.query(self.parser('.this.is.a.fact?')[0]))
        self.assertTrue(self.trie.query(self.parser('.this.is.a.second?')[0]))
        
    def test_exclusion_semantics_2(self):
        """ Test exclusion upcasting """
        base_facts = ".this.is.a.fact\n.this.is.a.second"
        retrieval_string = ".this.is.a"
        for f in self.parser(base_facts):
            self.trie.push(f)
        self.assertTrue(self.trie.query(self.parser('.this.is.a.fact?')[0]))
        self.assertTrue(self.trie.query(self.parser('.this.is.a.second?')[0]))
        exclusion_fact = ".this.is.a!exclusive"
        self.trie.push(self.parser(exclusion_fact)[0])
        self.assertFalse(self.trie.query(self.parser('.this.is.a.fact?')[0]))
        self.assertFalse(self.trie.query(self.parser('.this.is.a.second?')[0]))
        self.assertTrue(self.trie.query(self.parser('.this.is.a!exclusive?')[0]))
        
    def test_exclusion_semantics_3(self):
        """ Test exclusion re-definition """
        base_fact = ".this.is.an!exclusion"
        update_string = ".this.is.an!other"
        retrieval_string = ".this.is.an"
        self.trie.push(self.parser(base_fact)[0])
        self.assertTrue(self.trie.query(self.parser('.this.is.an!exclusion?')[0]))
        self.trie.push(self.parser(update_string)[0])
        self.assertFalse(self.trie.query(self.parser('.this.is.an!exclusion?')[0]))
        self.assertTrue(self.trie.query(self.parser('.this.is.an!other?')[0]))

    def test_exclsuion_semantics_3(self):
        """ test exclusion down-casting """
        root_logger.disable(root_logger.DEBUG)
        base_fact = ".this.is.an!exclusion"
        update_string = ".this.is.an.other\n.this.is.an.else"
        self.trie.push(self.parser(base_fact)[0])
        self.assertTrue(self.trie.query(self.parser('.this.is.an!exclusion?')[0]))
        for f in self.parser(update_string):
            self.trie.push(f)
        self.assertFalse(self.trie.query(self.parser('.this.is.an!exclusion?')[0]))
        self.assertTrue(self.trie.query(self.parser('.this.is.an.other?')[0]))
        self.assertTrue(self.trie.query(self.parser('.this.is.an.else?')[0]))

    def test_number_usage_post_retrieval(self):
        """ make sure numbers can be used when retrieved from the trie """
        base_facts = ".this.is.a.test.5\n.this.is.some.other!10"
        retrieval_string_1 = ".this.is.a.test.$x"
        retrieval_string_2 = ".this.is.some.other!$y"
        for f in self.parser(base_facts):
            self.trie.push(f)
        retrieved_1 = self.trie.get(self.parser(retrieval_string_1)[0])
        retrieved_2 = self.trie.get(self.parser(retrieval_string_2)[0])
        val1 = retrieved_1.bindings[0]['x'].value
        val2 = retrieved_2.bindings[0]['y'].value
        added = val1 + val2
        self.assertEqual(added,15)
        subbed = val2 - val1
        self.assertEqual(subbed,5)
                                 

if __name__ == "__main__":
    LOGLEVEL = root_logger.DEBUG
    LOG_FILE_NAME = "test_ELParser_Trie.log"
    root_logger.basicConfig(filename=LOG_FILE_NAME, level=LOGLEVEL, filemode='w')
    console = root_logger.StreamHandler()
    console.setLevel(root_logger.WARNING)
    root_logger.getLogger('').addHandler(console)
    logging = root_logger.getLogger(__name__)
    root_logger.disable(root_logger.CRITICAL)
    ##############################
    
    unittest.main()
