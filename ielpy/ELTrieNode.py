"""
The Node Structure used in ELTrie
"""
from uuid import uuid1
from .ELUtil import EL, ELOP2STR, ELVARSCOPE
from .ELStructure import ELPAIR, ELVAR
from .ELFactStructure import ELFACT
from .ELFunctions import get_EL_FUNC
from . import ELExceptions as ELE
import logging as root_logger

logging = root_logger.getLogger(__name__)
#----------------------------------------
##  CORE TRIE NODE
#----------------------------------------
class ELTrieNode:
    """ The internal node used for the Trie.
    Nominally an EL Operator (DOT or EX), and a value, usually a dict
    """

    def __init__(self, val, parent=None):
        self.uuid = uuid1()
        #Default to Dot, update later if necessary
        #Add an int time step stack, and then index elop, value, child edges by it
        #so self.change_time_steps: [0, 4, 6, 7, 8]
        self.elop = EL.DOT
        self.value = None
        self.parent = parent
        self.children = {}
        if isinstance(val, ELPAIR):
            self.elop = val.elop
            self.value = val.value
        else:
            self.value = val

    def update_value(self, value):
        del self.parent[self]
        self.value = value
        self.parent[self] = self

    def child_value(self):
        """ Utility to get the child value of exclusive nodes """
        if self.elop is not EL.EX:
            raise ELE.ELConsistencyException('Trying to get single child of a non-exclusive node')
        return list(self.children.values())[0].value

    def children_values(self):
        """ Utility to get the values of the children of a node """
        return [x.value for x in self.children.values()]

    def simple_string(self):
        val = str(self.value)
        if isinstance(self.value, float):
            val = val.replace('.', 'd')

        if self.parent is None:
            return "{}".format(ELOP2STR(self.elop))
        elif len(self.children) > 0:
            return "{}{}".format(val, ELOP2STR(self.elop))
        else:
            return "{}".format(val)

    def __hash__(self):
        """ Not a true hashing of the object, but good enough to enable
        usage in sets.
        Can't hash the value as that isn't unique"""
        return hash(self.uuid)


    def __repr__(self):
        return "EL_Trie_Node({},{} > {})".format(repr(self.value), \
                                                 repr(self.elop), \
                                                 repr(self.children.keys()))

    def __str__(self):
        """ Get the Str representation, treating this
        node as a leaf. """
        chain = []
        current = self
        while current is not None:
            chain.append(current)
            current = current.parent
        chain.reverse()
        as_strings = [x.simple_string() for x in chain]
        return "".join(as_strings)

    def __len__(self):
        return len(self.children)

    def __eq__(self, other):
        """ Check that EL ops match """
        if isinstance(other, ELPAIR):
            return self.value == other.value
        elif isinstance(other, ELTrieNode):
            return self.elop == other.elop and \
                self.value == other.value and \
                self.children == other.children
        else: #else compare to the internal vaue
            return self.value == other

    def __delitem__(self, key):
        #todo: if deleting an integer, and all children are integers, adjust indices
        if isinstance(key, ELTrieNode):
            del self.children[key.value]
        elif isinstance(key, ELPAIR):
            del self.children[key.value]
        else:
            del self.children[key]


    def __getitem__(self, key):
        logging.info("Getting: {}".format(key))
        if isinstance(key, ELTrieNode):
            return self.children[key.value]
        elif isinstance(key, ELPAIR):
            return self.children[key.value]
        else:
            return self.children[key]

    def __setitem__(self, key, value):
        assert isinstance(value, ELTrieNode)
        logging.info("Setting: {}".format(key))
        #an exclusion removes all else
        if self.elop == EL.EX:
            self.children.clear()
        #now process the key val pair:
        if isinstance(key, ELTrieNode) and isinstance(value, ELTrieNode):
            self.children[key.value] = value
            value.parent = self
        else:
            raise ELE.ELConsistencyException('Setting a TrieNode requires passing in a trie node')

    def update_elop(self, elop):
        if self.elop is not elop:
            self.children.clear()
            self.elop = elop

    def __contains__(self, key):
        result = False
        if isinstance(key, ELTrieNode):
            result = key.value in self.children
        if isinstance(key, ELPAIR):
            #check the key is right, and the elop is right
            logging.debug("TrieNode: {}".format(key.value in self.children))
            logging.debug("{}".format(list(self.children.keys())))
            result = key.value in self.children
        else:
            result = key in self.children
        logging.debug("TrieNode __contains__: {} --- {}".format(result, key))
        return result


    def values(self):
        return self.children.values()

    def is_empty(self):
        return len(self.children) == 0

    def __iter__(self):
        return iter(self.children.values())

    def to_el_facts(self, with_root=True):
        #Return leaves of this node as an array of ELStructure's
        queue = [(x, []) for x in self]
        leaves = []
        while len(queue) > 0:
            current, path = queue.pop(0)
            new_path = path + [ELPAIR(current.value, current.elop)]
            if len(current) > 0:
                queue.extend([(x, new_path) for x in current])
            else:
                leaves.append(ELFACT(new_path, r=with_root))

        return leaves

    def to_el_queries(self):
        leaves = self.to_el_facts()
        queries = [x.query() for x in leaves]
        return queries

    def to_el_function_formatted(self, comp=True):
        """ Format children of the node for use in a function,
        default to expecting comparisons.
        """
        comp_nodes = [x for x in self]
        formatted = []
        for node in comp_nodes:
            operator = get_EL_FUNC(node['operator'].child_value(), comp=comp)
            p1 = node['focus'].child_value()
            p2 = node['value'].child_value()
            if 'near' in node:
                nearVal = node['near'].child_value()
            else:
                nearVal = None
            forall_scoped = any([p1.scope is ELVARSCOPE.FORALL,
                                 (isinstance(p2, ELVAR) and \
                                  p2.scope is ELVARSCOPE.FORALL),
                                 (isinstance(nearVal, ELVAR) and \
                                  nearVal.scope is ELVARSCOPE.FORALL)])
            formatted.append((operator, p1, p2, nearVal, forall_scoped))

        return formatted

    def struct_equal(self, other):
        a = set([x for x in self.children.keys()])
        b = set([x for x in other.children.keys()])
        return a.issuperset(b)
