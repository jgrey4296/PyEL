"""
The Node Structure used in ELTrie
"""
import uuid
from .ELUtil import EL, ELOP2STR
from .ELStructure import ELPAIR, ELVAR
from .ELFactStructure import ELFACT
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
        self.uuid = uuid.uuid1()
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
        if isinstance(key, ELTrieNode):
            del self.children[key.value]
        elif isinstance(key, ELPAIR):
            del self.children[key.value]
        else:
            del self.children[key]


    def __getitem__(self, key):
        if isinstance(key, ELTrieNode):
            return self.children[key.value]
        elif isinstance(key, ELPAIR):
            return self.children[key.value]
        else:
            return self.children[key]

    def __setitem__(self, key, value):
        assert isinstance(value, ELTrieNode)
        #an exclusion removes all else
        if self.elop == EL.EX:
            self.children.clear()
        #now process the key val pair:
        if isinstance(key, ELTrieNode) and isinstance(value, ELTrieNode): 
            self.children[key.value] = value
            value.parent = self
        else:
            raise ELE.ELConsistencyException('Setting a TrieNode requires passing in a trie node')

    def update_elop(self,elop):
        if self.elop is not elop:
            self.children.clear()
            self.elop = elop
            
    def __contains__(self, key):
        logging.debug("TrieNode __contains__: {}".format(key))
        if isinstance(key, ELTrieNode):
            return key.value in self.children
        if isinstance(key, ELPAIR):
            if isinstance(key.value, ELVAR):
                raise Exception('checking trie for a var doesnt make sense')
            #check the key is right, and the elop is right
            logging.debug("TrieNode: {}".format(key.value in self.children))
            logging.debug("{}".format(list(self.children.keys())))
            return key.value in self.children
        else:
            return key in self.children

    def values(self):
        return self.children.values()

    def is_empty(self):
        return len(self.children) == 0

    def __iter__(self):
        return iter(self.children.values())
    
    def to_el_facts(self):
        #Return leaves of this node as an array of ELStructure's
        queue = [(x,[]) for x in self]
        leaves = []
        while len(queue) > 0:
            current, path = queue.pop(0)
            new_path = path + [ELPAIR(current.value, current.elop)]
            if len(current) > 0:
                queue.extend([(x, new_path) for x in current])
            else:
                leaves.append(ELFACT(new_path, r=True))

        return leaves

    def to_weighted_el_facts(self):
        return []
    
    def struct_equal(self, other):
        a = set([x for x in self.children.keys()])
        b = set([x for x in other.children.keys()])
        return a.issuperset(b)
    