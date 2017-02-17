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
        self.assertIsInstance(self.trie,ELTrie)

    def test_is_empty(self):
        """ Check the trie is empty upon init """
        self.assertTrue(self.trie.is_empty())

    def test_empty_invalidation_upon_add(self):
        """ Check the trie is no longer empty upong adding something """
        self.assertTrue(self.trie.is_empty())
        #Create the fact: .test
        base_term = ELBD.ELTERM("test")
        base_fact = ELBD.ELFACT([base_root,base_term])
        result = self.trie.push(base_fact)
        self.assertIsInstance(result, ELBD.ELSuccess)
        self.assertFalse(self.trie.is_empty())

    def test_adding_empty_fact(self):
        """ Check that just adding '.' does not change empty state """
        self.assertTrue(self.trie.is_empty())
        result = self.trie.push(ELBD.ELFACT([ELBD.ELROOT(ELBD.EL.DOT)]))
        self.assertIsInstance(result,ELBD.ELSuccess)
        self.assertTrue(self.trie.is_empty())
        
    def test_getting(self):
        """ Get a value from the trie """
        base_term = ELBD.ELTERM("test")
        #base_fact ~= ".test"
        base_fact = ELBD.ELFACT([base_root,base_term])
        add_response = self.trie.push(base_fact)
        result = self.trie.get(ELBD.ELFACT([base_root]))
        self.assertIsInstance(add_response, ELBD.ELSuccess)
        self.assertIsInstance(result,ELBD.ELGet)
        self.assertEqual(result.value,"ROOT")
        #One child, test.
        self.assertEqual(result.children,["test"])

    def test_multi_add(self):
        """ check adding multiple facts works in simplest case """
        base_term1 = ELBD.ELTERM("test")
        base_term2 = ELBD.ELTERM("blah")
        base_fact1 = ELBD.ELFACT([base_root,base_term1])
        base_fact2 = ELBD.ELFACT([base_root,base_term2])
        #now add:
        add_result1 = self.trie.push(base_fact1)
        add_result2 = self.trie.push(base_fact2)
        #verify success:
        self.assertIsInstance(add_result1,ELBD.ELSuccess)
        self.assertIsInstance(add_result2,ELBD.ELSuccess)
        #Now get the root and see the children are there:
        root = self.trie.get(root_fact)
        self.assertIsInstance(root,ELBD.ELGet)
        self.assertEqual(root.value,"ROOT")
        self.assertTrue("test" in root.children)
        self.assertTrue("blah" in root.children)

    def test_fact_len(self):
        """ Check adding a fact of depth 2 works """
        base_fact = ELBD.ELFACT()
        self.assertEqual(len(base_fact),0)
        base_fact.push(ELBD.ELROOT())
        self.assertEqual(len(base_fact),0)
        base_fact.push(ELBD.ELPAIR("test"))
        self.assertEqual(len(base_fact),1)
        base_fact.push(ELBD.ELPAIR("bloo"))
        self.assertEqual(len(base_fact),2)

    def test_fact_completion(self):
        """ Check that an ELFACT recognises when its finished """
        base_fact = ELBD.ELFACT()
        self.assertFalse(base_fact.complete())
        base_fact.push(ELBD.ELROOT())
        self.assertFalse(base_fact.complete())
        base_fact.push(ELBD.ELPAIR("blah"))
        self.assertFalse(base_fact.complete())
        base_fact.push(ELBD.ELTERM("bloo"))
        self.assertTrue(base_fact.complete())

    def test_fact_addition_of_depth_2_invalidates_empty(self):
        """ Check that facts of greater depths can be added """
        base_fact = ELBD.ELFACT(r=True).push(ELBD.ELPAIR("test")).push(ELBD.ELTERM("bloo"))
        self.assertEqual(len(base_fact),2)
        self.assertTrue(self.trie.is_empty())
        result = self.trie.push(base_fact)
        self.assertIsInstance(result,ELBD.ELSuccess)
        self.assertFalse(self.trie.is_empty())

    def test_fact_addition_of_depth_2_actually_adds(self):
        """ check that the data added to the trie of a depth 2 fact is actually added """
        base_fact = ELBD.ELFACT(r=True).push(ELBD.ELPAIR("test")).push(ELBD.ELTERM("bloo"))
        self.assertEqual(len(base_fact),2)
        self.assertTrue(self.trie.is_empty())
        successOrFail = self.trie.push(base_fact)
        self.assertIsInstance(successOrFail,ELBD.ELSuccess)
        result = self.trie.get(ELBD.ELFACT(r=True))
        self.assertEqual(result.value,"ROOT")
        self.assertTrue("test" in result)
        self.assertFalse("bloo" in result)
        result_depth1 = self.trie.get(ELBD.ELFACT(r=True).push(ELBD.ELTERM("test")))
        self.assertNotEqual(result_depth1.value,"ROOT")
        self.assertFalse("test" in result_depth1)
        self.assertTrue("bloo" in result_depth1)
                                    
                                      
        
        
        
    #Test adding an array
    #Check an array leaf can only be a leaf 
    #Test testing
    #Test removing
    #Test Exclusions
    #Test getting
        
        
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
