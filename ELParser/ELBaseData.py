"""
Base Data for EL
Enums: EL, ELV, ELCOMP, ELARITH

Classes: ELAction, ELComparison,
ELROOT, ELPAIR, ELTERM, ELRULE, ELARITH_FACT,
ELVAR
ELFACT, ELBIND

ELRESULT: ELSuccess, ELFail,

ELTrieNode

"""
import IPython
from enum import Enum
from collections import namedtuple
import logging as root_logger
import uuid
from ELParser.ELCompFunctions import get_ARITH_FUNC, ELCOMP, ELARITH
import ELParser.ELExceptions as ELE

logging = root_logger.getLogger(__name__)
##############################
# ENUMS
####################
#Exclusion Type of a fact component
EL = Enum('EL', 'DOT EX')
#Subtypes of leaves
ELV = Enum('ELV', 'ARR RULE')
#Scope Applicability of a Variable:
ELVARSCOPE = Enum('ELVARSCOPE', 'EXIS FORALL')


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
    '%' : ELARITH.MOD,
    'rnd' : ELARITH.RAND,
    'lg': ELARITH.LOG
}

#from stackoverflow question 483666
def EL_ARITH_2_STR(enumValue):
    lookup = {v: k for k, v in ELARITH_lookup.items()}
    if enumValue in lookup:
        return lookup[enumValue]
    else:
        raise ELE.ELParseException("Enum value {} not found".format(enumValue))

def EL_COMP_2_STR(enumValue):
    lookup = {v:k for k, v in ELCOMP_lookup.items()}
    if enumValue in lookup:
        return lookup[enumValue]
    else:
        raise ELE.ELParseException("Enum value {} not found".format(enumValue))


def ELOP2STR(elop):
    assert isinstance(elop, EL)
    if elop == EL.DOT:
        return "."
    elif elop == EL.EX:
        return "!"
    else:
        return elop

##############################
# Classes
####################

#Binding: Stack<Frame>, Frame, Slice, Entry
class ELBindingStack(list):
    """ The stack of assignments to keep between rules
    [ ELBindingFrame, ELBindingFrame... ]
    """
    def __init__(self):
        super().__init__([ELBindingFrame()])
    def top(self):
        return ELBindingFrame(self[-1])
    def add_level(self):
        self.append(self.top())


class ELBindingFrame(list):
    """ All possibilites across current slices
    [ ELBindingSlice(x=2..), ELBindingSlice(x=4...) ]
    """
    def __init__(self, data=None):
        #todo: add a inter_frame ELBinding, make sure its copied
        if data is None:
            super().__init__([ELBindingSlice()])
        else:
            super().__init__(data)

class ELBindingSlice(dict):
    """ The dictionaries of a rule possibility,
    { x : (ELBindingEntry), y: (ELBinding Entry ... }
    """
    def __init__(self, data=None, id=None):
        if data is None:
            data = []
            
        if isinstance(data, ELBindingSlice):
            super().__init__(data)
            self.uuid = data.uuid
            if id is not None:
                self.uuid = id
        else:
            super().__init__(data)
            self.uuid = uuid

    def copy(self):
        return ELBindingSlice(self)


class ELBindingEntry:
    """ Contains a single data point, $x = 5.
    Stores both the node uuid and the value itself
    """
    def __init__(self, key, id, value):
        self.key = key
        self.node = id
        self.value = value


#----------
# ACTIONS
#----------
class ELAction:
    """ The Base class of actions """

class ELComparison(ELAction):
    """ Holds a comparison operation between two bindings """
    def __init__(self, b1, op, b2):
        self.op = op[0]
        #only used for ~= operator
        self.nearVal = op[1]
        #VARS:
        self.b1 = b1
        self.b2 = b2

    def __repr__(self):
        if self.nearVal is None:
            return "({} {} {})".format(self.b1, EL_COMP_2_STR(self.op), self.b2)
        else:
            return "({} {}({}) {})".format(self.b1, EL_COMP_2_STR(self.op), self.nearVal, self.b2)

    def __str__(self):
        if self.op is not ELCOMP.NEAR:
            return str(self.b1) + EL_COMP_2_STR(self.op) + str(self.b2)
        else:
            return "{} {}({}) {}".format(str(self.b1),
                                         EL_COMP_2_STR(self.op),
                                         str(self.nearVal),
                                         str(self.b2))


    def __eq__(self, other):
        return self.op == other.op and \
            self.b1 == other.b1 and \
            self.b2 == other.b2

    def copy(self):
        return ELComparison(self.b1, (self.op, self.nearVal), self.b2)


class ELARITH_FACT(ELAction):
    """ An internal representation of an arithmetic operator fact,
    for use in actions
    Essentially a wrapper to house a fact, an operation, and a value to apply
    """
    def __init__(self, data=None, op=None, val=None):
        if not (isinstance(data, ELFACT) or isinstance(data, ELVAR) or isinstance(data, uuid.UUID)):
            raise ELE.ELConsistencyException('All Arith facts need a fact or variable as a base')
        if not isinstance(op, ELARITH):
            raise ELE.ELConsistencyException('Arith Fact missing an operator')
        if val is None:
            raise ELE.ELConsistencyException('Arith fact must have a value')
        self.data = data #A fact or Var
        self.op = op   #an operator
        self.val = val #a value or binding
        self.bindings = []
        #todo: populate bindings from data, and val
        if isinstance(data, ELVAR):
            self.bindings.append(data)
        elif isinstance(data, ELPAIR):
            self.bindings.extend(data.bindings)
        if isinstance(val, ELVAR):
            self.bindings.append(val)

        #retrieve sub vars
        self.bindings.extend([x.access_point for x in self.bindings if isinstance(x.access_point, ELVAR)])

    def hasForAllBinding(self):
        """ If one of the bindings is scoped to forall, return true """
        forallbindings = [x.scope is ELVARSCOPE.FORALL for x in self.bindings]
        return any(forallbindings)
            
    def apply(self, node):
        func = get_ARITH_FUNC(self.op)
        new_value = func(node.value, self.val)
        #update the parent:
        del node.parent[node]
        node.value = new_value
        node.parent[node] = node

    def bind(self, binding_slice, all_sub_slice=None):
        #returns a new bound ELARITH_FACT that has been bound
        assert isinstance(binding_slice, ELBindingSlice)
        if all_sub_slice is not None:
            assert isinstance(all_sub_slice, ELBindingSlice)
            
        if isinstance(self.data, ELVAR):
            new_data = self.data.get_val(binding_slice, all_sub_slice)
        else:
            new_data = self.data
        if isinstance(self.val, ELVAR):
            new_val = self.val.get_val(binding_slice, all_sub_slice)
        else:
            new_val = self.val
        return ELARITH_FACT(data=new_data, op=self.op, val=new_val)

    def __repr__(self):
        return "|ARITH: {} ({} {}) |".format(self.data, EL_ARITH_2_STR(self.op), self.val)

    def __str__(self):
        op = EL_ARITH_2_STR(self.op)
        return "{} {} {}".format(str(self.data),
                                 op,
                                 str(self.val))

    def copy(self):
        return ELARITH_FACT(self.data.copy(), self.op, self.val.copy())

class ELBIND(ELAction):
    """ An IR representation of the runtime 'bind' instruction """
    def __init__(self, var, root):
        if not (isinstance(root, ELFACT) or root is None):
            raise ELE.ELConsistencyException("Global bindings need to use facts")
        self.var = var
        self.root = root

    def __repr__(self):
        return "({} <- {})".format(self.var, self.root)
    def __str__(self):
        return "{} <- {}".format(str(self.var), str(self.root))
    def copy(self):
        return ELBIND(self.var.copy(), self.root.copy())

#----------
# Structure
#----------

class ELSTRUCTURE:

    def isVar(self):
        return False

class ELROOT(ELSTRUCTURE):
    """ The Representation of the Trie root """
    def __init__(self, elop=EL.DOT, var=None):
        self.elop = elop
        self.value = var

    def isVar(self):
        return self.value is not None

    def __repr__(self):
        if not self.isVar():
            return "ROOT{}".format(ELOP2STR(self.elop))
        else:
            return "ROOT({}){}".format(repr(self.value), ELOP2STR(self.elop))

    def __str__(self):
        if not self.isVar():
            return ELOP2STR(self.elop)
        else:
            return "{}{}".format(str(self.value), ELOP2STR(self.elop))

    def __eq__(self, other):
        return self.elop == other.elop and self.value == other.value

    def copy(self):
        if self.value is not None:
            return ELROOT(elop=self.elop, var=self.value.copy())
        else:
            return ELROOT(elop=self.elop)


class ELPAIR(ELSTRUCTURE):
    """ Internal pairs of statements of |test.|blah!|something.|
    Does not represent terminals
    """
    def __init__(self, value, elop=EL.DOT):
        self.value = value
        self.elop = elop

    def toTerminal(self):
        return ELTERM(self.value)

    def isVar(self):
        return isinstance(self.value, ELVAR)

    def __repr__(self):
        op = ELOP2STR(self.elop)
        return "{}{}".format(repr(self.value), op)

    def __str__(self):
        return str(self.value) + ELOP2STR(self.elop)

    def __eq__(self, other):
        return self.elop == other.elop and self.value == other.value

    def copy(self):
        try:
            return ELPAIR(self.value.copy(), self.elop)
        except AttributeError as e:
            return ELPAIR(self.value, self.elop)

class ELTERM(ELSTRUCTURE):
    """ Internal representation of the terminal of the EL String
    Houses a value, which may be a rule, or array, or simple value
    """
    def __init__(self, value):
        self.value = value

    def isVar(self):
        return isinstance(self.value, ELVAR)

    def __repr__(self):
        return "{} ||".format(repr(self.value))

    def __str__(self):
        value = str(self.value)
        if value[-1] == '.' or value[-1] == '!':
            return value[0:-1]
        else:
            return value

    def __eq__(self, other):
        return self.value == other.value

    def copy(self):
        try:
            return ELTERM(self.value.copy())
        except AttributeError as e:
            return ELTERM(self.value)

class ELRULE(ELSTRUCTURE):
    """ Internal representation of a rule """
    def __init__(self, conditions, actions, binding_comparisons=None):
        if binding_comparisons is None:
            binding_comparisons = []
        self.conditions = conditions
        self.actions = actions
        self.binding_comparisons = binding_comparisons

        #get the vars in each binding fact in conditions
        self.condition_bindings = set([var.value \
                                       for c in self.conditions \
                                       for var in c.value.bindings])

        #combine them all together:
        self.action_bindings = set([var.value \
                                    for clause in self.actions \
                                    for var in clause.bindings])

    def __hash__(self):
        return hash(repr(self))

    def copy(self):
        conditionsCopy = [x.copy() for x in self.conditions]
        actionsCopy = [x.copy() for x in self.actions]
        bindingsCopy = [x.copy() for x in self.binding_comparisons]
        return ELRULE(conditionsCopy, actionsCopy, bindingsCopy)


    def __repr__(self):
        return "Rule({},{},{})".format(repr(self.conditions),
                                       repr(self.actions),
                                       repr(self.binding_comparisons))

    def __str__(self):
        conditions = ", ".join([str(x) for x in self.conditions])
        bindings = ", ".join([str(x) for x in self.binding_comparisons])
        actions = ", ".join([str(x) for x in self.actions])
        if len(bindings) > 0:
            return "{} {} | {} -> {} {}".format('{', conditions,
                                                bindings,
                                                actions, '}')
        else:
            return "{} {} -> {} {}".format('{', conditions,
                                           actions, '}')

    def __eq__(self, other):
        #no need to compare condition/action_bindings as they are generated from these:
        if all([x == y for x, y in zip(self.conditions, other.conditions)]) \
           and all([x == y for x, y in zip(self.actions, other.actions)]) \
           and all([x == y for x, y in zip(self.binding_comparisons, other.binding_comparisons)]):
            return True
        else:
            return False


    def balanced_bindings(self):
        #get the set of all bindings used in comparisons
        comparison_set = set([x.b1.value for x in self.binding_comparisons]).union(set([x.b2.value for x in self.binding_comparisons if isinstance(x.b2, ELVAR)]))
        #get all bindings used in comparisons and actions:
        combined_bindings = self.action_bindings.union(comparison_set)
        #then get the ones that aren't in the condition_bindings
        the_difference = combined_bindings.difference(self.condition_bindings)
        return len(the_difference) == 0


class ELVAR(ELSTRUCTURE):
    """ An internal representation of a binding """
    def __init__(self, bindName, access_point=None, path_var=False, scope=ELVARSCOPE.EXIS):
        self.is_path_var = path_var
        self.scope = scope
        self.value = bindName
        if access_point is not None:
            self.access_point = access_point
        else:
            self.access_point = None

    def __repr__(self):
        if self.access_point is None:
            return "VAR({})".format(self.value)
        else:
            return "VAR({}@{})".format(self.value, self.access_point)
    def __str__(self):
        return "${}".format(self.value)
    def __eq__(self, other):
        return self.value == other.value and self.access_point == other.access_point
    def copy(self):
        return ELVAR(self.value)

    def get_val(self, binding_slice, all_sub_slice=None):
        assert isinstance(binding_slice, ELBindingSlice)
        if all_sub_slice is not None:
            assert isinstance(binding_slice, ELBindingSlice)
        return_val = None
        #Get the right scope:
        if self.scope is ELVARSCOPE.FORALL:
            assert all_sub_slice is not None
            focus_slice = all_sub_slice
        else:
            focus_slice = binding_slice
        #now get the right value:
        if self.is_path_var:
            return_val = focus_slice[self.value].node
        elif self.access_point:
            if isinstance(self.access_point, ELVAR):
                return_val = focus_slice[self.value].value[self.access_point.get_val(binding_slice, all_sub_slice)]
            else:
                return_val = focus_slice[self.value].value[self.access_point]
        else:
            return_val = focus_slice[self.value].value

        return return_val

class ELFACT(ELSTRUCTURE):
    """ An internal representation of an EL Fact string """

    def __init__(self, data=None, r=False, bindings=None, negated=False, filled_bindings=None):
        if data is None:
            data = []
        if bindings is None:
            bindings = []
        self.negated = negated
        #filled_bindings :: ELBindingSlice
        if filled_bindings is None:
            self.filled_bindings = ELBindingSlice()
        else:
            self.filled_bindings = ELBindingSlice(filled_bindings)
        #variables of the fact. [x,y,z...]
        self.bindings = bindings.copy()
        self.data = data.copy()
        if r is True:
            self.data.append(ELROOT())

    def hasForAllBinding(self):
        """ Return true if any binding is a forall binding """
        #todo: this doesn't account for forall variables that are array accessors
        allforalls = [x.scope is ELVARSCOPE.FORALL for x in self.bindings]
        return any(allforalls)

            
    def bind(self, binding_slice, all_sub_slice=None):
        #return a copy of the fact, where the var has been switched out
        #TODO: CONVERT PATH_VARS TO NODE IDS TO RETRIEVE AND MOD LATER
        assert isinstance(binding_slice, ELBindingSlice)
        if all_sub_slice is not None:
            assert isinstance(all_sub_slice, ELBindingSlice)
            
        new_string = []
        new_pair = None
        for x in self.data:
            if not x.isVar():
                new_pair = x
            elif isinstance(x, ELPAIR) and x.value.value in binding_slice:
                #ELPair.value :: ELVar
                new_pair = ELPAIR(x.value.get_val(binding_slice, all_sub_slice), \
                                  x.elop)
            elif isinstance(x, ELTERM) and x.value.value in binding_slice:
                #ELTerm.value :: ELVar
                new_pair = ELTERM(x.value.get_val(binding_slice, all_sub_slice))
            elif isinstance(x, ELROOT) and x.isVar() and x.value.value in binding_slice:
                #ELRoot.value :: ELVAR
                new_pair = ELROOT(elop=x.elop, \
                                  var=x.value.get_val(binding_slice, all_sub_slice))
            elif x.isVar() and x.value.value not in binding_slice:
                new_pair = x.copy()
            new_string.append(new_pair)
        updated_bindings = self.filled_bindings.copy()

        #todo: this has the ability to clobber bindings
        if self.hasForAllBinding():
            updated_bindings.update(all_sub_slice)
        updated_bindings.update(binding_slice)
        new_fact = ELFACT(new_string,
                          bindings=self.bindings,
                          filled_bindings=updated_bindings,
                          negated=self.negated)
        return new_fact

    def copy(self):
        dataCopy = [x.copy() for x in self.data if x is not None]
        bindingsCopy = self.bindings.copy()
        filled_bindings_copy = self.filled_bindings.copy()
        return ELFACT(dataCopy,
                      bindings=bindingsCopy,
                      negated=self.negated,
                      filled_bindings=filled_bindings_copy)

    def negate(self):
        self.negated = not self.negated
        return self

    def __eq__(self, other):
        if all([x == y for x, y in zip(self.data, other.data)]):
            return True
        else:
            return False

    def __repr__(self):
        if self.negated:
            return "| ~{} |".format("".join([repr(x) for x in self]))
        else:
            return "| {} |" .format("".join([repr(x) for x in self]))

    def __str__(self):
        if self.negated:
            return "~{}".format("".join([str(x) for x in self.data]))
        else:
            return "".join([str(x) for x in self.data])

    def short_str(self):
        """ Get the string up to, but not including,
        the last entry in the fact """
        value = "".join([str(x) for x in self.data[0:-1]])
        if value[-1] == '.' or value[-1] == '!':
            return value[0:-1]
        else:
            return value

    def __len__(self):
        return len(self.data[1:])

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, i):
        return self.data[i]

    # Construction Utilities:
    def root(self):
        return self.data[0]

    def push(self, statement):
        """ Utility for easy construction of a fact """
        self.data.append(statement)
        return self

    def var(self, *args):
        """ Utility for easy construction of a variable """
        var = ELVAR(*args)
        pair = ELPAIR(var)
        self.bindings.append(var)
        if isinstance(var.access_point, ELVAR):
            self.bindings.append(var.access_point)
        return self.push(pair)

    def pair(self, *args):
        """ Utility for easy construction of a fact:
        Internally create a new ELPAIR
        """
        return self.push(ELPAIR(*args))

    def evar(self, *args):
        """ Utility for easy construction of an exclusive variable """
        var = ELVAR(*args)
        pair = ELPAIR(var, EL.EX)
        self.bindings.append(var)
        if isinstance(var.access_point, ELVAR):
            self.bindings.append(var.access_point)
        self.push(pair)

    def epair(self, arg):
        """ Utility for easy construction of a fact:
        Internally create a new Exclusive ELPair
        """
        return self.push(ELPAIR(arg, EL.EX))

    def vterm(self, *args):
        var = ELVAR(*args)
        term = ELTERM(var)
        self.bindings.append(var)
        if isinstance(var.access_point, ELVAR):
            self.bindings.append(var.access_point)
        return self.push(term)

    def term(self, *args):
        """ Utility for construction of a new fact:
        Internally create a new terminal
        """
        return self.push(ELTERM(*args))


    def pop(self):
        """ Get the last element of the fact """
        return self.data.pop()

    def complete(self):
        """ Check to see if the fact is 'whole' (ended with a terminal) """
        return len(self) > 0 and isinstance(self.data[-1], ELTERM)

    def is_valid(self):
        """ Ensure this is a valid fact.
        Validity means the fact is made of ELPAIRS and is finished with an ELTERM
        """
        #Must end with a term
        if not isinstance(self.data[-1], ELTERM):
            raise Exception("Fact is not valid: No ELTERM")
        for x in self.data[1:]:
            if isinstance(x, ELPAIR) and isinstance(x.value, list):
                #must not have arrays as pairs, only terminals
                raise Exception("Fact is not valid: has Array in non-terminal")

    def is_valid_for_searching(self):
        """ Ensure this fact is valid for using as a search
        relaxes constraints on the string, can be just '.', and doesn't have to end
        with an ELTERM
        """
        for x in self.data[1:]:
            if isinstance(x, ELPAIR) and isinstance(x.value, list):
                #must not have arrays as pairs, only terminals
                raise Exception("Fact is not valid: has Array in non-terminal")
        return True

class ELQUERY(ELSTRUCTURE):
    """ A wrapper around a fact to signify it should be a query """
    def __init__(self, fact):
        if not isinstance(fact, ELFACT):
            raise ELE.ELConsistencyException("Queries need a fact")
        self.value = fact

    def bind(self, bindings):
        return ELQUERY(self.value.bind(bindings))

    def __eq__(self, query):
        if isinstance(query, ELQUERY):
            return self.value == query.value
        elif isinstance(query, ELFACT):
            return self.value == query
        else:
            return False

    def __repr__(self):
        return repr(self.value) + "?"

    def __str__(self):
        return str(self.value) + "?"

    def copy(self):
        return ELQUERY(self.value.copy())


#----------
#  Results
#----------

class ELRESULT:
    """ Base Class of Results """
    def __bool__(self):
        return False
    def __eq__(self, other):
        return False
    def __repr__(self):
        raise Exception('This should exist')

class ELFail(ELRESULT):
    """ Indication of failure """
    def __eq__(self, other):
        return other == False
    def __repr__(self):
        return "(ELFailure)"

class ELSuccess(ELRESULT):
    """ A Successful result """
    def __init__(self, path=None, bindings=None):
        # bindings :: ELBindingFrame
        if bindings is None:
            bindings = ELBindingFrame()
        self.bindings = bindings
        #path :: el_string with open variables applicable
        self.path = path

    def __bool__(self):
        return True

    def __repr__(self):
        return "(ELSuccess: {} , {})".format(repr(self.path), repr(self.bindings))

    def __len__(self):
        """ Get the number of children of this result """
        return len(self.bindings)

    def __getitem__(self, i):
        """ get a specified child """
        return self.bindings[i]

    def __iter__(self):
        """ Allow for each looping through the bindings """
        return iter(self.bindings)

    def __contains__(self, key):
        """ Check the result for a value in the children """
        if isinstance(key, ELPAIR):
            return key.value in self.children
        elif isinstance(key, ELTERM):
            return key.value in self.children
        else:
            return key in self.children

    def __eq__(self, other):
        """ Compare a value to the internal value """
        if isinstance(other, bool):
            return True == other
        if isinstance(other, ELPAIR):
            return self.value == other.value
        elif isinstance(other, ELTERM):
            return self.value == other.value
        else:
            return self.value == other


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
        elif isinstance(val, ELTERM):
            self.value = val.value
        else:
            self.value = val

    def contains_rule(self):
        return isinstance(self.value, ELRULE)


    def __hash__(self):
        """ Not a true hashing of the object, but good enough to enable
        usage in sets.
        Can't hash the value as that isn't unique"""
        return hash(self.uuid)


    def __repr__(self):
        return "EL_Trie_Node({},{} > {})".format(repr(self.value), \
                                                 repr(self.elop), \
                                                 repr(self.keys()))

    def __str__(self):
        return repr(self)


    def __len__(self):
        return len(self.children)

    def __eq__(self, other):
        """ Check that EL ops match """
        if isinstance(other, ELPAIR):
            return self.elop == other.elop and self.value == other.value
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
        elif isinstance(key, ELTERM):
            if isinstance(key.value, list):
                del self.children[ELV.ARR]
            elif isinstance(key.value, ELRULE):
                del self.children[ELV.RULE]
            else:
                del self.children[key.value]
        else:
            del self.children[key]


    def __getitem__(self, key):
        if isinstance(key, ELTrieNode):
            return self.children[key.value]
        elif isinstance(key, ELPAIR):
            return self.children[key.value]
        elif isinstance(key, ELTERM):
            if isinstance(key.value, list):
                #Only terminals can have arrays, but they are unhashable so use the ELV.ARR enum
                return self.children[ELV.ARR]
            elif isinstance(key.value, ELRULE):
                return self.children[ELV.RULE]
            else:
                return self.children[key.value]
        else:
            return self.children[key]

    def __setitem__(self, key, value):
        assert isinstance(value, ELTrieNode)
        #an exclusion removes all else
        if self.elop == EL.EX:
            self.children.clear()
        #now process the key val pair:
        if isinstance(key, ELTrieNode):
            self.children[key.value] = value
        elif isinstance(key, ELPAIR):
            self.children[key.value] = value
        elif isinstance(key, ELTERM):
            #Only terminals can have arrays, but they are unhashable so use the ELV.ARR enum
            if isinstance(key.value, list):
                self.children[ELV.ARR] = value
            elif isinstance(key.value, ELRULE):
                self.children[ELV.RULE] = value
            else:
                self.children[key.value] = value
        else:
            self.children[key] = value

    def __contains__(self, key):
        if isinstance(key, ELTrieNode):
            return key.value in self.keys()
        if isinstance(key, ELPAIR):
            if isinstance(key.value, ELVAR):
                raise Exception('checking trie for a var doesnt make sense')
            #check the key is right, and the elop is right
            return key.value in self.children and self.children[key.value] == key
        elif isinstance(key, ELTERM):
            #only check the key is right, as a terminal doesn't specify exclusion status
            if isinstance(key.value, list):
                return key.value in self.keys()
            elif isinstance(key.value, ELRULE):
                return key.value in self.keys()
            elif isinstance(key.value, ELVAR):
                raise Exception('checking a trie for a var doesnt make sense: {}'.format(key.value))
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

    def values(self):
        return self.children.values()

    def is_empty(self):
        return len(self.children) == 0
