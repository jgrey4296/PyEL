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
from ELParser import ELRuntime as ELR
from fractions import Fraction

#Parser returns a ParseResult, which is an array of actual parse data structures

gen_n = lambda: 1 + int(random()*20)

class ELRuntime_Tests(unittest.TestCase):

    def setUp(self):
        self.runtime = ELR.ELRuntime()
    def tearDown(self):
        self.runtime = None
 
    def test_simple(self):
        """ Check the runtime works in a minimal case """
        self.assertIsNotNone(self.runtime)
        self.assertIsInstance(self.runtime,ELR.ELRuntime)

    def test_simple_fact_assertion(self):
        """ Check facts can be asserted """
        test_fact = ".this.is.a.test"
        self.runtime(test_fact)
        check_fact = ".this.is.a"
        parsed = self.runtime.parser(check_fact)[0]
        retrieved = self.runtime.trie.get(parsed)
        self.assertTrue(retrieved)
        self.assertEqual(retrieved,'a')
        self.assertIn('test',retrieved)


    def test_simple_fact_query(self):
        """ check an asserted fact can be tested for """
        test_fact = ".this.is.a.test"
        self.runtime(test_fact)
        self.assertTrue(self.runtime.query(test_fact + "?"))

    def test_simple_fact_query_fail(self):
        """ Check a non asserted fact fails a query """
        test_fact = ".this.hasnt.been.added"
        self.assertFalse(self.runtime.query(test_fact + "?"))
        
    def test_multi_fact_assertion(self):
        """ Check multiple assertions in are all added """
        facts = [".this.is.a.test", ".this.is.another.test", ".and.a.third"]
        self.runtime("\n".join(facts))
        for fact in facts:
            self.assertTrue(self.runtime.query(fact + "?"))

    def test_multi_query(self):
        """ Check multiple queries at the same tiem work """
        facts = [".this.is.a.test", ".this.is.another.test", ".and.a.third"]
        self.runtime("\n".join(facts))
        as_queries = [x + "?" for x in facts]
        self.assertTrue(self.runtime.query("\n".join(as_queries)))

    def test_query_call(self):
        """ Check queries can be triggered by calling the runtime """
        base_fact = ".this.is.a.test"
        query = ".this.is?"
        self.runtime(base_fact)
        self.assertTrue(self.runtime(query)[0])
        
        
    def test_simple_fact_retraction(self):
        """ Check facts can be retracted """
        assert_fact = ".retraction.test.this.is.a.test"
        retract_fact = "~.retraction.test.this.is"
        query = ".retraction.test.this.is.a.test?"
        self.runtime(assert_fact)
        self.assertTrue(self.runtime.query(query))
        self.runtime(retract_fact)
        self.assertFalse(self.runtime(query)[0])
        
    def test_negated_query(self):
        """ Check queries can test for negatives """  
        base_fact = ".this.is.a.test"
        query = "~.this.is.a.test?"
        self.assertTrue(self.runtime(query)[0])
        self.runtime(base_fact)
        self.assertFalse(self.runtime(query)[0])
        
    def test_exclusion_semantics(self):
        """ Check the exclusion will override """
        self.runtime(".this.is.a.test")
        self.runtime(".this.is.a.blah")
        self.assertTrue(all(self.runtime(".this.is.a.test?\n.this.is.a.blah?")))
        self.runtime(".this.is.a!bloo")
        self.assertTrue(all(self.runtime("~.this.is.a.test?\n~.this.is.a.blah?\n.this.is.a!bloo?")))

    def test_exclusion_query_resolution(self):
        """ Test that an queries respect exclusion operators """
        self.runtime(".this.is.a!test")
        self.assertFalse(self.runtime(".this.is.a.test?")[0])
        self.assertTrue(self.runtime(".this.is.a!test?")[0])


    def test_rule_definition(self):
        """ Check that rules can be asserted """
        self.runtime(".this.is.a.test.rule.{ [] -> [] }")
        self.assertTrue(self.runtime(".this.is.a.test.rule?")[0])
        self.assertTrue(".this.is.a.test.rule." in self.runtime.rules)
        

    def test_rule_firing(self):
        None

    def test_rule_binding(self):
        None

    def test_rule_arith_action(self):
        None

    def test_fact_arrays(self):
        None

    def test_string_interpolation(self):
        None

    def test_fact_arithmetic(self):
        None

    def test_comments_are_ignored(self):
        None

    def test_rule_binding_balances(self):
        None

    def test_rule_comparisons(self):
        None

    def test_rule_binding_arith(self):
        None

    def test_rule_implicit_binding_comparison(self):
        None

    def test_rule_binding_non_equality(self):
        None

    def test_rule_near_operator(self):
        None

    def test_rule_near_operator_with_binding(self):
        None

    def test_global_binding(self):
        None

    def test_global_rebinding(self):
        None

    def test_subtree_testing(self):
        None

    def test_subtree_application(self):
        None

    def test_subtree_exclusive_application(self):
        None

    def test_subtree_variable_application(self):
        None
        
        
if __name__ == "__main__":
    LOGLEVEL = root_logger.DEBUG
    LOG_FILE_NAME = "ELRuntime_tests.log"
    root_logger.basicConfig(filename=LOG_FILE_NAME, level=LOGLEVEL, filemode='w')
    console = root_logger.StreamHandler()
    console.setLevel(root_logger.INFO)
    root_logger.getLogger('').addHandler(console)
    logging = root_logger.getLogger(__name__)
    root_logger.disable(root_logger.CRITICAL)
    ##############################
    unittest.main()
