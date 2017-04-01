"""
	BASIC testing of the ELParser
"""
import unittest
import logging as root_logger
import IPython
from random import random
from test_context import ELParser
from ELParser import ELPARSE
from ELParser import ELBaseData as ELBD
from ELParser import ELExceptions as ELE
from ELParser import ELRuntime as ELR
from fractions import Fraction

#Parser returns a ParseResult, which is an array of actual parse data structures

gen_n = lambda: 1 + int(random()*20)

class ELRuntime_Tests(unittest.TestCase):

    def setUp(self):
        self.runtime = ELR()
    def tearDown(self):
        self.runtime = None
 
    def test_simple(self):
        """ Check the runtime works in a minimal case """
        self.assertIsNotNone(self.runtime)
        self.assertIsInstance(self.runtime,ELR)

    def test_simple_fact_assertion(self):
        """ Check facts can be asserted """
        test_fact = ".this.is.a.test"
        self.runtime(test_fact)
        check_fact = ".this.is.a"
        parsed = self.runtime.parser(check_fact)[0]
        retrieved = self.runtime.trie.get(parsed)
        self.assertTrue(retrieved)

        parsed_false_fact = self.runtime.parser('.this.is.not.a.fact')[0]
        retrieved_false = self.runtime.trie.get(parsed_false_fact)
        self.assertFalse(retrieved_false)
        

    def test_simple_fact_query(self):
        """ check an asserted fact can be tested for """
        test_fact = ".this.is.a.test"
        self.runtime(test_fact)
        self.assertTrue(self.runtime(test_fact + "?"))

    def test_simple_fact_query_fail(self):
        """ Check a non asserted fact fails a query """
        test_fact = ".this.hasnt.been.added"
        self.assertFalse(self.runtime(test_fact + "?"))
        
    def test_multi_fact_assertion(self):
        """ Check multiple assertions in are all added """
        facts = [".this.is.a.test", ".this.is.another.test", ".and.a.third"]
        self.runtime("\n".join(facts))
        for fact in facts:
            self.assertTrue(self.runtime(fact + "?")[0])

    def test_multi_query(self):
        """ Check multiple queries at the same time work """
        facts = [".this.is.a.test", ".this.is.another.test", ".and.a.third"]
        self.runtime("\n".join(facts))
        as_queries = [x + "?" for x in facts]
        self.assertTrue(self.runtime("\n".join(as_queries)))

    def test_multi_query_fail(self):
        """ check that a multi query fails if one of the conditions fails """
        facts = [".this.is.a.test", ".this.is.another.test"]
        self.runtime("\n".join(facts))
        as_queries = [x+"?" for x in facts]
        as_queries.append(".and.a.third?")
        self.assertFalse(all(self.runtime("\n".join(as_queries))))
        
    def test_query_call(self):
        """ Check queries can be triggered by calling the runtime """
        base_fact = ".this.is.a.test"
        query = ".this.is?"
        self.runtime(base_fact)
        self.assertTrue(self.runtime(query))
        
        
    def test_simple_fact_retraction(self):
        """ Check facts can be retracted """
        assert_fact = ".retraction.test.this.is.a.test"
        retract_fact = "~.retraction.test.this.is"
        query = ".retraction.test.this.is.a.test?"
        self.runtime(assert_fact)
        self.assertTrue(self.runtime(query))
        self.runtime(retract_fact)
        self.assertFalse(self.runtime(query))
        
    def test_negated_query(self):
        """ Check queries can test for negatives """  
        base_fact = ".this.is.a.test"
        query = "~.this.is.a.test?"
        self.assertTrue(self.runtime(query))
        self.runtime(base_fact)
        self.assertFalse(self.runtime(query))
        
    def test_exclusion_semantics(self):
        """ Check the exclusion will override """
        self.runtime(".this.is.a.test")
        self.runtime(".this.is.a.blah")
        self.assertTrue(self.runtime(".this.is.a.test?\n.this.is.a.blah?"))
        self.runtime(".this.is.a!bloo")
        result = self.runtime("~.this.is.a.test?\n~.this.is.a.blah?\n.this.is.a!bloo?")
        print('Exclusion semantic result: {}'.format(result))
        self.assertTrue(result)

    def test_exclusion_query_resolution(self):
        """ Test that an queries respect exclusion operators """
        self.runtime(".this.is.a!test")
        self.assertFalse(self.runtime(".this.is.a.test?"))
        result = self.runtime(".this.is.a!test?")
        print('Exclusion query result: {}'.format(result))
        self.assertTrue(result)
              


    def test_rule_definition(self):
        """ Check that rules can be asserted """
        self.runtime(".this.is.a.test.rule.{ [] -> [] }")
        self.assertTrue(self.runtime(".this.is.a.test.rule?"))
        self.assertTrue(".this.is.a.test.rule" in self.runtime.rules)

    def test_getting_variables(self):
        """ Check that querying can retrieve potential bindings """
        self.runtime(".this.is.a.test\n.this.is.a.second")
        parsed = ELPARSE(".this.is.a.$x?")[0]
        results = self.runtime.fact_query(parsed)[0]
        self.assertEqual(len(results),1)
        self.assertTrue(results[0])
        self.assertIsInstance(results[0],ELBD.ELSuccess)
        self.assertEqual(len(results[0]),2)
        bindings = [x[1] for x in results[0].bindings]
        self.assertIn({'x': 'test'}, bindings)
        self.assertIn({'x': 'second'}, bindings)

        
    def test_getting_chained_variables(self):
        """ Check that multiple variables in a string are retrieved correctly """
        self.runtime(".this.is.a.first.test\n.this.is.a.second.blahh")
        parsed = ELPARSE(".this.is.a.$x.$y?")[0]
        results = self.runtime.fact_query(parsed, self.runtime.top_stack())[0]
        self.assertTrue(results)
        self.assertEqual(len(results[0]),2)
        bindings = [x[1] for x in results[0].bindings]
        self.assertIn({'x':'first','y':'test'}, bindings)
        self.assertIn({'x':'second','y':'blahh'}, bindings)
                    

    def test_rule_firing(self):
        self.runtime(".this.is.a.first.fact")
        self.runtime(".this.is.a.rule.{ .this.is.a.first? -> .this.is.a.second.fact }")
        parsed = ELPARSE(".this.is.a.rule")[0]
        parse_hash = str(parsed)
        the_rule = self.runtime.get_rule(parse_hash)
        self.assertFalse(self.runtime('.this.is.a.second.fact?'))
        self.runtime.run_rule(the_rule)
        self.assertTrue(self.runtime('.this.is.a.second.fact?'))
        self.assertFalse(self.runtime('.this.is.a.different.fact?'))
        self.assertTrue(self.runtime('~.this.is.a.different.fact?'))

    def test_rule_binding(self):
        self.runtime('.this.is.a.first.fact')
        self.runtime('.this.is.a.rule.{ .this.is.a.first.$x? -> .this.is.a.second.$x }')
        parsed = ELPARSE('.this.is.a.rule')[0]
        parse_hash = str(parsed)
        the_rule = self.runtime.get_rule(parse_hash)
        self.assertFalse(self.runtime('.this.is.a.second.fact?'))
        self.runtime.run_rule(the_rule)
        self.assertTrue(self.runtime('.this.is.a.second.fact?'))

    def test_rule_multi_binding(self):
        self.runtime('.this.is.a.first.fact')
        self.runtime('.this.rule.{ .this.is.a.$x.$y? -> .this.is.a.$y.$x }')
        parsed = ELPARSE('.this.rule')[0]
        parse_hash = str(parsed)
        the_rule = self.runtime.get_rule(parse_hash)
        self.assertFalse(self.runtime('.this.is.a.fact.first?'))
        self.runtime.run_rule(the_rule)
        self.assertTrue(self.runtime('.this.is.a.fact.first?'))

    def test_rule_multi_binding_across_conditions(self):
        self.runtime('.this.is.an.afact.a')
        self.runtime('.this.is.a.bfact.b')
        self.runtime('.this.is.a.rule.{ .this.is.an.afact.$x?, .this.is.a.bfact.$y? -> .the.combination.is.$x.$y }')
        parsed = ELPARSE('.this.is.a.rule')[0]
        parse_hash = str(parsed)
        the_rule = self.runtime.get_rule(parse_hash)
        self.assertFalse(self.runtime('.the.combination.is.a.b?'))
        self.runtime.run_rule(the_rule)
        self.assertTrue(self.runtime('.the.combination.is.a.b?'))
        
    def test_rule_multi_action(self):
        self.runtime('.this.is.an.afact.a')
        self.runtime('.this.is.a.rule.{ .this.is.an.afact? -> .response.first, .response.second }')
        parsed = ELPARSE('.this.is.a.rule')[0]
        parse_hash = str(parsed)
        the_rule = self.runtime.get_rule(parse_hash)
        self.assertFalse(self.runtime('.response.first?'))
        self.assertFalse(self.runtime('.response.second?'))
        self.runtime.run_rule(the_rule)
        self.assertTrue(self.runtime('.response.first?'))
        self.assertTrue(self.runtime('.response.second?'))
        
    def test_rule_multi_action_binding(self):
        self.runtime('.this.is.an.afact.a')
        self.runtime('.this.is.a.rule.{ .this.is.an.afact.$x? -> .response.first.$x, .response.second.$x }')
        parsed = ELPARSE('.this.is.a.rule')[0]
        parse_hash = str(parsed)
        the_rule = self.runtime.get_rule(parse_hash)
        self.assertFalse(self.runtime('.response.first.a?'))
        self.assertFalse(self.runtime('.response.second.a?'))
        self.runtime.run_rule(the_rule)
        self.assertTrue(self.runtime('.response.first.a?'))
        self.assertTrue(self.runtime('.response.second.a?'))
        
    def test_rule_mutli_binding_multi_action(self):
        self.runtime('.this.is.an.afact.a')
        self.runtime('.this.is.a.bfact.b')
        self.runtime('.this.is.a.rule.{ .this.is.an.afact.$x?, .this.is.a.bfact.$y? -> .response.first.$x, .response.second.$y }')
        parsed = ELPARSE('.this.is.a.rule')[0]
        parse_hash = str(parsed)
        the_rule = self.runtime.get_rule(parse_hash)
        self.assertFalse(self.runtime('.response.first.a?'))
        self.assertFalse(self.runtime('.response.second.b?'))
        self.runtime.run_rule(the_rule)
        self.assertTrue(self.runtime('.response.first.a?'))
        self.assertTrue(self.runtime('.response.second.b?'))
        
    def test_rule_binding_union(self):
        """  Ensure that .$x matches across all conditions """
        self.runtime('.first.x.blah')
        self.runtime('.second.x.bloo')
        self.runtime('.second.y.awef')
        self.runtime('.this.is.a.rule.{ .first.$x.$y?, .second.$x.$z? -> .third.$x.$y.$z }')
        parsed = ELPARSE('.this.is.a.rule')[0]
        parse_hash = str(parsed)
        the_rule = self.runtime.get_rule(parse_hash)
        self.assertFalse(self.runtime('.third.x.blah.bloo?'))
        self.runtime.run_rule(the_rule)
        self.assertTrue(self.runtime('.third.x.blah.bloo?'))

    def test_rule_exclusion(self):
        self.runtime('.first!x')
        self.runtime('.this.is.a.rule.{ .first!$x? -> .first!y, .second!$x }')
        parsed = ELPARSE('.this.is.a.rule')[0]
        parse_hash = str(parsed)
        the_rule = self.runtime.get_rule(parse_hash)
        self.assertFalse(all(self.runtime('.first!y?\n.second!x?')))
        result = self.runtime('~.first!y?\n~.second!x?')
        print('result: {}'.format(result))
        self.assertTrue(all(result))
        self.runtime.run_rule(the_rule)
        self.assertTrue(all(self.runtime('.first!y?\n.second!x?')))
                        
    def test_rule_exclusion_2(self):
        self.runtime('.first!x\n.second!x')
        self.runtime('.this.is.a.rule.{ .first!$x?, .second!$x? -> .third!$x } ')
        parsed = ELPARSE('.this.is.a.rule')[0]
        parse_hash = str(parsed)
        the_rule = self.runtime.get_rule(parse_hash)
        self.assertTrue(all(self.runtime('~.third!x?')))
        self.runtime.run_rule(the_rule)
        self.assertTrue(self.runtime('.third!x?'))

    def test_rule_value(self):
        self.runtime('.this.is.a.value.1d5')
        self.runtime('.this.is.a.rule.{ .this.is.a.value.$x? -> .result.$x }')
        parsed = ELPARSE('.this.is.a.rule')[0]
        parse_hash = str(parsed)
        the_rule = self.runtime.get_rule(parse_hash)
        self.assertFalse(self.runtime('.result.1d5?'))
        self.runtime.run_rule(the_rule)
        self.assertTrue(self.runtime('.result.1d5?'))
        
    def test_rule_less_comparison(self):
        self.runtime('.first.20')
        self.runtime('.second.40')
        self.runtime('.this.is.a.rule.{ .first.$x?, .second.$y? | $x < $y -> .third }')
        parsed = ELPARSE('.this.is.a.rule')[0]
        parse_hash = str(parsed)
        the_rule = self.runtime.get_rule(parse_hash)
        self.assertFalse(self.runtime('.third?'))
        self.runtime.run_rule(the_rule)
        self.assertTrue(self.runtime('.third?'))

    def test_rule_greater_comparison(self):
        self.runtime('.first.20')
        self.runtime('.second.40')
        self.runtime('.this.is.a.rule.{ .first.$x?, .second.$y? | $y > $x -> .third }')
        parsed = ELPARSE('.this.is.a.rule')[0]
        parse_hash = str(parsed)
        the_rule = self.runtime.get_rule(parse_hash)
        self.assertFalse(self.runtime('.third?'))
        self.runtime.run_rule(the_rule)
        self.assertTrue(self.runtime('.third?'))

    def test_rule_lessequal_comparison(self):
        self.runtime('.first.40')
        self.runtime('.second.40')
        self.runtime('.this.is.a.rule.{ .first.$x?, .second.$y? | $x <= $y -> .third }')
        parsed = ELPARSE('.this.is.a.rule')[0]
        parse_hash = str(parsed)
        the_rule = self.runtime.get_rule(parse_hash)
        self.assertFalse(self.runtime('.third?'))
        self.runtime.run_rule(the_rule)
        self.assertTrue(self.runtime('.third?'))

    def test_rule_greaterequal_comparison(self):
        self.runtime('.first.40')
        self.runtime('.second.40')
        self.runtime('.this.is.a.rule.{ .first.$x?, .second.$y? | $y >= $x -> .third }')
        parsed = ELPARSE('.this.is.a.rule')[0]
        parse_hash = str(parsed)
        the_rule = self.runtime.get_rule(parse_hash)
        self.assertFalse(self.runtime('.third?'))
        self.runtime.run_rule(the_rule)
        self.assertTrue(self.runtime('.third?'))

    def test_rule_equal_comparison(self):
        self.runtime('.first.40')
        self.runtime('.second.40')
        self.runtime('.this.is.a.rule.{ .first.$x?, .second.$y? | $x == $y -> .third }')
        parsed = ELPARSE('.this.is.a.rule')[0]
        parse_hash = str(parsed)
        the_rule = self.runtime.get_rule(parse_hash)
        self.assertFalse(self.runtime('.third?'))
        self.runtime.run_rule(the_rule)
        self.assertTrue(self.runtime('.third?'))

    def test_rule_less_comparison(self):
        self.runtime('.first.20')
        self.runtime('.second.40')
        self.runtime('.this.is.a.rule.{ .first.$x?, .second.$y? | $x != $y -> .third }')
        parsed = ELPARSE('.this.is.a.rule')[0]
        parse_hash = str(parsed)
        the_rule = self.runtime.get_rule(parse_hash)
        self.assertFalse(self.runtime('.third?'))
        self.runtime.run_rule(the_rule)
        self.assertTrue(self.runtime('.third?'))

    def test_rule_contains_comparison(self):
        self.runtime('.first.[1,2,3,4]')
        self.runtime('.second.2')
        self.runtime('.this.is.a.rule.{ .first.$x?, .second.$y? | $y @ $x -> .third }')
        parsed = ELPARSE('.this.is.a.rule')[0]
        parse_hash = str(parsed)
        the_rule = self.runtime.get_rule(parse_hash)
        self.assertFalse(self.runtime('.third?'))
        self.runtime.run_rule(the_rule)
        self.assertTrue(self.runtime('.third?'))

    def test_rule_not_contains_comparison(self):
        self.runtime('.first.[1,2,3,4]')
        self.runtime('.second.5')
        self.runtime('.this.is.a.rule.{ .first.$x?, .second.$y? | $y !@ $x -> .third }')
        parsed = ELPARSE('.this.is.a.rule')[0]
        parse_hash = str(parsed)
        the_rule = self.runtime.get_rule(parse_hash)
        self.assertFalse(self.runtime('.third?'))
        self.runtime.run_rule(the_rule)
        self.assertTrue(self.runtime('.third?'))
        
    def test_rule_contains_letter_comparison(self):
        self.runtime('.first.[a, b, c, d]')
        self.runtime('.second.a')
        self.runtime('.this.is.a.rule.{ .first.$x?, .second.$y? | $y !@ $x -> .third }')
        parsed = ELPARSE('.this.is.a.rule')[0]
        parse_hash = str(parsed)
        the_rule = self.runtime.get_rule(parse_hash)
        self.assertFalse(self.runtime('.third?'))
        self.runtime.run_rule(the_rule)
        self.assertTrue(self.runtime('~.third?'))

    def test_rule_near_comparison(self):
        self.runtime('.first.30')
        self.runtime('.second.35')
        self.runtime('.this.is.a.rule.{ .first.$x?, .second.$y? | $x ~=(10) $y -> .third }')
        parsed = ELPARSE('.this.is.a.rule')[0]
        parse_hash = str(parsed)
        the_rule = self.runtime.get_rule(parse_hash)
        self.assertFalse(self.runtime('.third?'))
        self.runtime.run_rule(the_rule)
        self.assertTrue(self.runtime('.third?'))
        
    def test_rule_less_comparison_using_var(self):
        self.runtime('.first.20')
        self.runtime('.second.30')
        self.runtime('.nearVal.10')
        self.runtime('.this.is.a.rule.{ .first.$x?, .second.$y?, .nearVal.$z? | $x ~=($z) $y -> .third }')
        parsed = ELPARSE('.this.is.a.rule')[0]
        parse_hash = str(parsed)
        the_rule = self.runtime.get_rule(parse_hash)
        self.assertFalse(self.runtime('.third?'))
        self.runtime.run_rule(the_rule)
        self.assertTrue(self.runtime('.third?'))

        
        
        
        
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
