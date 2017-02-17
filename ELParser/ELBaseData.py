"""
Base Data for EL
"""
from enum import Enum
from collections import namedtuple
import logging as root_logger
logging = root_logger.getLogger(__name__)


#Enums
EL = Enum('EL','DOT EX')

def ELOP2STR(elop):
    assert isinstance(elop,EL)
    if elop == EL.DOT:
        return "."
    elif elop == EL.EX:
        return "!"
    else:
        return elop

#Tuples, the main Intermediate Representations to feed to the runtime
class ELROOT:
    """ The Representation of the Trie root """
    def __init__(self,elop=EL.DOT):
        self.elop = elop
        
    def __repr__(self):
        return "ROOT{}".format(ELOP2STR(self.elop))

class ELPAIR:
    """ Internal pairs of statements of |test.|blah!|something.|
    Does not represent terminals 
    """
    def __init__(self,value,elop=EL.DOT):
        self.value = value
        self.elop = elop

    def __repr__(self):
        op = ELOP2STR(self.elop)
        return "{}{}".format(str(self.value),op)

class ELTERM:
    """ Internal representation of the terminal of the EL String
    """
    def __init__(self,value):
        self.value = value

    def __repr__(self):
        return "{} ||".format(str(self.value))
    
class ELFACT:
    """ An internal representation of an EL Fact string """

    def __init__(self,data=None, r=False):
        if data is None:
            self.data = []
            if r is True:
                self.data.append(ELROOT())
        else:
            self.data = data


    def __repr__(self):
        return "| {} |" .format("".join([str(x) for x in self]))
        
    def root(self):
        return self.data[0]

    def __len__(self):
        return len(self.data[1:])

    def push(self,statement):
        self.data.append(statement)
        return self

    def pop(self):
        return self.data.pop()

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self,i):
        return self.data[i]

    def complete(self):
        return len(self) > 0 and isinstance(self.data[-1],ELTERM)

#results from Trie manipualtion:
class ELRESULT:
    """ Base Class of Results """

class ELSuccess(ELRESULT):
    """ Indication of success """
    def __bool__(self):
        return True    
    def __eq__(self,other):
        return other == True
    def __repr__(self):
        return "ELSuccess"
    
class ELFail(ELRESULT):
    """ Indication of failure """
    def __bool__(self):
        return False
    def __eq__(self,other):
        return other == False
    def __repr__(self):
        return "ELFailure"
    
class ELGet(ELRESULT):
    """ A Successful result """
    def __init__(self,value,children):
        self.value = value
        self.children = children

    def __bool__(self):
        return True
        
    def __repr__(self):
        return "({} , {})".format(str(self.value),str(self.children))
        
    def __len__(self):
        return len(self.children)
        
    def __getitem__(self,i):
        return self.children[i]

    def __iter__(self):
        return iter(self.children)

    def __contains__(self,key):
        if isinstance(key,ELPAIR):
            return key.value in self.children
        elif isinstance(key,ELTERM):
            return key.value in self.children
        else:
            return key in self.children

    def __eq__(self,other):
        if isinstance(other,ELPAIR):
            return self.value == other.value
        elif isinstance(other,ELTERM):
            return self.value == other.value
        else:
            return self.value == other

        
class ELTrieNode:
    """ The internal node used for the Trie.
    Nominally an EL Operator (DOT or EX), and a value, usually a dict 
    """
    
    def __init__(self,val):
        self.elop = EL.DOT
        self.value = None
        self.children = {}
        if isinstance(val,ELPAIR):
            self.elop = val.elop
            self.value = val.value
        elif isinstance(val,ELTERM):
            self.value = val.value
        else:
            self.value = val

    #def __del__(self):
    #    logging.warning("ELTrie Node being destroyed: {}".format(str(self)))
            
    def __repr__(self):
        return "EL_Trie_Node({},{})".format(str(self.value),str(self.elop))
            
    def is_empty(self):
        return len(self.children) == 0
        
    def __eq__(self,other):
        """ Check that EL ops match """
        if isinstance(other, ELPAIR):
            return self.elop == other.elop
        else:
            return False

    def __getitem__(self,key):
        if isinstance(key,ELPAIR):
            return self.children[key.value]
        elif isinstance(key,ELTERM):
            return self.children[key.value]
        else:
            return self.children[key]

    def __setitem__(self,key,value):
        if self.elop == EL.EX:
            self.children.clear()
        if isinstance(key,ELPAIR):
            self.children[key.value] = value
        elif isinstance(key,ELTERM):
            self.children[key.value] = value
        else:
            self.children[key] = value
            
    def __contains__(self,key):
        if isinstance(key,ELPAIR):
            #check the key is right, and the elop is right
            return key.value in self.children and self.children[key.value] == key
        elif isinstance(key,ELTERM):
            #only check the key is right, as a terminal doesn't specify exclusion status
            return key.value in self.children
        else:
            return key in self.children
        
    def keys(self):
        return self.children.keys()
