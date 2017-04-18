"""
	BASIC testing of the ELTrie
"""
import unittest
import IPython
import logging as root_logger
from random import random
from test_context import ielpy
from ielpy.ELUtil import EL
from ielpy.ELStructure import ELROOT, ELPAIR, ELVAR
from ielpy.ELFactStructure import ELFACT
from ielpy.ELResults import ELSuccess, ELFail
from ielpy.ELTrie import ELTrie
from fractions import Fraction


base_root = ELROOT(EL.DOT)
root_fact = ELFACT([base_root])
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
        """ Check the trie is no longer empty upon adding: '.test' """
        self.assertTrue(self.trie.is_empty())
        #Create the fact: .test
        base_term = ELPAIR("test")
        base_fact = ELFACT([base_root,base_term])
        result = self.trie.push(base_fact)
        self.assertTrue(result)
        self.assertIsInstance(result, ELSuccess)
        self.assertFalse(self.trie.is_empty())

    def test_adding_empty_fact(self):
        """ Check that just adding '.' does not change empty state """
        self.assertTrue(self.trie.is_empty())
        fact = ELFACT(r=True)
        result = self.trie.push(fact)
        self.assertTrue(result)
        self.assertTrue(self.trie.is_empty())
        
    def test_getting(self):
        """ Check adding .test allows getting .test """
        base_term = ELPAIR("test")
        #base_fact ~= ".test"
        base_fact = ELFACT([base_root,base_term])
        add_response = self.trie.push(base_fact)
        result = self.trie.get(ELFACT([base_root]))
        self.assertTrue(add_response)
        self.assertIsInstance(result,ELSuccess)
        retrieved_node = self.trie[result.bindings[0].uuid]
        self.assertEqual(retrieved_node,"ROOT")
        #One child only
        self.assertEqual(len(retrieved_node),1)

    def test_multi_add(self):
        """ check adding .test and .blah non exclusively works in simplest case """
        base_fact1 = ELFACT(r=True).pair('test')
        base_fact2 = ELFACT(r=True).pair('blah')
        #now add:
        add_result1 = self.trie.push(base_fact1)
        add_result2 = self.trie.push(base_fact2)
        #verify success
        self.assertTrue(add_result1)
        self.assertTrue(add_result2)
        #Now get the root and see the children are there:
        root = self.trie.root
        self.assertEqual(root.value,"ROOT")
        self.assertTrue("test" in root.children)
        self.assertTrue("blah" in root.children)

    def test_fact_len(self):
        """ Check adding a fact .test.bloo is of depth 2 """
        base_fact = ELFACT()
        self.assertEqual(len(base_fact),0)
        base_fact.insert(ELROOT())
        self.assertEqual(len(base_fact),1)
        base_fact.insert(ELPAIR("test"))
        self.assertEqual(len(base_fact),2)
        base_fact.insert(ELPAIR("bloo"))
        self.assertEqual(len(base_fact),3)

    def test_fact_addition_of_depth_2_invalidates_empty(self):
        """ Check that facts of greater depths can be added 
        + .test.bloo
        """
        base_fact = ELFACT(r=True).pair("test").pair("bloo")
        self.assertEqual(len(base_fact),3)
        self.assertTrue(self.trie.is_empty())
        result = self.trie.push(base_fact)
        self.assertTrue(result)
        self.assertFalse(self.trie.is_empty())

    def test_fact_addition_of_depth_2_actually_adds(self):
        """ check that the data added to the trie of a depth 2 fact is actually added 
        + .test.bloo, get .test and .test.bloo
        """
        base_fact = ELFACT(r=True).pair("test").pair("bloo")
        self.assertEqual(len(base_fact),3)
        self.assertTrue(self.trie.is_empty())
        successOrFail = self.trie.push(base_fact)
        self.assertTrue(successOrFail)
        self.assertEqual(len(self.trie.root),1)
        
        #Get the first node:
        query = ELFACT(r=True).pair("test")
        result_depth1 = self.trie.get(query)
        result_depth1_node_uuid = result_depth1.bindings[0].uuid
        result_depth1_node = self.trie[result_depth1_node_uuid]
        self.assertEqual(len(result_depth1_node),1)
        
        

    def test_fact_addition_doesnt_duplicate(self):
        """ Check that adding the same fact, or head components of the same fact
        twice, doesnt duplicate those facts. .test.bloo * 2
        """
        logging.debug("Starting bad test")
        base_fact = ELFACT(r=True).pair("test").pair("bloo")
        self.trie.push(base_fact)
        successOrFail = self.trie.push(base_fact)
        self.assertTrue(successOrFail)
        #check the root node:
        self.assertEqual(len(self.trie.root),1)
        
        #Check the test node:
        test_node_result = self.trie.get(ELFACT(r=True).pair('test'))
        self.assertTrue(test_node_result)
        self.assertIsInstance(test_node_result, ELSuccess)
        test_node_uuid = test_node_result.bindings[0].uuid
        test_node_actual = self.trie[test_node_uuid]
        self.assertEqual(len(test_node_actual),1)

        
    def test_exclusion_addition(self):
        """ Check adding an exclusion operator works .test!blah """
        base_fact = ELFACT(r=True).epair("test").pair('blah')
        successOrFail = self.trie.push(base_fact)
        self.assertTrue(successOrFail)
        result = self.trie.get(ELFACT(r=True).epair("test"))
        self.assertTrue(result)
        self.assertIsInstance(result,ELSuccess)

    def test_non_exclusion_lift_to_exclusion(self):
        """ Check lifting a trie node to exclusive works
        .test.bloo -> .test!bloo
        .test.blah -> ''
        """
        base_fact = ELFACT(r=True).pair("test").pair("bloo")
        base_fact2 = ELFACT(r=True).pair("test").pair("blah")
        ex_fact =  ELFACT(r=True).epair("test").pair("bloo")
        self.trie.push(base_fact)
        self.trie.push(base_fact2)
        self.assertTrue(self.trie.query(base_fact.query()))
        self.assertTrue(self.trie.query(base_fact2.query()))
        self.assertFalse(self.trie.query(ex_fact.query()))

        self.trie.push(ex_fact)
        
        self.assertFalse(self.trie.query(base_fact.query()))
        self.assertFalse(self.trie.query(base_fact2.query()))
        self.assertTrue(self.trie.query(ex_fact.query()))

        

    def test_exclusion_rewrite(self):
        """ Check that updating a value of an exclusion node works 
        .test!bloo => .test!blah
        """
        orig_fact = ELFACT(r=True).epair("test").pair("bloo")
        update_fact = ELFACT(r=True).epair("test").pair("blah")
        self.trie.push(orig_fact)
        gotten = self.trie.get(orig_fact)
        self.assertTrue(gotten)
        
        self.trie.push(update_fact)
        gotten_2 = self.trie.get(orig_fact)
        self.assertFalse(gotten_2)
        gotten_3 = self.trie.get(update_fact)
        self.assertTrue(gotten_3)
        
    def test_exclusion_to_non_downscale(self):
        """ Check that .a.b!c => a.b.c passes and updates """
        ex_fact = ELFACT(r=True).pair("a").epair("b").pair("c")
        non_ex_fact = ELFACT(r=True).pair("a").pair("b").pair("c")
        non_ex_fact_2 = ELFACT(r=True).pair("a").pair("b").pair("d")
        result_1 = self.trie.push(ex_fact)
        self.assertTrue(result_1)
        initial = self.trie.get(ex_fact)
        self.assertTrue(initial)
        #then update:
        update_1 = self.trie.push(non_ex_fact)
        update_2 = self.trie.push(non_ex_fact_2)
        self.assertTrue(update_1)
        self.assertTrue(update_2)
        old_fact = self.trie.get(ex_fact)
        self.assertFalse(old_fact)
        new_fact_1 = self.trie.get(non_ex_fact)
        self.assertTrue(new_fact_1)
        new_fact_2 = self.trie.get(non_ex_fact_2)
        self.assertTrue(new_fact_2)


        

    def test_adding_array(self):
        """ Check .a.b.[1,2,3] succeeds """
        test_fact = ELFACT(r=True).pair("a").pair("b").insert([1,2,3])
        expanded = test_fact.expand()
        for f in expanded:
            s = self.trie.push(f)
            self.assertTrue(s)

    def test_getting_array(self):
        """ Check you can get .a.b.[1,2,3] """
        #todo: utilize variables here
        None


    def test_array_subvalues_fails(self):
        """ Check .a.b.[1,2,3].d fails """
        bad_fact = ELFACT(r=True).pair("a").pair("b").pair([1,2,3]).pair("d")
        f = self.trie.push(bad_fact)
        self.assertFalse(f)
        
    def test_decimal(self):
        """ Check .a.b.1d5 works """
        decimal = ELFACT(r=True).pair("a").pair("b").pair(1.5)
        s = self.trie.push(decimal)
        self.assertTrue(s)
        fact = ELFACT(r=True).pair("a").pair("b").pair(1.5)
        gotten = self.trie.get(fact)
        self.assertTrue(gotten)
        self.assertIsInstance(gotten, ELSuccess)
        gotten2 = self.trie.get(ELFACT(r=True).pair("a").pair("b"))
        self.assertTrue(gotten2)
        self.assertIsInstance(gotten2, ELSuccess)

    def test_fraction(self):
        """ Check .a.b.1/5 works """
        fraction = ELFACT(r=True).pair("a").pair("b").pair(Fraction(1,5))
        self.trie.push(fraction)
        gotten = self.trie.get(ELFACT(r=True).pair("a").pair("b").pair(Fraction(1,5)))
        self.assertTrue(gotten)
        fraction_node_uuid = gotten.bindings[0].uuid
        fraction_node = self.trie[fraction_node_uuid]
        self.assertEqual(fraction_node,Fraction(1,5))
                

    def test_terminal_string(self):
        """ Check .a.b."blah bloo" works """
        string_fact = ELFACT(r=True).pair("a").pair("b").pair("blah bloo")
        s = self.trie.push(string_fact)
        result = self.trie.query(string_fact.query())
        self.assertTrue(result)
        
        

    def test_non_terminal_string(self):
        """ Check .a.b."blah bloo".c works """
        string_fact = ELFACT(r=True).pair("a").pair("b").pair("blah bloo").pair("c")
        self.trie.push(string_fact)
        result = self.trie.query(string_fact.query())
        self.assertTrue(result)
        

    def test_negative_number(self):
        """ Check that .a.b.-5 works """
        #todo: utilize variable getting
        neg_fact = ELFACT(r=True).pair("a").pair("b").pair(-5)
        pre_assertion = self.trie.query(neg_fact.query())
        self.assertFalse(pre_assertion)
        self.trie.push(neg_fact)
        post_assertion = self.trie.query(neg_fact.query())
        self.assertTrue(post_assertion)
        

    def test_negative_number_subvalues(self):
        """ Check that .a.b.-5.c works """
        neg_sub_fact = ELFACT(r=True).pair("a").pair("b").pair(-5).pair("c")
        s = self.trie.push(neg_sub_fact)
        result = self.trie.query(neg_sub_fact.query())
        self.assertTrue(result)

    def test_trie_query(self):
        """ Check that queries return accurately """
        base_fact = ELFACT(r=True).pair('a').pair('b').pair('c')
        s = self.trie.push(base_fact)
        queried = self.trie.query(base_fact.query())
        self.assertTrue(queried)
        
    def test_trie_retraction(self):
        """ Check that a fact can be retracted """
        base_fact = ELFACT(r=True).pair('a').pair('b').pair('c')
        self.trie.push(base_fact)
        self.assertTrue(self.trie.query(base_fact.query()))
        self.trie.pop(base_fact)
        self.assertFalse(self.trie.query(base_fact.query()))
        

    def test_trie_retraction_doesnt_clobber(self):
        """ make sure only nodes that don't have other children are retracted """
        base_fact1 = ELFACT(r=True).pair('a').pair('b')
        base_fact2 = base_fact1.copy()
        base_fact1.pair('c')
        base_fact2.pair('d')
        self.trie.push(base_fact1)
        self.trie.push(base_fact2)
        self.assertTrue(self.trie.query(base_fact1.query()))
        self.assertTrue(self.trie.query(base_fact2.query()))
        self.trie.pop(base_fact1)
        self.assertTrue(self.trie.query(base_fact2.query()))
        self.assertFalse(self.trie.query(base_fact1.query()))

    def test_trie_exclusive_retraction(self):
        """ Check that retracting a fact with an exclusive component works """
        base_fact = ELFACT(r=True).pair('a').epair('b').pair('c')
        self.trie.push(base_fact)
        self.assertTrue(self.trie.query(base_fact.query()))
        self.trie.pop(base_fact)
        self.assertFalse(self.trie.query(base_fact.query()))

    def test_trie_retraction_of_non_existent_fact(self):
        """ check that retracting something non-existent works """
        base_fact = ELFACT(r=True).pair('a').epair('b').pair('c')
        retraction = ELFACT(r=True).pair('a').epair('b').pair('d')
        self.trie.push(base_fact)
        self.assertTrue(self.trie.query(base_fact.query()))
        self.trie.pop(retraction)
        self.assertTrue(self.trie.query(base_fact.query()))
                        

    def test_trie_metrics(self):
        """ Check the dfs of the trie for metrics works in a simple case """
        base_fact1 = ELFACT(r=True).pair('a').epair('b').pair('c')
        base_fact2 = ELFACT(r=True).pair('a').pair('d').pair('e')
        self.trie.push(base_fact1)
        self.trie.push(base_fact2)
        results = self.trie.dfs_for_metrics()
        self.assertEqual(results['maxDepth'],3)
        self.assertEqual(len(results['leaves']),2)
        base_fact3 = ELFACT(r=True).pair('a').pair('d').pair('f').pair('g')
        self.trie.push(base_fact3)
        results2 = self.trie.dfs_for_metrics()
        self.assertEqual(results2['maxDepth'],4)
        self.assertEqual(len(results2['leaves']),3)
        retract_fact = ELFACT(r=True).pair('a').pair('d')
        self.trie.pop(retract_fact)
        results3 = self.trie.dfs_for_metrics()
        self.assertEqual(results3['maxDepth'],3)
        

    def test_trie_get_variables(self):
        """ Get the possible entries for a variable """
        base_fact1 = ELFACT(r=True).pair('a').epair('b').pair('c')
        base_fact2 = ELFACT(r=True).pair('a').pair('d').pair('e')
        self.trie.push(base_fact1)
        self.trie.push(base_fact2)
        query_fact = ELFACT(r=True).pair('a').var('x')
        results = self.trie.get(query_fact)
        self.assertTrue(results)
        self.assertIsInstance(results,ELSuccess)
        self.assertEqual(results.path, query_fact)
        self.assertEqual(len(results),2)
        bindings = [x for x in results.bindings]

        x_b_in_bindings = bindings[0]['x'].value == 'b' or \
                          bindings[1]['x'].value == 'b'

        x_d_in_bindings = bindings[0]['x'].value == 'd' or \
                          bindings[1]['x'].value == 'd'

        self.assertTrue(x_b_in_bindings)
        self.assertTrue(x_d_in_bindings)

        

    def test_trie_get_variables_when_only_one_child(self):
        """ Get the possible entry for a variable """
        base_fact1 = ELFACT(r=True).pair('a').epair('b').pair('c')
        base_fact2 = ELFACT(r=True).pair('b').pair('d').pair('e')
        self.trie.push(base_fact1)
        self.trie.push(base_fact2)
        query_fact = ELFACT(r=True).pair('a').var('x')
        results = self.trie.get(query_fact)
        self.assertTrue(results)
        self.assertIsInstance(results,ELSuccess)
        self.assertEqual(results.path, query_fact)
        bindings = [x for x in results.bindings]
        self.assertEqual(len(results.bindings),1)
        self.assertTrue(bindings[0]['x'].value == 'b')



    def test_trie_get_dfs_of_query(self):
        """ Get all the possible bindings as a flat array for queries like:
        	.a.b.$x.$y 
        """
        #both match .a.$x.c.$y
        base_fact1 = ELFACT(r=True).pair('a').pair('b').pair('c').pair('d')
        base_fact2 = ELFACT(r=True).pair('a').pair('f').pair('c').pair('e')
        self.trie.push(base_fact1)
        self.trie.push(base_fact2)
        query = ELFACT(r=True).pair('a').pair(ELVAR('x')).pair('c').var('y')
        results = self.trie.get(query)
        self.assertIsInstance(results,ELSuccess);
        self.assertEqual(results.path, query)
        self.assertEqual(len(results.bindings),2)
        bindings = [x for x in results.bindings]
        xb_yd_in_one_binding = (bindings[0]['x'].value == 'b' and \
                               bindings[0]['y'].value == 'd') or \
                               (bindings[1]['x'].value == 'b' and
                                bindings[1]['y'].value == 'd')
        
        xf_ye_in_one_binding = (bindings[0]['x'].value == 'f' and \
                                bindings[0]['y'].value == 'e') or \
                                (bindings[1]['x'].value == 'f' and \
                                 bindings[1]['y'].value == 'e')
        self.assertTrue(xb_yd_in_one_binding)
        self.assertTrue(xf_ye_in_one_binding)

    


    def test_trie_get_dfs_of_query_expanded_base(self):
        """ Check that variation of the lower variable are retrieved, even
        when the higher term remains the same
        """
        base_fact1 = ELFACT(r=True).pair('a').pair('b').pair('c').pair('d')
        base_fact2 = ELFACT(r=True).pair('a').pair('b').pair('c').pair('e')
        self.trie.push(base_fact1)
        self.trie.push(base_fact2)
        query = ELFACT(r=True).pair('a').pair(ELVAR('x')).pair('c').var('y')
        results = self.trie.get(query);
        self.assertIsInstance(results,ELSuccess);
        self.assertEqual(results.path, query)
        self.assertEqual(len(results.bindings),2)
        bindings = [x for x in results.bindings]

        xb_yd_in_one_binding = (bindings[0]['x'].value == 'b' and \
                                bindings[0]['y'].value == 'd') or \
                                (bindings[1]['x'].value == 'b' and \
                                 bindings[1]['y'].value == 'd')

        xb_ye_in_one_binding = (bindings[0]['x'].value == 'b' and \
                                bindings[0]['y'].value == 'e') or \
                                (bindings[1]['x'].value == 'b' and \
                                 bindings[1]['y'].value == 'e')

        self.assertTrue(xb_yd_in_one_binding)
        self.assertTrue(xb_ye_in_one_binding)

    def test_trie_get_dfs_of_query_excluding_non_matches(self):
        """ Similar to getting dfs of query, but rejecting only partial matches """
        #both match .a.$x but not .a.$x.c.$y
        base_fact1 = ELFACT(r=True).pair('a').pair('b').pair('c').pair('d')
        base_fact2 = ELFACT(r=True).pair('a').pair('f').pair('g').pair('e')
        self.trie.push(base_fact1)
        self.trie.push(base_fact2)        
        query = ELFACT(r=True).pair('a').pair(ELVAR('x')).pair('c').var('y')
        results = self.trie.get(query);
        self.assertIsInstance(results,ELSuccess);
        self.assertEqual(results.path, query)
        self.assertEqual(len(results.bindings),1)
        xb_yd_in_binding = results.bindings[0]['x'].value == 'b' and \
                           results.bindings[0]['y'].value == 'd'

        self.assertTrue(xb_yd_in_binding)
        

    def test_exclusion_query_terminal_mismatch(self):
        """
        .a.b!c
        .a.b?  => assumes .a.b.? but needs to check for .a.b!?
        """
        base_fact = ELFACT(r=True).pair('a').epair('b').pair('c')
        query = base_fact.query()
        query2 = ELFACT(r=True).pair('a').pair('b').query()
        self.trie.push(base_fact)
        result = self.trie.query(query)
        self.assertTrue(result)
        result2 = self.trie.query(query2)
        self.assertTrue(result2)

        
        
    #test trie dump
    #test trie pickle?

        
if __name__ == "__main__":
    LOGLEVEL = root_logger.DEBUG
    LOG_FILE_NAME = "test_ELTrie.log"
    root_logger.basicConfig(filename=LOG_FILE_NAME, level=LOGLEVEL, filemode='w')
    console = root_logger.StreamHandler()
    console.setLevel(root_logger.DEBUG)
    root_logger.getLogger('').addHandler(console)
    logging = root_logger.getLogger(__name__)
    root_logger.disable(root_logger.CRITICAL)
    ##############################
    
    unittest.main()
