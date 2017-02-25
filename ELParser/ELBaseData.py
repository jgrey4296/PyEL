"""
Base Data for EL
Enums: EL, ELV, ELCOMP, ELARITH

Classes: ELAction, ELComparison,
ELROOT, ELPAIR, ELTERM, ELRULE, ELARITH_FACT,
ELVAR
ELFACT, ELBIND

ELRESULT: ELSuccess, ELFail, ELGet,

ELTrieNode

"""
import IPython
from enum import Enum
from collections import namedtuple
import logging as root_logger
logging = root_logger.getLogger(__name__)
import ELParser.ELExceptions as ELE

##############################
# ENUMS
####################
EL = Enum('EL','DOT EX')
ELV = Enum('ELV','ARR RULE')
ELCOMP = Enum('ELCOMP','GREATER LESSER GREATEREQUAL LESSEREQUAL EQUAL NOTEQUAL CONTAINS NOTCONTAINS NEAR')
ELARITH = Enum('ELARITH','MINUS PLUS MUL DIV POW MOD')

##############################
# Enum Utilities
####################
ELCOMP_lookup = {
    '<'   : ELCOMP.LESSER,
    '>'   : ELCOMP.GREATER,
    '<='  : ELCOMP.LESSEREQUAL,
    '>='  : ELCOMP.GREATEREQUAL,
    '=='  : ELCOMP.EQUAL,
    '!='  : ELCOMP.NOTEQUAL,
    '@'   : ELCOMP.CONTAINS,
    '!@'  : ELCOMP.NOTCONTAINS,
    '~='   : ELCOMP.NEAR
}

ELARITH_lookup = {
    '-' : ELARITH.MINUS,
    '+' : ELARITH.PLUS,
    '*' : ELARITH.MUL,
    '/' : ELARITH.DIV,
    '^' : ELARITH.POW,
    '%' : ELARITH.MOD
}

#from stackoverflow question 483666
def EL_ARITH_2_STR(enumValue):
    lookup = {v: k for k,v in ELARITH_lookup.items()}
    if enumValue in lookup:
        return lookup[enumValue]
    else:
        raise ELE.ELParseException("Enum value {} not found".format(enumValue))

def EL_COMP_2_STR(enumValue):
    lookup = {v:k for k,v in ELCOMP_lookup.items()}
    if enumValue in lookup:
        return lookup[enumValue]
    else:
        raise ELE.ELParseException("Enum value {} not found".format(enumValue))


def ELOP2STR(elop):
    assert isinstance(elop,EL)
    if elop == EL.DOT:
        return "."
    elif elop == EL.EX:
        return "!"
    else:
        return elop

##############################
# Classes
####################
    
class ELAction:
    """ The Base class of actions """

class ELComparison:
    """ Holds a comparison operation between two bindings """
    def __init__(self,b1,op,b2):
        self.op = op[0]
        #only used for ~= operator
        self.nearVal = op[1]
        self.b1 = b1
        self.b2 = b2

    def __repr__(self):
        if self.nearVal is None:
            return "({} {} {})".format(self.b1, EL_COMP_2_STR(self.op), self.b2)
        else:
            return "({} {}({}) {})".format(self.b1, EL_COMP_2_STR(self.op), self.nearVal, self.b2)
        
    def __eq__(self,other):
        return self.op == other.op and \
            self.b1 == other.b1 and \
            self.b2 == other.b2
    
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
    Houses a value, which may be a rule, or array, or simple value
    """
    def __init__(self,value):
        self.value = value
        
    def __repr__(self):
        return "{} ||".format(str(self.value))

    def __eq__(self,other):
        return self.value == other.value
    
class ELRULE:
    """ Internal representation of a rule """
    def __init__(self,conditions,actions,binding_comparisons=[]):
        self.conditions = conditions
        self.actions = actions
        #get the vars in each binding fact in conditions
        self.condition_bindings = set([x.value for c in self.conditions for x in c.bindings])
        non_arith_facts = [x for x in self.actions if isinstance(x,ELFACT)]
        arith_actions = [x for x in self.actions if isinstance(x,ELARITH_FACT)]
        arith_facts = [x.data for x in arith_actions if isinstance(x.data,ELFACT)]
        
        #get the vars in from normal action: .a.b.$c
        non_arith_vars = set([x.value for a in non_arith_facts for x in a.bindings])
        #vars of .a.b.$c + 20
        arith_fact_vars = set([x.value for a in arith_facts for x in a.bindings])
        #vars of $c + 20
        arith_raw_vars = set([x.data.value for x in arith_actions if isinstance(x.data,ELVAR)])
        #vars of .a.b.c + $d
        arith_values = set([x.val.value for x in arith_actions if isinstance(x.val,ELVAR)])

        #combine them all together:
        self.action_bindings = non_arith_vars.union(arith_fact_vars).union(arith_fact_vars, \
                                                                           arith_raw_vars, \
                                                                           arith_values)

        #Array of tuples: (op b1 b2)
        self.binding_comparisons = binding_comparisons

    def __repr__(self):
        return "Rule({},{},{})".format(str(self.conditions),
                                             str(self.actions),
                                             str(self.binding_comparisons))
            
    def __eq__(self,other):
        #no need to compare condition/action_bindings as they are generated from these:
        if all([x == y for x,y in zip(self.conditions,other.conditions)]) \
           and all([x == y for x,y in zip(self.actions, other.actions)]) \
           and all([x == y for x,y in zip(self.binding_comparisons, other.binding_comparisons)]):
            return True
        else:
            return False

    
    def balanced_bindings(self):
        #get the set of all bindings used in comparisons
        comparison_set = set([x.b1.value for x in self.binding_comparisons]).union(set([x.b2.value for x in self.binding_comparisons]))
        #get all bindings used in comparisons and actions:
        combined_bindings = self.action_bindings.union(comparison_set)
        #then get the ones that aren't in the condition_bindings
        the_difference = combined_bindings.difference(self.condition_bindings)
        return len(the_difference) == 0
        

class ELVAR:
    """ An internal representation of a binding """
    def __init__(self,bindName):
        self.value = bindName
    def __repr__(self):
        return "VAR({})".format(self.value)
    def __eq__(self,other):
        return self.value == other.value


class ELARITH_FACT:
    """ An internal representation of an arithmetic operator fact,
    for use in actions 
    Essentially a wrapper to house a fact, an operation, and a value to apply
    """
    def __init__(self, data=None, op=None, val=None):
        if not (isinstance(data,ELFACT) or isinstance(data,ELVAR)):
            raise ELE.ELConsistencyException('All Arith facts need a fact or variable as a base')
        if not isinstance(op,ELARITH):
            raise ELE.ELConsistencyException('Arith Fact missing an operator')
        self.data=data #A fact
        self.op = op   #an operator
        self.val = val #a value or binding       

    def __repr__(self):
        return "|ARITH: {} ({} {}) |".format(self.data,EL_ARITH_2_STR(self.op), self.val)
    
class ELFACT:
    """ An internal representation of an EL Fact string """

    def __init__(self,data=None, r=False, bindings = None, negated=False):
        self.negated = negated
        if bindings is not None:
            self.bindings = bindings
        else:
            self.bindings = []
        if data is None:
            self.data = []
            if r is True:
                self.data.append(ELROOT())
        else:
            self.data = data

    def __eq__(self,other):
        if all([x == y for x,y in zip(self.data,other.data)]):
            return True
        else:
            return False
                
    def __repr__(self):
        return "| {} |" .format("".join([str(x) for x in self]))

    def __len__(self):
        return len(self.data[1:])

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self,i):
        return self.data[i]
    
    def root(self):
        return self.data[0]
    
    def push(self,statement):
        """ Utility for easy construction of a fact """
        self.data.append(statement)
        return self

    def pair(self,*args):
        """ Utility for easy construction of a fact:
        Internally create a new ELPAIR
        """
        return self.push(ELPAIR(*args))

    def epair(self,arg):
        """ Utility for easy construction of a fact:
        Internally create a new Exclusive ELPair
        """
        return self.push(ELPAIR(arg,EL.EX))

    def term(self,*args):
        """ Utility for construction of a new fact:
        Internally create a new terminal
        """
        return self.push(ELTERM(*args))
    
    def pop(self):
        """ Get the last element of the fact """
        return self.data.pop()

    def complete(self):
        """ Check to see if the fact is 'whole' (ended with a terminal) """
        return len(self) > 0 and isinstance(self.data[-1],ELTERM)

    def is_valid(self):
        """ Ensure this is a valid fact. 
        Validity means the fact is made of ELPAIRS and is finished with an ELTERM
        """
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


    
class ELBIND:
    """ An IR representation of the runtime 'bind' instruction """
    def __init__(self,var, root):
        if not (isinstance(root,ELFACT) or root is None):
            raise ELE.ELConsistencyException("Global bindings need to use facts")
        self.var = var
        self.root = root

    def __repr__(self):
        return "({} <- {})".format(self.var, self.root)
    
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
        """ Get the number of children of this result """
        return len(self.children)
        
    def __getitem__(self,i):
        """ get a specified child """
        return self.children[i]

    def __iter__(self):
        """ Allow for each looping through the children """
        return iter(self.children)

    def __contains__(self,key):
        """ Check the result for a value in the children """
        if isinstance(key,ELPAIR):
            return key.value in self.children
        elif isinstance(key,ELTERM):
            return key.value in self.children
        else:
            return key in self.children

    def __eq__(self,other):
        """ Compare a value to the internal value """
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
        #Default to Dot, update later if necessary
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
            elif isinstance(key.value,ELRULE):
                return self.children[ELV.RULE]
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
            elif isinstance(key.value,ELRULE):
                self.children[ELV.RULE] = value
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
            if isinstance(key.value,list):
                return key.value in self.keys()
            elif isinstance(key.value,ELRULE):
                return key.value in self.keys()
            else:
                return key.value in self.children 
        else:
            return key in self.children
        
    def keys(self):
        #get keys, but replace arrays with their actual values
        keys = list(self.children.keys())
        if ELV.ARR in keys:
            keys[keys.index(ELV.ARR)] = self.children[ELV.ARR].value
        if ELV.RULE in keys:
            keys[keys.index(ELV.RULE)] = self.children[ELV.RULE].value
        return keys

    def is_empty(self):
        return len(self.children) == 0
