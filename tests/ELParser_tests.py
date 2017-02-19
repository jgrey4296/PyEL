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

    ####################

    def test_empty_rule(self):
        """ test .this.is.a.rule.{[] -> []} """
        test_fact = ".this.is.a.rule.{[]->[]} """
        results = self.parser.parseString(test_fact)
        self.assertEqual(len(results),1)
        self.assertIsInstance(results[0],ELBD.ELFACT)
        self.assertEqual(len(results[0]),5)
        
    
    def test_rule_defintion(self):
        """ Test .this.is.a.rule.{[.blah.bloo.blee] -> [.wee.bloo.blah]} """
        None

    def test_rule__multiline(self):
        """ As above, but across multiple lines """
        None
        
    def test_rule_multiconditions(self):
        """ Test .this.is.a.rule{[.blah.bloo,.blee.blah] -> [.wee.bloo, .wee.blah]} """
        None


    def test_rule_multiconditions_multiline(self):
        """ As above, but across multiple lines """
        None

    def test_rule_bindings(self):
        """ Test .this.is.a.rule.{[.blah.bloo.$1] -> [.bloo.blee.$1]} """
        None

    def test_rule_name_binding(self):
        """ Test .this.is.a.rule.{[.blah.bloo.$name] -> [.bloo.blee.$name]} """
        None

    def test_rule_negation_testing(self):
        """ Test .this.is.a.rule.{[~.blah.bloo.blee] -> [.blah.bloo.blee]} """
        None

    def test_rule_retraction(self):
        """ Test .this.is.a.rule.{[.blah.bloo.blee] -> [~.blah.bloo.blee]} """
        None

    def test_rule_condition_comparison(self):
        """ test .this.is.a.rule.{[.a.b.c > 20, a.b.c < 50] -> [] } """
        None

    def test_rule_arith_action(self):
        """ test .this.is.a.rule.{[] -> [.a.b.c + 20 ]} """
        None

    def test_rule_arith_action_expanded(self):
        """ test .this.is.a.rule.{[] -> [.a.b.c+2/3, .a.b.d-1d4, .a.b.c*5/6, .a.b.c / 2]} """
        None

    def test_rule_modulo_action(self):
        """ test .this.is.a.rule.{[.a.b.c%5] -> [.a.b.c%2]} """
        None

    def test_rule_binding_comparison(self):
        """ test .this.is.a.rule.{[.a.b.c.$1, .a.b.d.$1] -> []} """
        None

    def test_rule_binding_comparison_non_equality(self):
        """" test .this.is.a.rule.{[.a.b.c.$1, .a.b.d.$2, $1 != $2] -> []} """
        None

    def test_rule_binding_comparison_size(self):
        """ test .this.is.a.rule.{[.a.b.c.$1,.a.b.d.$2, $1 < $2] -> []} """
        None

    def test_closure_binding(self):
        """ test:
        x <- .person.bob
        x.likes.fish        
        """
        None

    def test_closure_unbinding(self):
        """ test:
        x <- .person.bob
        x <- 
        """
        None

    def test_closure_rebinding(self):
        """ test:
        x <- .person.bob
        x <- .person.bill
        """
        None

    def test_statement_array(self):
        """ test .a.b.list.[.a.b.c,.a.b.c,.a.b.d] """
        None

    def test_condition_variables(self):
        """ test:
        .this.is.a.condition.set.{.a.b.c, .b.d.e, .e.f.$1}
        .this.is.an.action.set.{.e.f.g, .h.i.j, .l.m.$1}
        .this.is.a.rule.{ .this.is.a.condition.set -> .this.is.an.action.set }
        """
        None

    def test_subtree_application(self):
        """ test: 
        .a.b.c.d, .a.b.e.f
        .a.g :: .a.b
        """
        None
        
    def test_subtree_test(self):
        """ test:
        .a.b.c.d, .a.b.e.f
        .a.g.c.d, .a.g.e.f
        .a.g ::? .a.b
        """
        None

    def test_subtree_variable_application(self):
        """ test:
        .a.b.c.$1, .a.b.c.$2,
        .a.d :: .a.b(bob,bill)        
        """
        None
        
    
        
if __name__ == "__main__":
    LOGLEVEL = root_logger.DEBUG
    LOG_FILE_NAME = "ELParser_tests.log"
    root_logger.basicConfig(filename=LOG_FILE_NAME, level=LOGLEVEL, filemode='w')
    console = root_logger.StreamHandler()
    console.setLevel(root_logger.INFO)
    root_logger.getLogger('').addHandler(console)
    logging = root_logger.getLogger(__name__)
    root_logger.disable(root_logger.CRITICAL)
    ##############################

    unittest.main()
