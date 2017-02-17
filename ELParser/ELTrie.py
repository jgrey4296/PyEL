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

    def __repr__(self):
        return "EL_Trie_Node({},{})".format(str(self.value),str(self.elop))
            
    def is_empty(self):
        return len(self.children) == 0
        
    def elops_match(self,el_op):
        return False

    def __getitem__(self,key):
        if isinstance(key,ELBD.ELPAIR):
            return self.children[key.value]
        elif isinstance(key,ELBD.ELTERM):
            return self.children[key.value]
        else:
            return self.children[key]

    def __setitem__(self,key,value):
        if isinstance(key,ELBD.ELPAIR):
            self.children[key.value] = value
        elif isinstance(key,ELBD.ELTERM):
            self.children[key.value] = value
        else:
            self.children[key] = value
            
    def __contains__(self,key):
        if isinstance(key,ELBD.ELPAIR):
            return key.value in self.children
        elif isinstance(key,ELBD.ELTERM):
            return key.value in self.children
        else:
            return key in self.children
        
    def keys(self):
        return self.children.keys()

    
class ELTrie:
    """ A Simple Python Trie implementation for EL """
    def __init__(self):
        #The root element of the trie, everything starts here.
        #Is essentially the opening '.'
        self.root = ELTrieNode('ROOT')

    def is_empty(self):
        return self.root.is_empty()
        
    def push(self,el_string):
        """ Take an ELFact of [ROOT, [PAIRS], TERM],
        and attempt to add to the trie
        """
        assert isinstance(el_string,ELBD.ELFACT)
        assert isinstance(el_string.data[0],ELBD.ELROOT)
        if len(el_string.data) > 1:
            assert isinstance(el_string.data[-1],ELBD.ELTERM)
        
        #First change is (Parent,Original,New) for rewinding
        first_change = (None,None,None)
        current = None
        for statement in el_string:
            if isinstance(statement,ELBD.ELROOT):
                current = self.root
                continue
            elif isinstance(statement,ELBD.ELTERM) and statement not in current:
                current[statement] = ELTrieNode(statement)
            elif isinstance(statement,ELBD.ELPAIR) and statement not in current:
                current[statement] = ELTrieNode(statement)
            current = current[statement]
            
        return ELBD.ELSuccess()
        
    def pop(self,el_string):
        """ Remove an EL String from the Trie """
        return False
        
    def test(self,el_string):
        """ Given an EL String, test the Trie to see if it is true """

    def get(self,el_string):
        """ Get the values at the leaf of the specified EL String
            Returns an ELBD.ELRESULT

        """
        assert isinstance(el_string,ELBD.ELFACT)
        if len(el_string.data) == 1 and isinstance(el_string.data[0],ELBD.ELROOT):
            return ELBD.ELGet(self.root.value, list(self.root.keys()))
        else:
            current = None
            for statement in el_string:
                if isinstance(statement,ELBD.ELROOT):
                    current = self.root
                    continue
                elif statement in current:
                    current = current[statement]
                else:
                    return ELBD.ELFail()

            return ELBD.ELGet(current.value,list(current.keys()))
        
        

          

