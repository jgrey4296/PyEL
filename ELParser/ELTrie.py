"""
A Simple Trie for EL
"""
import logging as root_logger
from ELParser import ELBaseData as ELBD
logging = root_logger.getLogger(__name__)

class ELTrieNode:
    """ The internal node used for the Trie.
    Nominally an EL Operator (DOT or EX), and a value, usually a dict 
    """
    
    def __init__(self,val):
        self.elop = ELBD.EL.DOT
        self.value = None
        self.children = {}
        if isinstance(val,ELBD.ELPAIR):
            self.elop = val.elop
            self.value = val.value
        elif isinstance(val,ELBD.ELTERM):
            self.value = val.value
        else:
            self.value = val

    def is_empty(self):
        return len(self.children) == 0
        
    def elops_match(self,el_op):
        return False


    
class ELTrie:
    """ A Simple Python Trie implementation for EL """
    def __init__(self):
        #The root element of the trie, everything starts here.
        #Is essentially the opening '.'
        self.root = ELTrieNode()

    def is_empty(self):
        return self.root.is_empty()
        
    def add_fact(self,el_string):
        """ Add an EL String into the Trie """

        #First change is (Parent,Original,New) for rewinding
        first_change = (None,None,None)
        current = self.root
        for el_pair in el_string.data:
            if el_pair.elop != current.elop:
                return first_change
            
            #If a pure addition:
            elif current.is_empty():
                new_node = ELTrieNode(el_pair.elop,el_pair.value)
                current
                
            #else do the elops match?
            elif el_pair.elop != current.elop:
                return False
            #elops match, move down
            

            
        return True
        
    def remove_fact(self,el_string):
        """ Remove an EL String from the Trie """
        return False
        
    def test(self,el_string):
        """ Given an EL String, test the Trie to see if it is true """

    def get(self,el_string):
        """ Get the values at the leaf of the specified EL String """
        


          

