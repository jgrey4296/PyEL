"""
Base Data for EL
"""
from enum import Enum
from collections import namedtuple

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
        return self.data.__iter__()

    def __getitem__(self,i):
        return self.data[i]

    def complete(self):
        return len(self) > 0 and isinstance(self.data[-1],ELTERM)

#results from Trie manipualtion:
class ELRESULT:
    """ Base Class of Results """

class ELSuccess(ELRESULT):
    """ Indication of success """
    
class ELFail(ELRESULT):
    """ Indication of failure """
    
    
class ELGet(ELRESULT):
    """ A Successful result """
    def __init__(self,value,children):
        self.value = value
        self.children = children

    def __getitem__(self,i):
        return self.children[i]

    def __iter__(self):
        return self.children.__iter__()

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
