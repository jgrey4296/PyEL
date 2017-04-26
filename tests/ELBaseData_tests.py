"""
	BASIC testing of the ELParser
"""
import unittest
import logging as root_logger
import IPython
from random import random
from test_context import ielpy
from ielpy.ELStructure import ELPAIR, ELVAR
from ielpy.ELFactStructure import ELFACT
from ielpy.ELBinding import ELBindingSlice, ELBindingEntry
from ielpy.ELTrieNode import ELTrieNode
from ielpy import ELParser
from ielpy import ELExceptions as ELE
from fractions import Fraction

#Parser returns a ParseResult, which is an array of actual parse data structures

gen_n = lambda: 2 + int(random()*20)

class ELBaseData_Tests(unittest.TestCase):

    def test_Fact_binding(self):
        testFact = ELFACT(r=True).var('b').var('c').var('d')
        bindingDict = ELBindingSlice(
            {'b': ELBindingEntry('b',None,'blah'),
             'c': ELBindingEntry('c', None, 'crickey'),
             'd': ELBindingEntry('d', None, 'dimwit') })
        bound = testFact.bind_slice(bindingDict)
        self.assertEqual(str(testFact), '.$b.$c.$d.')
        self.assertEqual(repr(testFact), '| ROOT.VAR($b).VAR($c).VAR($d). |')
        self.assertNotEqual(repr(testFact), repr(bound))
        self.assertEqual(str(bound), '.blah.crickey.dimwit.')
        self.assertEqual(repr(bound), "| ROOT.'blah'.'crickey'.'dimwit'. |")

    def test_fact_expansion(self):
        testFact = ELFACT(r=True).pair('blah').pair('bloo').var('blee')
        subfact_1 = ELFACT(r=True).pair('awef').pair('awefgg').pair('awee')
        subfact_2 = ELFACT(r=True).pair('poi').epair('iuy').pair('oyb')
        testFact.insert([subfact_1, subfact_2])

        expanded = testFact.expand()
        self.assertEqual(len(expanded),2)
        self.assertEqual(str(expanded[0]), ".blah.bloo.$blee.awef.awefgg.awee.")
        self.assertEqual(str(expanded[1]), ".blah.bloo.$blee.poi.iuy!oyb.")

    def test_fact_array_expansion_ints(self):
        testFact = ELFACT(r=True).pair('blah').pair('bloo').insert([1,2,3,4])
        expanded = testFact.expand()
        self.assertEqual(len(expanded),4)
        
    def test_trie_node_sub_nodes_to_facts(self):
        node = ELTrieNode(ELPAIR('blah'))
        sub_node_1 = ELTrieNode(ELPAIR('bloo'))
        sub_node_2 = ELTrieNode(ELPAIR('awef'))
        sub_node_1a = ELTrieNode(ELPAIR('blarg'))
        sub_node_1b = ELTrieNode(ELPAIR('oiju'))

        node[sub_node_1] = sub_node_1
        node[sub_node_2] = sub_node_2
        sub_node_1[sub_node_1a] = sub_node_1a
        sub_node_1[sub_node_1b] = sub_node_1b
        #Final Trie: blah.[awef, bloo.[blarg, oiju]]
        as_facts = node.to_el_facts()
        self.assertEqual(len(as_facts), 3)
        as_strings = [str(x) for x in as_facts]
        self.assertIn(".awef.", as_strings)
        self.assertIn(".bloo.blarg.", as_strings)
        self.assertIn(".bloo.oiju.", as_strings)
        

    def test_trie_node_sub_nodes_to_facts_with_var(self):
        node = ELTrieNode(ELPAIR('blah'))
        sub_node_1 = ELTrieNode(ELPAIR(ELVAR('bloo')))
        sub_node_2 = ELTrieNode(ELPAIR('awef'))
        sub_node_1a = ELTrieNode(ELPAIR('blarg'))
        sub_node_1b = ELTrieNode(ELPAIR('oiju'))

        node[sub_node_1] = sub_node_1
        node[sub_node_2] = sub_node_2
        sub_node_1[sub_node_1a] = sub_node_1a
        sub_node_1[sub_node_1b] = sub_node_1b
        #Final Trie: blah.[awef, bloo.[blarg, oiju]]
        as_facts = node.to_el_facts()
        self.assertEqual(len(as_facts), 3)
        as_strings = [str(x) for x in as_facts]
        self.assertIn(".awef.", as_strings)
        self.assertIn(".$bloo.blarg.", as_strings)
        self.assertIn(".$bloo.oiju.", as_strings)
        

        
        
    def test_fact_string_str(self):
        None

    def test_fact_string_repr(self):
        None
        
    def test_fact_variable_str(self):
        None

    def test_fact_variable_repr(self):
        None

    def test_rule_str(self):
        None

    def test_rule_repr(self):
        None

    
        
    
        
if __name__ == "__main__":
    LOGLEVEL = root_logger.DEBUG
    LOG_FILE_NAME = "test_ELBaseData.log"
    root_logger.basicConfig(filename=LOG_FILE_NAME, level=LOGLEVEL, filemode='w')
    console = root_logger.StreamHandler()
    console.setLevel(root_logger.INFO)
    root_logger.getLogger('').addHandler(console)
    logging = root_logger.getLogger(__name__)
    root_logger.disable(root_logger.CRITICAL)
    ##############################

    unittest.main()
