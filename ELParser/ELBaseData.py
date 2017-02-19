"""
Base Data for EL
"""
from enum import Enum
from collections import namedtuple
import logging as root_logger
logging = root_logger.getLogger(__name__)


#Enums
EL = Enum('EL','DOT EX')
#El Value enum
ELV = Enum('ELV','ARR')

def ELOP2STR(elop):
    assert isinstance(elop,EL)
    if elop == EL.DOT:
        return "."
    elif elop == EL.EX:
        return "!"
    else:
        return elop

class ELAction:
    """ The Base class of actions """


    
#The main Intermediate Representations to feed to the runtime
class ELROOT:
    """ The Representation of the Trie root """
    def __init__(self,elop=EL.DOT):
        self.elop = elop
        
    def __repr__(self):
        return "ROOT{}".format(ELOP2STR(self.elop))

    def __eq__(self,other):
        return self.elop == other.elop

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

    def __eq__(self,other):
        return self.elop == other.elop and self.value == other.value
    
class ELTERM:
    """ Internal representation of the terminal of the EL String
    """
    def __init__(self,value):
        self.value = value
        
    def __repr__(self):
        return "{} ||".format(str(self.value))

    def __eq__(self,other):
        return self.value == other.value
    
class ELRULE:
    """ Internal representation of a rule """
    def __init__(self,conditions,actions,bindings=[],binding_comparisons=[]):
        self.conditions = conditions
        self.actions = actions
        self.bindings = bindings
        self.binding_comparisons = binding_comparisons

    def __repr__(self):
        return "Rule({},{},{},{})".format(str(self.conditions),
                                             str(self.actions),
                                             str(self.bindings),
                                             str(self.binding_comparisons))

    def __eq__(self,other):
        if all([x == y for x,y in zip(self.conditons,other.conditions)]) \
           and all([x == y for x,y in zip(self.actions, other.actions)]) \
           and all([x == y for x,y in zip(self.bindings, other.bindings)]) \
           and all([x == y for x,y in zip(self.binding_comparisons, other.binding_comparisons)]):
            return True
        else:
            return False
               
    
class ELFACT:
    """ An internal representation of an EL Fact string """

    def __init__(self,data=None, r=False):
        if data is None:
            self.data = []
            if r is True:
                self.data.append(ELROOT())
        else:
            self.data = data


    def is_valid(self):
        """ Ensure this is a valid fact """
        #Must end with a term
        if not isinstance(self.data[-1],ELTERM):
            raise Exception("Fact is not valid: No ELTERM")
        for x in self.data[1:]:
        	if isinstance(x,ELPAIR) and isinstance(x.value,list):
                    #must not have arrays as pairs, only terminals
                    raise Exception("Fact is not valid: has Array in non-terminal")

    def is_valid_for_searching(self):
        """ Ensure this fact is valid for using as a search 
        relaxes constraints on the string, can be just '.', and doesn't have to end 
        with an ELTERM
        """
        for x in self.data[1:]:
        	if isinstance(x,ELPAIR) and isinstance(x.value,list):
                    #must not have arrays as pairs, only terminals
                    raise Exception("Fact is not valid: has Array in non-terminal")

                
    def __repr__(self):
        return "| {} |" .format("".join([str(x) for x in self]))
        
    def root(self):
        return self.data[0]

    def __len__(self):
        return len(self.data[1:])

    def push(self,statement):
        self.data.append(statement)
        return self

    def pair(self,*args):
        return self.push(ELPAIR(*args))

    def epair(self,arg):
        return self.push(ELPAIR(arg,EL.EX))

    def term(self,*args):
        return self.push(ELTERM(*args))

    
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
            if isinstance(key.value,list):
                #Only terminals can have arrays, but they are unhashable so use the ELV.ARR enum
                return self.children[ELV.ARR]
            else:
                return self.children[key.value]
        else:
            return self.children[key]

    def __setitem__(self,key,value):
        if self.elop == EL.EX:
            self.children.clear()
        if isinstance(key,ELPAIR):
            self.children[key.value] = value
        elif isinstance(key,ELTERM):
            #Only terminals can have arrays, but they are unhashable so use the ELV.ARR enum
            if isinstance(key.value,list):
                self.children[ELV.ARR] = value
            else:
                self.children[key.value] = value
        else:
            self.children[key] = value
            
    def __contains__(self,key):
        if isinstance(key,ELPAIR):
            #check the key is right, and the elop is right
            return key.value in self.children and self.children[key.value] == key
        elif isinstance(key,ELTERM):
            #only check the key is right, as a terminal doesn't specify exclusion status
            return key.value in self.keys()
        else:
            return key in self.children
        
    def keys(self):
        #get keys, but replace arrays with their actual values
        keys = list(self.children.keys())
        if ELV.ARR in keys:
            keys[keys.index(ELV.ARR)] = self.children[ELV.ARR].value        
        return keys
