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
from fractions import Fraction

#Parser returns a ParseResult, which is an array of actual parse data structures

gen_n = lambda: 2 + int(random()*20)

class ELParser_Tests(unittest.TestCase):

    def setUp(self):
        self.parser = ELParser.ELPARSE
    def tearDown(self):
        self.parser = None
 
    def test_simple(self):
        """ Check the parser works in a minimal case """
        result = self.parser('.this.is.a.test')[0]
        self.assertIsInstance(result,ELBD.ELFACT)

    def test_n_facts(self):
        """ check that n facts are parsed together """
        n_facts = gen_n()
        fact_string = ".this.is.a.test"
        all_facts = "\n".join([fact_string for x in range(n_facts)])
        results = self.parser(all_facts)
        self.assertEqual(len(results),n_facts)

    def test_results_are_ELFACTS(self):
        """ check that the returned type is a ELBD.ELFACT """
        fact_string = ".this.is.a.test\n.this.is.another.test"
        results = self.parser(fact_string)
        self.assertIsInstance(results[0],ELBD.ELFACT)
        self.assertIsInstance(results[1],ELBD.ELFACT)

    def test_results_contain_data(self):
        """ check that a parsed result contains the correct amount of data in its data field """
        fact_length = gen_n()
        test_fact = ".test".join(["" for x in range(fact_length)])
        results = self.parser(test_fact)
        #-1 because you're comparing to the *connections* not the actual elements in the empty array
        self.assertEqual(len(results[0].data),fact_length)

    def test_results_contain_array(self):
        """ check that the parsed result correctly gets an array in a fact """
        test_fact = ".this.is.an.array.[1,2,3,4,5]"
        results = self.parser(test_fact)
        self.assertEqual(len(results[0].data),6)
        self.assertIsInstance(results[0].data[-1],ELBD.ELTERM)
        self.assertEqual(results[0].data[-1].value,[1,2,3,4,5])

    def test_empty_array(self):
        """ check that an array can be empty """
        test_fact = ".this.is.an.empty.array.[]"
        results = self.parser(test_fact)
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
        results = self.parser(test_fact)
        self.assertEqual(len(results[0].data),7)
        self.assertIsInstance(results[0].data[-1],ELBD.ELTERM)
        #Checking LENGTH:
        self.assertEqual(len(results[0].data[-1].value),3)
        #Checking CONTENT:
        self.assertEqual(results[0].data[-1].value,[1,2,3])

    def test_fact_with_string_inside(self):
        """ check facts can have strings inside them """
        test_fact = '.this.is.a."string fact"'
        results = self.parser(test_fact)
        self.assertEqual(results[0].data[-1].value,'string fact')

    def test_fact_with_string_sub_values(self):
        """ check that a string fact can continue having sub values """
        test_fact = '.this.is."a test".with.subvalues'
        results = self.parser(test_fact)
        self.assertEqual(len(results[0].data),6)

    def test_fact_with_exclusion_operator(self):
        """ Check the ! exclusion operator works in facts """
        test_fact = ".this.is.an!exclusive.fact"
        results = self.parser(test_fact)
        self.assertEqual(len(results[0].data),6)
        self.assertEqual(results[0].data[3].elop,ELBD.EL.EX)

    def test_fact_with_string_including_ex_op(self):
        """ check that an ! in a string doesn't interfere """
        test_fact = '.this.is."a !test"'
        results = self.parser(test_fact)
        self.assertEqual(len(results[0].data),4)
        self.assertEqual(results[0].data[-1].value,'a !test')

    def test_fact_with_number(self):
        """ check that facts can include numbers """
        test_fact = '.a.b.5'
        results = self.parser(test_fact)
        self.assertEqual(results[0].data[-1].value,5)

    def test_fact_with_negative_number(self):
        """ check that numbers in facts can be negative """
        test_fact = '.a.b.-5'
        results = self.parser(test_fact)
        self.assertEqual(results[0].data[-1].value,-5)

    def test_fact_with_underscore_number(self):
        """ check that numbers can be formatted to be read """
        test_fact = '.a.b.5_000_000'
        results = self.parser(test_fact)
        self.assertEqual(results[0].data[-1].value,5000000)

    def test_fact_with_number_array(self):
        """ check that numbers can be in arrays """
        test_fact ='.a.b.[1,2,3]'
        results = self.parser(test_fact)
        self.assertEqual(results[0].data[-1].value,[1,2,3])

    def test_fact_with_underscore_negative_number(self):
        """ check that formatted numbers can be negative """
        test_fact = ".a.b.-12_000_000"
        results = self.parser(test_fact)
        self.assertEqual(results[0].data[-1].value,-12000000)

    def test_facts_can_be_fractions(self):
        """ check that numbers in facts can be fractions """
        test_fact = ".a.b.1/5"
        results = self.parser(test_fact)
        self.assertIsInstance(results[0].data[-1].value,Fraction)

    def test_facts_can_be_decimals(self):
        """ check that numbers can be decimals """
        test_fact = ".a.b.1d5"
        results = self.parser(test_fact)
        self.assertEqual(results[0].data[-1].value,1.5)

    def test_numbers_can_have_sub_facts(self):
        """ make sure numbers dont have to be leaves """
        test_fact = ".a.b.5.c"
        results = self.parser(test_fact)
        self.assertEqual(len(results[0].data),5)
        self.assertEqual(results[0].data[-1].value,'c')

    def test_comments_are_ignored(self):
        """ make sure comments are ignored """
        test_fact = ".a.b.c\n#blahhhhh\n.c.d.e"
        results = self.parser(test_fact)
        self.assertEqual(len(results),2)

    ####################

    def test_empty_rule(self):
        """ test .this.is.a.rule.{[] -> []} """
        test_fact = ".this.is.a.rule.{[]->[]} """
        results = self.parser(test_fact)
        self.assertEqual(len(results),1)
        self.assertIsInstance(results[0],ELBD.ELFACT)
        self.assertEqual(len(results[0]),5)
        self.assertIsInstance(results[0][-1],ELBD.ELTERM)
        self.assertIsInstance(results[0][-1].value,ELBD.ELRULE)
        self.assertEqual(len(results[0][-1].value.conditions),0)
        self.assertEqual(len(results[0][-1].value.actions),0)
        
                
    
    def test_rule_definition(self):
        """ Test .this.is.a.rule.{[.blah?, .bloo?, .blee?] -> [.wee.bloo.blah]} """
        test_fact = ".this.is.a.rule.{[.a?, .b?, .c?] -> [.d, .e, .f]}"
        conditions = ".a\n.b\n.c"
        actions = ".d\n.e\n.f"
        results = self.parser(test_fact)
        conditions_parsed = self.parser(conditions)
        actions_parsed = self.parser(actions)
        for x,y in zip(results[0][-1].value.conditions,conditions_parsed):
            self.assertIsInstance(x,ELBD.ELQUERY)
            self.assertEqual(x.value,y)
        for x,y in zip(results[0][-1].value.actions,actions_parsed):
            self.assertIsInstance(x,ELBD.ELFACT)
            self.assertEqual(x,y)

    def test_rule_multiline(self):
        """ As above, but across multiple lines """
        test_fact = """ .this.is.a.rule.{
        [.a?, .b?, .c?]
        ->
        [.d, .e, .f]
        }
        """
        results = self.parser(test_fact)
        self.assertIsInstance(results[0][-1].value,ELBD.ELRULE)
        for x in results[0][-1].value.conditions:
            self.assertIsInstance(x,ELBD.ELQUERY)
        for x in results[0][-1].value.actions:
            self.assertIsInstance(x,ELBD.ELFACT)
            
        
    def test_rule_multiconditions(self):
        """ Test .this.is.a.rule{[.blah.bloo?, .blee.blah?] -> [.wee.bloo, .wee.blah]} """
        test_fact = ".this.is.a.rule.{[.blah.bloo?, .blee.blah?] -> [.wee.bloo, .wee.blah]}"
        results = self.parser(test_fact)
        self.assertIsInstance(results[0][-1].value,ELBD.ELRULE)
        for x in results[0][-1].value.conditions:
            self.assertIsInstance(x,ELBD.ELQUERY)
        for x in results[0][-1].value.actions:
            self.assertIsInstance(x,ELBD.ELFACT)
        

    def test_rule_multiconditions_multiline(self):
        """ As above, but across multiple lines """
        test_fact = """.this.is.a.rule.{
    		[.blah.bloo?, .blee.blah?] 
        	-> 
		[.wee.bloo, .wee.blah]}"""
        results = self.parser(test_fact)
        self.assertIsInstance(results[0][-1].value,ELBD.ELRULE)
        for x in results[0][-1].value.conditions:
            self.assertIsInstance(x,ELBD.ELQUERY)
        for x in results[0][-1].value.actions:
            self.assertIsInstance(x,ELBD.ELFACT)
        

    def test_rule_bindings(self):
        """ Test .this.is.a.rule.{[.blah.bloo.$1?] -> [.bloo.blee.$1]} """
        test_fact = ".this.is.a.rule.{[.blah.bloo.$1?] -> [.bloo.blee.$1]}"
        results = self.parser(test_fact)
        self.assertIsInstance(results[0][-1].value.conditions[0].value[-1].value, ELBD.ELVAR)
        self.assertIsInstance(results[0][-1].value.actions[0][-1].value,ELBD.ELVAR)

    def test_bindings_are_registered(self):
        """ bindings need to be registered with their parent fact, and that facts parent rule """
        test_fact = ".this.is.a.$binding"
        results = self.parser(test_fact)
        self.assertEqual(len(results[0].bindings),1)
        self.assertEqual(results[0].bindings[0].value,"binding")

    def test_bindings_are_registered_when_non_terminal(self):
        """ bindings should be registered even when they aren't at the end of a fact """
        test_fact = ".this.is.a.$binding.blah"
        results = self.parser(test_fact)
        self.assertEqual(len(results[0].bindings),1)
        self.assertEqual(results[0].bindings[0].value,"binding")

    def test_bindings_complain_when_unbalanced(self):
        """ undefined bindings in actions should complain """
        test_fact = ".this.is.a.rule.{[.blah.bloo?] -> [.blah.bloo.$blee]}"
        with self.assertRaises(ELE.ELConsistencyException):
            self.parser(test_fact)

    def test_fact_negation(self):
        """ ~.a.fact.should.be.negatable """
        test_fact = "~.a.fact.should.be.negatable """
        results = self.parser(test_fact)
        self.assertIsInstance(results[0][-1],ELBD.ELTERM)
        self.assertEqual(results[0][-1].value,"negatable")
        self.assertTrue(results[0].negated)

    def test_fact_not_negated(self):
        """ .a.normal.fact.shouldnt.be.negated """
        test_fact = ".a.normal.fact.shouldnt.be.negated """
        results = self.parser(test_fact)
        self.assertFalse(results[0].negated)
            
    def test_rule_negation_testing(self):
        """ Test .this.is.a.rule.{[~.blah.bloo.blee?] -> [.blah.bloo.blee]} """
        test_fact = ".this.is.a.rule.{[~.blah.bloo.blee?] -> [.blah.bloo.blee]}"
        results = self.parser(test_fact)
        self.assertTrue(results[0][-1].value.conditions[0].value.negated)
        self.assertFalse(results[0][-1].value.actions[0].negated)

    def test_rule_action_negation(self):
        """ test .this.is.a.rule.{[] -> [~.blah.bloo.blee]} """
        test_fact = ".this.is.a.rule.{[] -> [~.blah.bloo.blee]}"
        results = self.parser(test_fact)
        self.assertTrue(results[0][-1].value.actions[0].negated)

    def test_rule_condition_comparison(self):
        """ .this.is.a.rule.{[.a.b.$c?, .a.b.$d?] | [$c > $d ] -> [] } """
        test_fact = ".this.is.a.rule.{[.a.b.$c?, .a.b.$d?] | [$c > $d] -> [] } "
        results = self.parser(test_fact)
        self.assertEqual(len(results[0][-1].value.binding_comparisons),1)
        self.assertEqual(results[0][-1].value.binding_comparisons[0].b1.value,'c')
        self.assertEqual(results[0][-1].value.binding_comparisons[0].b2.value,'d')
        self.assertEqual(results[0][-1].value.binding_comparisons[0].op,ELBD.ELCOMP.GREATER)

    def test_simple_comparison_lookup(self):
        test_comp = ">"
        results = ELParser.COMP.parseString(test_comp)
        self.assertEqual(results[0][0],ELBD.ELCOMP.GREATER)
        self.assertIsNone(results[0][1])

    def test_simple_arith_lookup(self):
        test_arith = '+'
        results = ELParser.ARITH.parseString(test_arith)
        self.assertEqual(results[0],ELBD.ELARITH.PLUS)
        
    def test_rule_arith_action(self):
        """ test .this.is.a.rule.{[] -> [.a.b.c + 20 ]} """
        test_fact = ".this.is.a.rule.{[] -> [.a.b.c + 20]} """
        results = self.parser(test_fact)
        self.assertIsInstance(results[0][-1].value.actions[0],ELBD.ELARITH_FACT)
       
    def test_only_actions_can_have_arith_ops(self):
        """ The fact .a.b.c + 20 should fail """
        test_fact = ".a.b.c + 20"
        with self.assertRaises(ELE.ELParseException):
            self.parser(test_fact)

    def test_rule_brackets_as_optional(self):
        """ .this.is.a.rule.{ .a.b.$c?, .d.e.$f? | $c < $f -> .a.b.e } """
        test_fact = ".this.is.a.rule.{ .a.b.$c?, .d.e.$f? | $c < $f -> .a.b.e }"
        results = self.parser(test_fact)
        self.assertIsInstance(results[0][-1].value,ELBD.ELRULE)
        self.assertEqual(len(results[0][-1].value.binding_comparisons),1)
        self.assertEqual(len(results[0][-1].value.condition_bindings),2)
            
    def test_rule_arith_action_expanded(self):
        """ test .this.is.a.rule.{[] -> [.a.b.c+2/3, .a.b.d-1d4, .a.b.c*5/6, .a.b.c / 2]} """
        test_fact = ".this.is.a.rule.{[] -> .a.b.c+2/3, .a.b.d-1d4, .a.b.c*5/6, .a.b.c/2}"
        results = self.parser(test_fact)
        self.assertEqual(len(results[0][-1].value.actions),4)
        for action in results[0][-1].value.actions:
            self.assertIsInstance(action,ELBD.ELARITH_FACT)

    def test_arith_action_using_var_not_fact(self):
        """ .this.is.a.rule.{ .a.b.$c? -> $c + 2 } """
        test_fact = ".this.is.a.rule.{ .a.b.$c? -> $c + 2 }"
        result = self.parser(test_fact)
        self.assertIn('c',result[0][-1].value.condition_bindings)
        self.assertIn('c',result[0][-1].value.action_bindings)
            

    def test_rule_modulo_action(self):
        """ test .this.is.a.rule.{ [] -> [.a.b.c % 2]} """
        test_fact = ".this.is.a.rule.{ [] -> .a.b.c % 5 }"
        result = self.parser(test_fact)
        self.assertIsInstance(result[0][-1].value.actions[0],ELBD.ELARITH_FACT)

    def test_rule_implicit_binding_comparison(self):
        """ test .this.is.a.rule.{[.a.b.c.$1?, .a.b.d.$1] -> []} """
        test_fact = ".this.is.a.rule.{.a.b.c.$1?, .a.b.d.$1? -> [] } """
        result = self.parser(test_fact)
        self.assertIn('1',result[0][-1].value.condition_bindings)
                
    def test_rule_binding_comparison_non_equality(self):
        """" test .this.is.a.rule.{[.a.b.c.$1?, .a.b.d.$2?] | [$1 != $2] -> []} """
        test_fact = ".this.is.a.rule.{.a.b.c.$1?, .a.b.d.$2? | $1 != $2 -> [] }"
        result = self.parser(test_fact)
        self.assertEqual(result[0][-1].value.binding_comparisons[0].op,ELBD.ELCOMP.NOTEQUAL)

    def test_rule_binding_comparisons(self):
        """ test .this.is.a.rule.{[.a.b.c.$1?,.a.b.d.$2?] | [$1 < $2] -> []} """
        test_fact = """.this.is.a.rule.{ .a.b.c.$1?, .a.b.d.$2? | 
        $1 > $2, $1 < $2, $1 >= $2, $1 <= $2, $1 == $2, $1 != $2, $1 @ $2, $1 !@ $2 -> []}"""
        result = self.parser(test_fact)
        comparisons = result[0][-1].value.binding_comparisons
        #pair with the enums apart from the 'near' enum
        paired = zip(comparisons,list(ELBD.ELCOMP)[:-1])
        for comp,enumValue in paired:
            self.assertEqual(comp.op,enumValue)

    def test_near_operator(self):
        """ The near operator ~=(num) """
        test_fact = ".this.is.a.rule.{.a.b.$1.$2? | $1 ~=(2) $2 -> [] }"
        result = self.parser(test_fact)
        self.assertIsInstance(result[0][-1].value.binding_comparisons[0],ELBD.ELComparison)
        self.assertEqual(result[0][-1].value.binding_comparisons[0].op,ELBD.ELCOMP.NEAR)
        self.assertEqual(result[0][-1].value.binding_comparisons[0].nearVal,2)
            
    def test_global_binding(self):
        """ test just the bind statement  """
        test_fact = "$x <- .person.bob"
        result = self.parser(test_fact)
        root_fact = self.parser('.person.bob')[0]
        self.assertIsInstance(result[0],ELBD.ELBIND)
        self.assertEqual(result[0].var.value,'x')
        self.assertEqual(result[0].root,root_fact)

    def test_global_unbinding(self):
        """ test an empty bind statement """
        test_fact = "$x <- "
        result = self.parser(test_fact)
        self.assertIsInstance(result[0],ELBD.ELBIND)
        self.assertEqual(result[0].var.value,'x')
        self.assertIsNone(result[0].root)


    def test_global_rebinding(self):
        """ test sequence of bindings """
        test_fact = """$x <- .person.bob\n$x <- .person.bill"""
        results = self.parser(test_fact)
        bob = self.parser('.person.bob')[0]
        bill = self.parser('.person.bill')[0]
        self.assertEqual(len(results),2)
        #check bob binding:
        self.assertIsInstance(results[0],ELBD.ELBIND)
        self.assertEqual(results[0].var.value,'x')
        self.assertEqual(results[0].root,bob)
        #check bill binding:
        self.assertIsInstance(results[1],ELBD.ELBIND)
        self.assertEqual(results[1].var.value,'x')
        self.assertEqual(results[1].root,bill)

    def test_statement_array(self):
        """ test a sequence of facts """
        test_fact = ".a.b.list.[.a.b.c, .a.b.c, .a.b.d]"
        result = self.parser(test_fact)
        self.assertEqual(len(result[0][-1].value),3)
        for entry in result[0][-1].value:
            self.assertIsInstance(entry,ELBD.ELFACT)

    def test_rules_cant_have_sub_facts(self):
        """ Rules must be terminals """
        test_fact = ".a.b.rule.{ [] -> [] }.d"
        with self.assertRaises(ELE.ELParseException):
            self.parser(test_fact)

    def test_condition_separately(self):
        """ Parsing a query on its own should work """
        test_query = ".a.b.c?"
        result = self.parser(test_query)[0]
        self.assertIsInstance(result,ELBD.ELQUERY)

    def test_path_var_scoping_exis(self):
        test_var = "$..x"
        result = ELParser.PATH_VAR.parseString(test_var)[0]
        self.assertIsInstance(result, ELBD.ELVAR)
        self.assertEqual(result.value, 'x')
        self.assertEqual(result.scope, ELBD.ELVARSCOPE.EXIS)
        self.assertIsNone(result.access_point)
        self.assertTrue(result.is_path_var)

    def test_path_var_scoping_forall(self):
        test_var = "@..x"
        result = ELParser.PATH_VAR.parseString(test_var)[0]
        self.assertIsInstance(result, ELBD.ELVAR)
        self.assertEqual(result.value, 'x')
        self.assertEqual(result.scope, ELBD.ELVARSCOPE.FORALL)
        self.assertIsNone(result.access_point)
        self.assertTrue(result.is_path_var)

    def test_non_path_var_scoping_exis(self):
        test_var = "$x"
        result = ELParser.NON_PATH_VAR.parseString(test_var)[0]
        self.assertIsInstance(result, ELBD.ELVAR)
        self.assertEqual(result.value, 'x')
        self.assertEqual(result.scope, ELBD.ELVARSCOPE.EXIS)
        self.assertIsNone(result.access_point)
        self.assertFalse(result.is_path_var)
        
    def test_non_path_var_scoping_forall(self):
        test_var = "@x"
        result = ELParser.NON_PATH_VAR.parseString(test_var)[0]
        self.assertIsInstance(result, ELBD.ELVAR)
        self.assertEqual(result.value, 'x')
        self.assertEqual(result.scope, ELBD.ELVARSCOPE.FORALL)
        self.assertIsNone(result.access_point)
        self.assertFalse(result.is_path_var)
    
    def test_non_path_array_access(self):
        test_var = "$x(4)"
        result = ELParser.NON_PATH_VAR.parseString(test_var)[0]
        self.assertIsInstance(result, ELBD.ELVAR)
        self.assertEqual(result.value, 'x')
        self.assertEqual(result.scope, ELBD.ELVARSCOPE.EXIS)
        self.assertEqual(result.access_point,4)
        self.assertFalse(result.is_path_var)

    def test_non_path_array_access_from_var(self):
        test_var = "$x($y)"
        result = ELParser.NON_PATH_VAR.parseString(test_var)[0]
        self.assertIsInstance(result, ELBD.ELVAR)
        self.assertEqual(result.value, 'x')
        self.assertEqual(result.scope, ELBD.ELVARSCOPE.EXIS)
        self.assertIsInstance(result.access_point, ELBD.ELVAR)
        self.assertEqual(result.access_point.value, 'y')
        self.assertFalse(result.is_path_var)

        

        
            
    def test_condition_variables(self):
        """ test:
        .this.is.a.condition.set.{.a.b.c?, .b.d.e?, .e.f.$1?}
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
