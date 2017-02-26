"""
	BASIC testing of the ELTrie
"""
import unittest
import IPython
import logging as root_logger
from random import random
from test_context import ELParser
from ELParser.ELTrie import ELTrie
from ELParser import ELBaseData as ELBD
from fractions import Fraction


base_root = ELBD.ELROOT(ELBD.EL.DOT)
root_fact = ELBD.ELFACT([base_root])
logging = root_logger.getLogger(__name__)


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
        """ Check the trie is no longer empty upong adding: ".test  """
        self.assertTrue(self.trie.is_empty())
        #Create the fact: .test
        base_term = ELBD.ELTERM("test")
        base_fact = ELBD.ELFACT([base_root,base_term])
        result = self.trie.push(base_fact)
        self.assertTrue(result)
        self.assertIsInstance(result, ELBD.ELSuccess)
        self.assertFalse(self.trie.is_empty())

    def test_adding_empty_fact(self):
        """ Check that just adding '.' does not change empty state """
        self.assertTrue(self.trie.is_empty())
        result = self.trie.push(ELBD.ELFACT([ELBD.ELROOT(ELBD.EL.DOT)]))
        self.assertFalse(result)
        self.assertIsInstance(result,ELBD.ELFail)
        self.assertTrue(self.trie.is_empty())
        
    def test_getting(self):
        """ Check adding .test allows getting .test """
        base_term = ELBD.ELTERM("test")
        #base_fact ~= ".test"
        base_fact = ELBD.ELFACT([base_root,base_term])
        add_response = self.trie.push(base_fact)
        result = self.trie.get(ELBD.ELFACT([base_root]))
        self.assertTrue(add_response)
        self.assertIsInstance(result,ELBD.ELGet)
        self.assertEqual(result.value,"ROOT")
        #One child, test.
        self.assertEqual(result.children,["test"])

    def test_multi_add(self):
        """ check adding .test and .blah non exclusively works in simplest case """
        base_term1 = ELBD.ELTERM("test")
        base_term2 = ELBD.ELTERM("blah")
        base_fact1 = ELBD.ELFACT([base_root,base_term1])
        base_fact2 = ELBD.ELFACT([base_root,base_term2])
        #now add:
        add_result1 = self.trie.push(base_fact1)
        add_result2 = self.trie.push(base_fact2)
        #verify success
        self.assertTrue(add_result1)
        self.assertTrue(add_result2)
        #Now get the root and see the children are there:
        root = self.trie.get(root_fact)
        self.assertIsInstance(root,ELBD.ELGet)
        self.assertEqual(root.value,"ROOT")
        self.assertTrue("test" in root.children)
        self.assertTrue("blah" in root.children)

    def test_fact_len(self):
        """ Check adding a fact .test.bloo is of depth 2 """
        base_fact = ELBD.ELFACT()
        self.assertEqual(len(base_fact),0)
        base_fact.push(ELBD.ELROOT())
        self.assertEqual(len(base_fact),0)
        base_fact.push(ELBD.ELPAIR("test"))
        self.assertEqual(len(base_fact),1)
        base_fact.push(ELBD.ELPAIR("bloo"))
        self.assertEqual(len(base_fact),2)

    def test_fact_completion(self):
        """ Check that an ELFACT recognises when its finished 
        .a.  -> incomplete.  .a.b.c -> finished
        """
        base_fact = ELBD.ELFACT()
        self.assertFalse(base_fact.complete())
        base_fact.push(ELBD.ELROOT())
        self.assertFalse(base_fact.complete())
        base_fact.push(ELBD.ELPAIR("blah"))
        self.assertFalse(base_fact.complete())
        base_fact.push(ELBD.ELTERM("bloo"))
        self.assertTrue(base_fact.complete())

    def test_fact_addition_of_depth_2_invalidates_empty(self):
        """ Check that facts of greater depths can be added 
        + .test.bloo
        """
        base_fact = ELBD.ELFACT(r=True).push(ELBD.ELPAIR("test")).push(ELBD.ELTERM("bloo"))
        self.assertEqual(len(base_fact),2)
        self.assertTrue(self.trie.is_empty())
        result = self.trie.push(base_fact)
        self.assertTrue(result)
        self.assertFalse(self.trie.is_empty())

    def test_fact_addition_of_depth_2_actually_adds(self):
        """ check that the data added to the trie of a depth 2 fact is actually added 
        + .test.bloo, get .test and .test.bloo
        """
        base_fact = ELBD.ELFACT(r=True).push(ELBD.ELPAIR("test")).push(ELBD.ELTERM("bloo"))
        self.assertEqual(len(base_fact),2)
        self.assertTrue(self.trie.is_empty())
        successOrFail = self.trie.push(base_fact)
        self.assertTrue(successOrFail)
        result = self.trie.get(ELBD.ELFACT(r=True))
        self.assertEqual(result.value,"ROOT")
        self.assertTrue("test" in result)
        self.assertFalse("bloo" in result)
        result_depth1 = self.trie.get(ELBD.ELFACT(r=True).push(ELBD.ELTERM("test")))
        self.assertNotEqual(result_depth1.value,"ROOT")
        self.assertFalse("test" in result_depth1)
        self.assertTrue("bloo" in result_depth1)
        self.assertEqual(result_depth1,"test")
        self.assertEqual(len(result_depth1),1)
        result_depth2 = self.trie.get(ELBD.ELFACT(r=True).push(ELBD.ELTERM("test")).push(ELBD.ELTERM("bloo")))
        self.assertEqual(len(result_depth2), 0)
        self.assertEqual(result_depth2,"bloo")

    def test_fact_addition_doesnt_duplicate(self):
        """ Check that adding the same fact, or head components of the same fact
        twice, doesnt duplicate those facts. .test.bloo * 2
        """
        base_fact = ELBD.ELFACT(r=True).push(ELBD.ELPAIR("test")).push(ELBD.ELTERM("bloo"))
        self.trie.push(base_fact)
        successOrFail = self.trie.push(base_fact)
        self.assertTrue(successOrFail)
        base_result = self.trie.get(ELBD.ELFACT(r=True))
        self.assertEqual(base_result.value,"ROOT")
        self.assertEqual(len(base_result.children),1)
        self.assertTrue("test" in base_result.children)
        self.assertFalse("bloo" in base_result.children)
        depth1_result = self.trie.get(ELBD.ELFACT(r=True).push(ELBD.ELTERM("test")))
        self.assertEqual(depth1_result.value,"test")
        self.assertEqual(len(depth1_result.children),1)
        self.assertFalse("test" in depth1_result.children)
        self.assertTrue("bloo" in depth1_result.children)

    def test_exclusion_addition(self):
        """ Check adding an exclusion operator works .test!blah """
        base_fact = ELBD.ELFACT(r=True).push(ELBD.ELPAIR("test",ELBD.EL.EX)).push(ELBD.ELTERM('blah'))
        successOrFail = self.trie.push(base_fact)
        self.assertTrue(successOrFail)
        result = self.trie.get(ELBD.ELFACT(r=True).push(ELBD.ELTERM("test")))
        self.assertIsInstance(result,ELBD.ELGet)
        self.assertEqual(result,"test")
        self.assertTrue("blah" in result)

    def test_non_exclusion_lift_to_exclusion(self):
        """ Check lifting a trie node to exclusive works
        .test.bloo -> .test!bloo
        .test.blah -> ''
        """
        root_logger.disable(root_logger.NOTSET)
        logging.debug("Exclusion lift")
        base_fact = ELBD.ELFACT(r=True).push(ELBD.ELPAIR("test")).push(ELBD.ELTERM("bloo"))
        base_fact2 = ELBD.ELFACT(r=True).push(ELBD.ELPAIR("test")).push(ELBD.ELTERM("blah"))
        ex_fact =  ELBD.ELFACT(r=True).push(ELBD.ELPAIR("test",ELBD.EL.EX)).push(ELBD.ELTERM("bloo"))
        s = self.trie.push(base_fact)
        s2 = self.trie.push(base_fact2)
        self.assertTrue(s)
        result = self.trie.get(ELBD.ELFACT(r=True).push(ELBD.ELTERM("test")))
        self.assertEqual(len(result),2)
        self.assertTrue("bloo" in result)
        self.assertTrue("blah" in result)
        s3 = self.trie.push(ex_fact)
        self.assertTrue(s2)
        result_2 = self.trie.get(ELBD.ELFACT(r=True).push(ELBD.ELTERM("test")))
        self.assertEqual(len(result_2),1)
        self.assertTrue("bloo" in result_2)
        self.assertFalse("blah" in result_2)
        root_logger.disable(root_logger.CRITICAL)

    def test_exclusion_rewrite(self):
        """ Check that updating a value of an exclusion node works 
        .test!bloo => .test!blah
        """
        root_logger.disable(root_logger.NOTSET)
        logging.debug("Exclusion rewrite")
        orig_fact = ELBD.ELFACT(r=True).push(ELBD.ELPAIR("test",ELBD.EL.EX)).push(ELBD.ELTERM("bloo"))
        update_fact = ELBD.ELFACT(r=True).push(ELBD.ELPAIR("test",ELBD.EL.EX)).push(ELBD.ELTERM("blah"))
        self.trie.push(orig_fact)
        gotten = self.trie.get(ELBD.ELFACT(r=True).push(ELBD.ELTERM("test")))
        self.assertTrue("bloo" in gotten)
        self.trie.push(update_fact)
        gotten_2 = self.trie.get(ELBD.ELFACT(r=True).push(ELBD.ELTERM("test")))
        self.assertTrue("blah" in gotten_2)
        self.assertFalse("bloo" in gotten_2)
        root_logger.disable(root_logger.CRITICAL)
        
    def test_exclusion_to_non_downscale(self):
        """ Check that .a.b!c => a.b.c passes and updates """
        ex_fact = ELBD.ELFACT(r=True).push(ELBD.ELPAIR("a")).push(ELBD.ELPAIR("b",ELBD.EL.EX)).push(ELBD.ELTERM("c"))
        non_ex_fact = ELBD.ELFACT(r=True).push(ELBD.ELPAIR("a")).push(ELBD.ELPAIR("b")).push(ELBD.ELTERM("c"))
        non_ex_fact_2 = ELBD.ELFACT(r=True).push(ELBD.ELPAIR("a")).push(ELBD.ELPAIR("b")).push(ELBD.ELTERM("d"))
        result_1 = self.trie.push(ex_fact)
        result_2 = self.trie.push(non_ex_fact)
        result_3 = self.trie.push(non_ex_fact_2)
        self.assertTrue(result_1)
        self.assertTrue(result_2)
        self.assertTrue(result_3)
        gotten = self.trie.get(ELBD.ELFACT(r=True).push(ELBD.ELPAIR("a")).push(ELBD.ELTERM("b")))
        self.assertTrue(gotten)
        self.assertEqual(len(gotten),2)
        self.assertEqual(gotten,"b")
        self.assertTrue("c" in gotten)
        self.assertTrue("d" in gotten)

    def test_adding_array(self):
        """ Check .a.b.[1,2,3] succeeds """
        test_fact = ELBD.ELFACT(r=True).pair("a").pair("b").term([1,2,3])
        s = self.trie.push(test_fact)
        self.assertTrue(s)

    def test_getting_array(self):
        """ Check you can get .a.b.[1,2,3] """
        test_fact = ELBD.ELFACT(r=True).pair("a").pair("b").term([1,2,3])
        self.trie.push(test_fact)
        gotten = self.trie.get(ELBD.ELFACT(r=True).pair("a").pair("b"))
        self.assertEqual(gotten,"b")
        self.assertEqual(len(gotten),1)
        self.assertTrue([1,2,3] in gotten)
        self.assertFalse([3,4,5] in gotten)
        gotten_2 = self.trie.get(ELBD.ELFACT(r=True).pair("a").pair("b").term([1,2,3]))
        self.assertEqual(gotten_2,[1,2,3])
        self.assertEqual(gotten_2.value[1],2)
        self.assertNotEqual(gotten_2,[2,3,4])
        self.assertEqual(len(gotten_2),0)


    def test_array_subvalues_fails(self):
        """ Check .a.b.[1,2,3].d fails """
        bad_fact = ELBD.ELFACT(r=True).pair("a").pair("b").pair([1,2,3]).term("d")
        f = self.trie.push(bad_fact)
        self.assertFalse(f)
        
    def test_decimal(self):
        """ Check .a.b.1d5 works """
        decimal = ELBD.ELFACT(r=True).pair("a").pair("b").term(1.5)
        s = self.trie.push(decimal)
        self.assertTrue(s)
        gotten = self.trie.get(ELBD.ELFACT(r=True).pair("a").pair("b"))
        self.assertEqual(gotten,"b")
        self.assertEqual(len(gotten),1)
        self.assertTrue(1.5 in gotten)
        gotten2 = self.trie.get(ELBD.ELFACT(r=True).pair("a").pair("b").pair(1.5))
        self.assertEqual(gotten2,1.5)
        self.assertEqual(len(gotten2),0)

    def test_fraction(self):
        """ Check .a.b.1/5 works """
        fraction = ELBD.ELFACT(r=True).pair("a").pair("b").term(Fraction(1,5))
        s = self.trie.push(fraction)
        gotten = self.trie.get(ELBD.ELFACT(r=True).pair("a").pair("b"))
        self.assertEqual(gotten,"b")
        self.assertEqual(len(gotten),1)
        self.assertTrue(Fraction(1,5) in gotten)
                

    def test_terminal_string(self):
        """ Check .a.b."blah bloo" works """
        string_fact = ELBD.ELFACT(r=True).pair("a").pair("b").term("blah bloo")
        s = self.trie.push(string_fact)
        gotten = self.trie.get(ELBD.ELFACT(r=True).pair("a").pair("b"))
        self.assertEqual(gotten,"b")
        self.assertEqual(len(gotten),1)
        self.assertTrue("blah bloo" in gotten)
        

    def test_non_terminal_string(self):
        """ Check .a.b."blah "bloo".c works """
        string_fact = ELBD.ELFACT(r=True).pair("a").pair("b").pair("blah bloo").term("c")
        s = self.trie.push(string_fact)
        gotten = self.trie.get(ELBD.ELFACT(r=True).pair("a").pair("b").pair("blah bloo"))
        self.assertEqual(gotten,"blah bloo")
        self.assertEqual(len(gotten),1)
        self.assertTrue("c" in gotten)
        

    def test_negative_number(self):
        """ Check that .a.b.-5 works """
        neg_fact = ELBD.ELFACT(r=True).pair("a").pair("b").term(-5)
        s = self.trie.push(neg_fact)
        gotten = self.trie.get(ELBD.ELFACT(r=True).pair("a").pair("b"))
        self.assertEqual(gotten,"b")
        self.assertEqual(len(gotten),1)
        self.assertTrue(-5 in gotten)
        

    def test_negative_number_subvalues(self):
        """ Check that .a.b.-5.c works """
        neg_sub_fact = ELBD.ELFACT(r=True).pair("a").pair("b").pair(-5).term("c")
        s = self.trie.push(neg_sub_fact)
        gotten = self.trie.get(ELBD.ELFACT(r=True).pair("a").pair("b").pair(-5))
        self.assertEqual(gotten,-5)
        self.assertEqual(len(gotten),1)
        self.assertTrue("c" in gotten)

    #TODO: test trie query
        
    #Test removing
    #test trie dump
    #test trie pickle?

        
if __name__ == "__main__":
    LOGLEVEL = root_logger.DEBUG
    LOG_FILE_NAME = "ELTrie_tests.log"
    root_logger.basicConfig(filename=LOG_FILE_NAME, level=LOGLEVEL, filemode='w')
    console = root_logger.StreamHandler()
    console.setLevel(root_logger.INFO)
    root_logger.getLogger('').addHandler(console)
    logging = root_logger.getLogger(__name__)
    root_logger.disable(root_logger.CRITICAL)
    ##############################
    
    unittest.main()
