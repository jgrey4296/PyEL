"""
	BASIC testing of the ELParser
"""
import unittest
import logging as root_logger
import IPython
from random import random
from test_context import ielpy
from ielpy import ELPARSE
from ielpy import ELExceptions as ELE
from ielpy import ELRuntime as ELR
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
            self.assertTrue(self.runtime(fact + "?"))

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
        self.assertTrue(all(result))

    def test_exclusion_query_resolution(self):
        """ Test that an queries respect exclusion operators """

        self.runtime(".this.is.a!test")
        self.assertFalse(self.runtime(".this.is.a.test?"))
        result = self.runtime(".this.is.a!test?")
        self.assertTrue(result)


    def test_getting_variables(self):
        """ Check that querying can retrieve potential bindings """
        self.runtime(".this.is.a.test\n.this.is.a.second")
        parsed = ELPARSE(".this.is.a.$x?")[0]
        results = self.runtime.fact_query(parsed)
        self.assertEqual(len(results.bindings),2)
        self.assertTrue(results)
        bindings = results.bindings
        test_in_bindings = bindings[0]['x'].value == 'test' or bindings[1]['x'].value == 'test'
        second_in_bindings = bindings[0]['x'].value == 'second' or bindings[1]['x'].value == 'second'
        self.assertTrue(test_in_bindings)
        self.assertTrue(second_in_bindings)

        
    def test_getting_chained_variables(self):
        """ Check that multiple variables in a string are retrieved correctly """
        self.runtime(".this.is.a.first.test\n.this.is.a.second.blahh")
        parsed = ELPARSE(".this.is.a.$x.$y?")[0]
        results = self.runtime.fact_query(parsed, self.runtime.top_stack())
        self.assertTrue(results)
        self.assertEqual(len(results[1]),2)
        bindings = results.bindings
        self.assertIn('x',bindings[0])
        self.assertIn('y',bindings[0])
        self.assertIn('x',bindings[1])
        self.assertIn('y',bindings[1])

        one_binding_x_is_first = bindings[0]['x'].value == 'first' or bindings[1]['x'].value == 'first'
        one_binding_y_is_test = bindings[0]['y'].value == 'test' or bindings[1]['y'].value == 'test'
        one_binding_x_is_second = bindings[0]['x'].value == 'second' or bindings[1]['x'].value == 'second'
        one_binding_y_is_blah = bindings[0]['y'].value == 'blahh' or bindings[1]['y'].value == 'blahh'
        self.assertTrue(one_binding_x_is_first)
        self.assertTrue(one_binding_y_is_test)
        self.assertTrue(one_binding_x_is_second)
        self.assertTrue(one_binding_y_is_blah)

    def test_comma_separated_facts(self):
        """
        .a.b.c, .a.b.d, .a.b.e
        .a.b.c?, .a.b.d?, .a.b.e?
        """
        self.runtime('.a.b.c, .a.b.d, .a.b.e')
        self.assertTrue(self.runtime('.a.b.c?'))
        self.assertTrue(self.runtime('.a.b.d?'))
        self.assertTrue(self.runtime('.a.b.e?'))
        self.assertTrue(all(self.runtime('.a.b.c?, .a.b.d?, .a.b.e?')))
        #Just checking the call is passing automatically, make sure it *can* fail:
        self.assertFalse(all(self.runtime('.a.b.c?, .a.b.d?, .a.b.f?')))
        
    def test_comments_are_ignored(self):
        """
        #.this.is.a.bad.fact
        .a.b.c
        ~.this.is.a.bad.fact?
        """
        self.runtime('#.this.is.a.bad.fact\n.a.b.c')
        self.assertFalse(self.runtime('.this.is.a.bad.fact?'))
        self.assertTrue(self.runtime('.a.b.c?'))

    def test_comments_ignore_rest_of_line(self):
        self.runtime('.this.is.a.test#.but.not.this.far')
        self.assertTrue(self.runtime('.this.is.a.test?'))
        self.assertFalse(self.runtime('.this.is.a.test.but.not.this.far?'))
        self.assertFalse(self.runtime('.but.not.this.far?'))


    def test_condition_running(self):
        """
        .a.b.c, .d.e.f
        .conditions.[ .a.b.c?, .d.e.f? ] => True
        """
        self.runtime('.a.b.c, .d.e.f')
        self.assertTrue(all(self.runtime('.a.b.c?, .d.e.f?')))
        self.runtime('.conditions.[ .a.b.c?, .d.e.f? ]')
        self.assertTrue(self.runtime.run_conditions('.conditions?'))

    def test_condition_binding(self):
        """
        .a.b.blah
        .conditions.[ .a.b.$x? ] => (True, {x: blah })
        """
        self.runtime('.a.b.blah')
        self.runtime('.conditions.[ .a.b.$x? ]')
        result = self.runtime.run_conditions('.conditions?')
        self.assertTrue(result)
        self.assertEqual(len(result.bindings), 1)
        self.assertIn('x', result.bindings[0])
        self.assertEqual('blah', result.bindings[0]['x'].value)
        

    def test_condition_sequence_binding(self):
        """
        .a.b.blah, .a.d.blah,
        .conditions.[ .a.b.$x?, .a.d.$x? ] => (True, {x: blah})
        """
        self.runtime('.a.b.blah, .a.d.blah')
        self.runtime('.conditions.[ .a.b.$x?, .a.d.$x? ]')
        result = self.runtime.run_conditions('.conditions?')
        self.assertTrue(result)
        self.assertEqual(len(result.bindings),1)
        self.assertIn('x', result.bindings[0])
        self.assertEqual('blah', result.bindings[0]['x'].value)

    def test_conditions_with_prior_bindings(self):
        """
        .a.b.blah, .a.d.blah
        bindings <- .a.b.$x?
        .conditions.[ .a.d.$x? ]
        bindings -> .conditions? => True
        """
        self.runtime('.a.b.blah, .a.d.blah')
        self.runtime('.conditions.[ .a.d.$x? ]')
        bindings = self.runtime('.a.b.$x?').bindings
        result = self.runtime.run_conditions('.conditions?', bindings=bindings)
        self.assertTrue(result)

        
    def test_condition_binding_comparison(self):
        """
        .a.b.10, .a.d.20,
        .test.conditions.[ .a.b.$x?, .a.d.$y? ] => (True, {x : 10, y: 20 })
        .test.comparisons.[ $x < $y ] => True
        """
        self.runtime('.a.b.10, .a.d.20')
        self.runtime('.test.conditions.[.a.b.$x?, .a.d.$y? ]')
        self.runtime('.test.comparisons.[ $x < $y ]')
        result = self.runtime.run_conditions('.test.conditions?')
        self.assertTrue(result)
        self.assertIn('x', result.bindings[0])
        self.assertIn('y', result.bindings[0])
        passing_bindings = self.runtime.run_comparisons('.test.comparisons?', result.bindings)
        self.assertEqual(len(passing_bindings), 1)

    def test_condition_binding_filtering(self):
        """
        .a.b.10, .a.b.40, .a.d.20,
        .test.conditions.[ .a.b.$x?, .a.d.$y? ],
        .test.comparisons.[ $x < $y ] 
        """
        self.runtime('.a.b.10, .a.b.40, .a.b.18, .a.d.20')
        self.runtime('.test.conditions.[ .a.b.$x?, .a.d.$y? ]')
        self.runtime('.test.comparisons.[ $x < $y ]')
        result = self.runtime.run_conditions('.test.conditions?')
        self.assertTrue(result)
        self.assertEqual(len(result), 3)
        passing_bindings = self.runtime.run_comparisons('.test.comparisons?', result.bindings)
        self.assertEqual(len(passing_bindings), 2)

        
    def test_arith_action(self):
        """
        .a.b.10,
        .test.conditions.[ .a.b.$x ],
        .test.arithmetic.[ $..x + 10 ],
        .a.b.20? => True
        """
        self.runtime('.a.b.10')
        self.runtime('.test.conditions.[ .a.b.$x ]')
        self.runtime('.test.arithmetic.[ $..x + 10 ]')
        result = self.runtime.run_conditions('.test.conditions?')
        self.assertTrue(result)
        self.assertEqual(len(result), 1)
        self.assertFalse(self.runtime('.a.b.20?'))
        result.bindings.select()
        self.runtime.run_arithmetic('.test.arithmetic?', bindings=result.bindings)
        self.assertTrue(self.runtime('.a.b.20?'))

    def test_arith_in_place(self):
        """
        .a.b.10
        .test.conditions.[ .a.b.$x? ]
        .test.arithmetic.[ $x * 10 ]
        .a.b.10?
        """
        self.runtime('.a.b.10, .test.[ .conditions.[ .a.b.$x? ], .arithmetic.[ $x * 10 ] ]')
        result = self.runtime.run_conditions('.test.conditions?')
        result.bindings.select()
        self.assertTrue(result)
        self.assertEqual(len(result), 1)
        self.assertTrue(self.runtime('.a.b.10?'))
        self.runtime.run_arithmetic('.test.arithmetic?', bindings=result.bindings)
        self.assertTrue(self.runtime('.a.b.10?'))
        
    def test_arith_chain(self):
        """
        .a.b.10, .a.c.5,
        .test.conditions.[ .a.b.$x?, .a.c.$y? ],
        .test.arithmetic.[ $y + 5, $..x + $y ]
        .a.b.20?
        .a.c.5?        
        """
        self.runtime('.a.b.10, .a.c.5')
        self.runtime('.test.conditions.[ .a.b.$x?, .a.c.$y? ]')
        self.runtime('.test.arithmetic.[ $y + 5, $..x + $y ]')
        result = self.runtime.run_conditions('.test.conditions?')
        result.bindings.select()
        self.assertTrue(result)
        self.assertEqual(len(result), 1)
        self.assertFalse(self.runtime('.a.b.20?'))
        self.assertTrue(self.runtime('.a.c.5?'))
        self.runtime.run_arithmetic('.test.arithmetic?', bindings=result.bindings)
        self.assertTrue(self.runtime('.a.b.20?'))
        self.assertTrue(self.runtime('.a.c.5?'))

        
    def test_action(self):
        """
        .a.b.blah
        .test.conditions.[ .a.b.$x? ] => (True, {x: blah})
        .test.actions.[ $..x.bloo ]
        .a.b.blah.bloo? => True
        """
        self.runtime('.a.b.blah')
        self.runtime('.test.conditions.[ .a.b.$x? ]')
        self.runtime('.test.actions.[ $..x.bloo ]')
        self.assertFalse(self.runtime('.a.b.blah.bloo?'))
        result = self.runtime.run_conditions('.test.conditions?')
        self.assertTrue(result)
        self.runtime.run_actions('.test.actions?', bindings=result.bindings)
        self.assertTrue(self.runtime('.a.b.blah.bloo?'))

    def test_condition_arith_action(self):
        """
        .a.b.10, .a.c.20
        .test.conditions.[ .a.b.$x?, .a.c.$y ],
        .test.arithmetic.[ $x + $y ],
        .test.actions.[ .a.d.$x ]
        """
        self.runtime('.a.b.10, .a.c.20, .test.[ .conditions.[ .a.b.$x?, .a.c.$y? ] ]')
        self.runtime('.test.[ .arithmetic.[ $x + $y ], .actions.[ .a.d.$x ] ]')
        self.assertFalse(self.runtime('.a.d.30?'))
        result = self.runtime.run_conditions('.test.conditions?')
        result.bindings.select()
        binding = self.runtime.run_arithmetic('.test.arithmetic?', result.bindings)
        self.runtime.run_actions('.test.actions?', binding)
        self.assertTrue(self.runtime('.a.d.30?'))

    def test_node_output(self):
        """
        .a.b.[ .output."Test output" ]
        """
        self.runtime('.a.b.[ .output."Test output" ]')
        output = self.runtime.run_output('.a.b.output?')
        self.assertEqual(output, "Test output")

    def test_node_output_from_options(self):
        """
        .a.b.[ .output.[ "First Test", "Second Test", "Third Test" ]]
        """
        self.runtime('.a.b.[ .output.[ "First Test", "Second Test", "Third Test" ]]')
        output = self.runtime.run_output('.a.b.output?')
        self.assertIn(output,["First Test", "Second Test", "Third Test"])
        
    def test_trie_next_following(self):
        """
        .first.[ .next.[ .second, .third ], .output."blah" ],
        .second.[ .next.[ .fourth ], .output."bloo" ],
        .third.[ .next.[ .fourth ], .output."awef" ],
        .forth.[ .next.[], .output."finished" ]
        """
        self.runtime('.first.[ .next.[ .second, .third ], .output."blah"]')
        self.runtime('.second.[ .next.fourth, .output."bloo" ]')
        self.runtime('.third.[ .next.fourth, .output."awef" ]')
        self.runtime('.fourth.output.finished')
        next_node = self.runtime.next_node('.first.next?')
        second = self.runtime('.second?').nodes[0]
        third = self.runtime('.third?').nodes[0]
        fourth = self.runtime('.fourth?').nodes[0]
        self.assertIn(next_node.uuid, [second, third])
        final = self.runtime.next_node(next_node['next'])
        self.assertEqual(final.uuid, fourth)


    def test_binding_less_actions(self):
        """
        .a.b.c,
        .actions.[ ~.a.b.c, .a.b.d ]
        ~.a.b.c?
        .a.b.d?
        """
        self.runtime('.a.b.c')
        self.runtime('.actions.[ ~.a.b.c, .a.b.d ]')
        self.assertFalse(self.runtime('.a.b.d?'))
        self.assertFalse(self.runtime('~.a.b.c?'))
        self.runtime.run_actions('.actions?')
        self.assertTrue(self.runtime('~.a.b.c?, .a.b.d?'))
        
    def test_string_interpolation(self):
        """
        .name.first.Henry
        .name.second.Thornwood
        .conditions.[ .name.first.$x?, .name.second.$y? ],
        .actions.[ .output."His name was $x Maurice $y" ]
        .output."His name was Henry Maurice Thornwood"?
        """
        self.runtime('.name.first.Henry, .name.second.Thornwood')
        self.runtime('.node.conditions.[ .name.first.$x?, .name.second.$y?]')
        self.runtime('.node.output.[ "His name was {x} Maurice {y}"]')
        result = self.runtime.run_conditions('.node.conditions?')
        result.bindings.select()
        output = self.runtime.run_output('.node.output?', result.bindings)
        self.assertEqual(output, "His name was Henry Maurice Thornwood")

    def test_trie_execution_in_total(self):
        """
        .first.[ .actions.[ .name.Henry.ThornWood ], .output."Start", .next.second ]
        .second.[ .conditions.[ .name.$x ], .output."{x} said hello", .next.third ]
        .third.[ .conditions.[ .name.$x.$y ], .output."Hello Mr {y}"]
        """
        self.runtime('.first.[ .actions.[ .name.Henry.Thornwood ], .output."Start", .next.second ]')
        self.runtime('.second.[ .conditions.[ .name.$x ], .output."{x} said hello", .next.third ]')
        self.runtime('.third.[ .conditions.[ .name.$x.$y ], .output."Hello Mr {y}"]')
        #pass in trie num value
        output = self.runtime.execute('.first')
        #test the output:
        self.assertEqual(len(output), 3)
        self.assertEqual(output[0], 'Start')
        self.assertEqual(output[1], 'Henry said hello')
        self.assertEqual(output[2], 'Hello Mr Thornwood')

    def test_trie_execution_in_total_2(self):
        #todo: (n).name.$x.$y? -> select n of the possibilities
        self.runtime(""" .people.henry.thornwoord, .people.agatha.griseldom,
        .first.[ .conditions.[ .people.$x.$y? ], .output."Hello {x}", .next.second],
        .second.[ .output."Testing {x}" ]
        """)
        output = self.runtime.execute('.first')
        self.assertEqual(len(output), 2)
        self.assertIn(output[0], ['Hello henry', 'Hello agatha'])
        self.assertIn(output[1], ['Testing henry', 'Testing agatha'])

    def test_trie_execution_options(self):
        self.runtime(""" .first.[ .actions.[ .name.henry.thornwood ], .next.second ], 
        .second.[ .conditions.[ .name.$x.$y? ], .actions.[ .people.$x.$y, ~.name ], .output.[ "Blah {x}", "Bloo {y}" ], .next.[ .third, .fourth ]],
        .third.[ .output."Final {x}" ],
        .fourth.[ .output."Final {y}" ]
        """)
        output = self.runtime.execute('.first')
        #TODO

    def test_forall_simple(self):
        """
        .a.b.c, .a.b.d, .a.b.e,
        .node.conditions.[ .a.b.$x? ]
        .node.actions.[ .test.@x ]
        .test.c?,
        .test.d?,
        .test.e?
        """
        self.runtime('.a.b.[ c, d, e]');
        self.runtime('.node.conditions.[ .a.b.$x? ]')
        results = self.runtime.run_conditions('.node.conditions')
        results.bindings.select()
        self.runtime('.node.actions.[ .test.@x ]')
        self.runtime.run_actions('.node.actions', bindings=results.bindings)
        self.assertTrue(all(self.runtime('.test.c?, .test.d?, .test.e?')))
        
    def test_forall_binding_arithmetic(self):
        """
        .a.b.10, .a.c.20, .a.d.2,
        .test.conditions.[ .a.$x.$y? ] ],
        .test.arithmetic.[ @..y + 5 ],
        .a.b.15?
        .a.c.25?
        .a.d.7?
        """
        self.runtime('.a.b.10, .a.c.20, .a.d.2')
        self.runtime('.test.conditions.[ .a.$x.$y? ]')
        self.runtime('.test.arithmetic.[ @..y + 5 ]')
        result = self.runtime.run_conditions('.test.conditions?')
        self.assertTrue(result)
        self.assertEqual(len(result), 3)
        self.assertFalse(any(self.runtime('.a.b.15?, .a.c.25?, .a.d.7?')))
        self.runtime.run_arithmetic('.test.arithmetic?', result.bindings)
        self.assertTrue(all(self.runtime('.a.b.15?, .a.c.25?, .a.d.7?')))

    def test_forall_binding_arithmetic_chained_to_actions(self):
        self.runtime('.a.b.10, .a.c.20, .a.d.2')
        self.runtime('.test.conditions.[ .a.$x.$y?]')
        self.runtime('.test.arithmetic.[ @y + 5]')
        self.runtime('.test.actions.[ .output.@x.@y ]')
        result = self.runtime.run_conditions('.test.conditions?')
        self.assertTrue(result)
        updated_bindings = self.runtime.run_arithmetic('.test.arithmetic?', result.bindings)
        self.runtime.run_actions('.test.actions?', updated_bindings)

        #check the originals werent modified:
        self.assertTrue(all(self.runtime('.a.b.10?, .a.c.20?, .a.d.2?')))
        #check the new assertions were:
        self.assertTrue(all(self.runtime('.output.b.15?, .output.c.25?, .output.d.7?')))

    def test_binding_purity(self):
        self.runtime('.a.b.10, .a.c.20, .a.d.2')
        self.runtime('.test.conditions.[ .a.$x.$y?]')
        self.runtime('.test.arithmetic.[ @y + 5]')
        self.runtime('.test.actions.[ .output.@x.@y ]')
        result = self.runtime.run_conditions('.test.conditions?')
        self.assertTrue(result)
        updated_bindings = self.runtime.run_arithmetic('.test.arithmetic?', result.bindings)
        self.runtime.run_actions('.test.actions?', result.bindings)
        self.assertTrue(all(self.runtime('.a.b.10?, .a.c.20?, .a.d.2?')))
        self.assertTrue(all(self.runtime('.output.b.10?, .output.c.20?, .output.d.2?')))


    def test_forall_and_selected_binding(self):
        self.runtime('.a.b.10, .a.c.20, .a.d.2')
        self.runtime('.test.conditions.[ .a.$x.$y?]')
        self.runtime('.test.arithmetic.[ @y + 5]')
        self.runtime('.test.actions.[ .output.$x, .outputs.@x.@y]')
        result = self.runtime.run_conditions('.test.conditions?')
        result.bindings.select(0)
        updated_bindings = self.runtime.run_arithmetic('.test.arithmetic?', result.bindings)
        self.runtime.run_actions('.test.actions?', updated_bindings)
        self.assertTrue(all(self.runtime('.a.b.10?, .a.c.20?, .a.d.2?')))
        self.assertTrue(all(self.runtime('.outputs.b.15?, .outputs.c.25?, .outputs.d.7?')))
        self.assertTrue(self.runtime('.output.b?'))

    def test_binding_selection(self):
        """
        .a.b, .a.c, .a.d, .a.e,
        .test.conditions.[ .a.$x? ],
        .test.comparisons.[ $x == c ],
        .test.actions.[ .output.$x ]
        """
        self.runtime('.a.b, .a.c, .a.d, .a.e')
        self.runtime('.test.conditions.[ .a.$x? ]')
        self.runtime('.test.comparisons.[ $x == c ]')
        self.runtime('.test.actions.[ .output.$x ]')
        result = self.runtime.run_conditions('.test.conditions')
        bindings = self.runtime.run_comparisons('.test.comparisons', result.bindings)
        self.runtime.run_actions('.test.actions', bindings)
        self.assertTrue(self.runtime('.output.c'))

    def test_binding_selection_with_forall_exclusion(self):
        """
        .a.b, .a.c, .a.d, .a.e,
        .test.conditions.[ .a.$x? ],
        .test.comparisons.[ $x == c ],
        .test.actions.[ .output.$x ]
        """
        self.runtime('.a.b, .a.c, .a.d, .a.e')
        self.runtime('.test.conditions.[ .a.$x? ]')
        self.runtime('.test.comparisons.[ $x == c ]')
        self.runtime('.test.actions.[ .output.$x, .other.@!x ]')
        result = self.runtime.run_conditions('.test.conditions')
        bindings = self.runtime.run_comparisons('.test.comparisons', result.bindings)
        self.runtime.run_actions('.test.actions', bindings)
        self.assertTrue(self.runtime('.output.c?'))
        self.assertTrue(all(self.runtime('.other.b?, .other.d?, .other.e?')))
        self.assertTrue(self.runtime('~.other.c?'))
        self.assertTrue(all(self.runtime('~.output.b?, ~.output.d?, ~.output.e?')))
    

        
    #todo: test forall binding actions
    #todo: string interpolation, selection based on a variable,
    #todo: weighting based on a variable
    
    def test_trie_weighted_next_following(self):
        """
        .first.[ .next.[ .0d6.second, .0d4.third ], .output."blah" ],
        .second.[ .output."bloo" ],
        .third.[ .output."blee" ]
        """
        None

    
    def test_global_binding(self):
        """
        $x <- .a.b.c
        $..x.d
        .a.b.c.d?
        """
        None

    def test_global_rebinding(self):
        """
        $x <- .a.b.c
        $x <- .q.e
        $..x.d
        ~.a.b.c.d?
        .q.e.d?
        """
        None

    
        
        
if __name__ == "__main__":
    LOGLEVEL = root_logger.DEBUG
    LOG_FILE_NAME = "test_ELRuntime.log"
    root_logger.basicConfig(filename=LOG_FILE_NAME, level=LOGLEVEL, filemode='w')
    console = root_logger.StreamHandler()
    console.setLevel(root_logger.DEBUG)
    root_logger.getLogger('').addHandler(console)
    logging = root_logger.getLogger(__name__)
    root_logger.disable(root_logger.CRITICAL)
    ##############################
    unittest.main()
