"""
	BASIC testing of the ELParser
"""
import unittest
import logging as root_logger
import IPython
from random import random
from test_context import ielpy
from ielpy import ELParser
from ielpy import ELExceptions as ELE
from ielpy.ELFunctions import ELCOMP, ELARITH
from ielpy.ELActions import ELBIND
from ielpy.ELStructure import ELVAR, ELQUERY
from ielpy.ELFactStructure import ELFACT, ELComparison
from ielpy.ELUtil import ELVARSCOPE, EL, ELARR
from fractions import Fraction


logging = root_logger.getLogger(__name__)
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
        self.assertIsInstance(result,ELFACT)

    def test_n_facts(self):
        """ check that n facts are parsed together """
        n_facts = gen_n()
        fact_string = ".this.is.a.test"
        all_facts = "\n".join([fact_string for x in range(n_facts)])
        results = self.parser(all_facts)
        self.assertEqual(len(results),n_facts)

    def test_results_are_ELFACTS(self):
        """ check that the returned type is a ELFACT """
        fact_string = ".this.is.a.test\n.this.is.another.test"
        results = self.parser(fact_string)
        self.assertIsInstance(results[0], ELFACT)
        self.assertIsInstance(results[1], ELFACT)

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
        self.assertEqual(results[0].data[-1],[1,2,3,4,5])

    def test_empty_array(self):
        """ check that an array can be empty """
        test_fact = ".this.is.an.empty.array.[]"
        results = self.parser(test_fact)
        #length is 7, num of '.' + terminal
        self.assertEqual(len(results[0].data), 7)
        self.assertEqual(results[0][-1], [])
        
    def test_multi_line_array(self):
        """ check that an array can be on multiple lines """
        test_fact = """.this.is.a.multiline.array.[
        1,
        2,
        3
        ]"""
        results = self.parser(test_fact)
        self.assertEqual(len(results[0].data),7)
        #Checking LENGTH:
        self.assertEqual(len(results[0].data[-1]),3)
        #Checking CONTENT:
        self.assertEqual(results[0].data[-1],[1,2,3])

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
        self.assertEqual(results[0].data[3].elop, EL.EX)

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
        self.assertEqual(results[0].data[-1],[1,2,3])

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

    def test_fact_negation(self):
        """ ~.a.fact.should.be.negatable """
        test_fact = "~.a.fact.should.be.negatable """
        results = self.parser(test_fact)
        self.assertEqual(results[0][-1].value,"negatable")
        self.assertTrue(results[0].negated)

    def test_fact_not_negated(self):
        """ .a.normal.fact.shouldnt.be.negated """
        test_fact = ".a.normal.fact.shouldnt.be.negated """
        results = self.parser(test_fact)
        self.assertFalse(results[0].negated)
            
    def test_simple_comparison_lookup(self):
        test_comp = ">"
        results = ELParser.COMP.parseString(test_comp)
        self.assertEqual(results[0][0], ELCOMP.GREATER)
        self.assertIsNone(results[0][1])

    def test_simple_arith_lookup(self):
        test_arith = '+'
        results = ELParser.ARITH.parseString(test_arith)
        self.assertEqual(results[0], ELARITH.PLUS)
        
    def test_only_actions_can_have_arith_ops(self):
        """ The fact .a.b.c + 20 should fail """
        test_fact = ".a.b.c + 20"
        logging.debug("A Warning should be logged for .a.b.c + 20")  
        with self.assertRaises(ELE.ELParseException):
            self.parser(test_fact)
        logging.debug("The warning should have been logged")

            
    def test_global_binding(self):
        """ test just the bind statement  """
        test_fact = "$x <- .person.bob"
        result = self.parser(test_fact)
        root_fact = self.parser('.person.bob')[0]
        self.assertIsInstance(result[0], ELBIND)
        self.assertEqual(result[0].var.value,'x')
        self.assertEqual(result[0].root,root_fact)

    def test_global_unbinding(self):
        """ test an empty bind statement """
        test_fact = "$x <- "
        result = self.parser(test_fact)
        self.assertIsInstance(result[0], ELBIND)
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
        self.assertIsInstance(results[0], ELBIND)
        self.assertEqual(results[0].var.value,'x')
        self.assertEqual(results[0].root,bob)
        #check bill binding:
        self.assertIsInstance(results[1], ELBIND)
        self.assertEqual(results[1].var.value,'x')
        self.assertEqual(results[1].root,bill)

    def test_statement_array(self):
        """ test a sequence of facts """
        test_fact = ".a.b.list.[.a.b.c, .a.b.c, .a.b.d]"
        result = self.parser(test_fact)
        self.assertEqual(len(result[0][-1]),3)
        for entry in result[0][-1]:
            self.assertIsInstance(entry, ELFACT)

    def test_condition_separately(self):
        """ Parsing a query on its own should work """
        test_query = ".a.b.c?"
        result = self.parser(test_query)[0]
        self.assertIsInstance(result, ELFACT)
        self.assertIsInstance(result[-1], ELQUERY)

    def test_path_var_scoping_exis(self):
        test_var = "$..x"
        result = ELParser.VAR.parseString(test_var)[0]
        self.assertIsInstance(result, ELVAR)
        self.assertEqual(result.value, 'x')
        self.assertEqual(result.scope, ELVARSCOPE.EXIS)
        self.assertIsNone(result.array_point)
        self.assertTrue(result.is_path_var)

    def test_path_var_scoping_forall(self):
        test_var = "@..x"
        result = ELParser.VAR.parseString(test_var)[0]
        self.assertIsInstance(result, ELVAR)
        self.assertEqual(result.value, 'x')
        self.assertEqual(result.scope, ELVARSCOPE.FORALL)
        self.assertIsNone(result.array_point)
        self.assertTrue(result.is_path_var)

    def test_non_path_var_scoping_exis(self):
        test_var = "$x"
        result = ELParser.VAR.parseString(test_var)[0]
        self.assertIsInstance(result, ELVAR)
        self.assertEqual(result.value, 'x')
        self.assertEqual(result.scope, ELVARSCOPE.EXIS)
        self.assertIsNone(result.array_point)
        self.assertFalse(result.is_path_var)
        
    def test_non_path_var_scoping_forall(self):
        test_var = "@x"
        result = ELParser.VAR.parseString(test_var)[0]
        self.assertIsInstance(result, ELVAR)
        self.assertEqual(result.value, 'x')
        self.assertEqual(result.scope, ELVARSCOPE.FORALL)
        self.assertIsNone(result.array_point)
        self.assertFalse(result.is_path_var)
    
    def test_non_path_array_define(self):
        test_var = "$x(4)"
        result = ELParser.VAR.parseString(test_var)[0]
        self.assertIsInstance(result, ELVAR)
        self.assertEqual(result.value, 'x')
        self.assertEqual(result.scope, ELVARSCOPE.EXIS)
        self.assertEqual(result.array_point,4)
        self.assertEqual(result.array_type, ELARR.DEFINE)
        self.assertFalse(result.is_path_var)

    def test_non_path_array_access(self):
        test_var = "$x[4]"
        result = ELParser.VAR.parseString(test_var)[0]
        self.assertIsInstance(result, ELVAR)
        self.assertEqual(result.value, 'x')
        self.assertEqual(result.scope, ELVARSCOPE.EXIS)
        self.assertEqual(result.array_point,4)
        self.assertEqual(result.array_type, ELARR.ACCESS)
        self.assertFalse(result.is_path_var)

        
    def test_non_path_array_define_from_var(self):
        test_var = "$x($y)"
        result = ELParser.VAR.parseString(test_var)[0]
        self.assertIsInstance(result, ELVAR)
        self.assertEqual(result.value, 'x')
        self.assertEqual(result.scope, ELVARSCOPE.EXIS)
        self.assertEqual(result.array_type, ELARR.DEFINE)
        self.assertIsInstance(result.array_point, ELVAR)
        self.assertEqual(result.array_point.value, 'y')
        self.assertFalse(result.is_path_var)

    def test_non_path_array_access_from_var(self):
        test_var = "$x[$y]"
        result = ELParser.VAR.parseString(test_var)[0]
        self.assertIsInstance(result, ELVAR)
        self.assertEqual(result.value, 'x')
        self.assertEqual(result.scope, ELVARSCOPE.EXIS)
        self.assertEqual(result.array_type, ELARR.ACCESS)
        self.assertIsInstance(result.array_point, ELVAR)
        self.assertEqual(result.array_point.value, 'y')
        self.assertFalse(result.is_path_var)
        
        
    def test_comparison_array(self):
        test_string = ".this.is.a.test.[ $x < $y, $y == $z ]"
        result = self.parser(test_string)[0]
        self.assertIsInstance(result, ELFACT)
        self.assertIsInstance(result[-1], list)
        self.assertTrue(all([isinstance(x, ELComparison) for x in result[-1]]))
        
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
    LOG_FILE_NAME = "test_ELParser.log"
    root_logger.basicConfig(filename=LOG_FILE_NAME, level=LOGLEVEL, filemode='w')
    console = root_logger.StreamHandler()
    console.setLevel(root_logger.INFO)
    root_logger.getLogger('').addHandler(console)
    #root_logger.disable(root_logger.CRITICAL)
    ##############################

    unittest.main()
