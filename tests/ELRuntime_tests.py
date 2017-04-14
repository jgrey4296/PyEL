"""
	BASIC testing of the ELParser
"""
import unittest
import logging as root_logger
import IPython
from random import random
from test_context import ielpy
from ielpy import ELPARSE
from ielpy import ELBaseData as ELBD
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
        self.assertTrue(result)

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
        results = self.runtime.fact_query(parsed)[0]
        self.assertEqual(len(results),2)
        self.assertTrue(results)
        self.assertIsInstance(results,ELBD.ELSuccess)
        bindings = [x for x in results.bindings]
        test_in_bindings = bindings[0]['x'].value == 'test' or bindings[1]['x'].value == 'test'
        second_in_bindings = bindings[0]['x'].value == 'second' or bindings[1]['x'].value == 'second'
        self.assertTrue(test_in_bindings)
        self.assertTrue(second_in_bindings)

        
    def test_getting_chained_variables(self):
        """ Check that multiple variables in a string are retrieved correctly """
        self.runtime(".this.is.a.first.test\n.this.is.a.second.blahh")
        parsed = ELPARSE(".this.is.a.$x.$y?")[0]
        results = self.runtime.fact_query(parsed, self.runtime.top_stack())[0]
        self.assertTrue(results)
        self.assertEqual(len(results[0]),2)
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


    def test_condition_evaluation(self):
        fact_string = """ 
        .a.b.c, .d.e!blah,
        .a.test.[
        	.conditions.[
        		.a.b.c?,
        		.d.e!$f?
		]
        ]
        """
        self.runtime(fact_string)
        













        
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
    LOG_FILE_NAME = "ELRuntime_tests.log"
    root_logger.basicConfig(filename=LOG_FILE_NAME, level=LOGLEVEL, filemode='w')
    console = root_logger.StreamHandler()
    console.setLevel(root_logger.WARNING)
    root_logger.getLogger('').addHandler(console)
    logging = root_logger.getLogger(__name__)
    #root_logger.disable(root_logger.INFO)
    ##############################
    unittest.main()
