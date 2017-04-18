"""
The ways ELStructure components can be assembled into facts
"""
import IPython
import logging as root_logger
from uuid import UUID
from .ELFunctions import ELCOMP, ELARITH, get_EL_FUNC
from .ELUtil import EL, ELVARSCOPE, EL_ARITH_2_STR, EL_COMP_2_STR
from .ELBinding import ELBindingSlice 
from .ELStructure import ELSTRUCTURE, ELPAIR, ELROOT, ELVAR, ELQUERY
from . import ELExceptions as ELE

logging = root_logger.getLogger(__name__)

##########
# FACT Structure
##########    
class ELExpandable(ELSTRUCTURE):
    def expand(self):
        return [self]
    
class ELFACT(ELExpandable):
    """ An internal representation of an EL Fact string """

    def __init__(self, data=None,
                 r=False,
                 bindings=None,
                 negated=False,
                 filled_bindings=None):
        if data is None:
            data = []
        if bindings is None:
            bindings = []

        self.data = []
        self.negated = negated
        #variables of the fact. [x,y,z...]
        self.bindings = bindings.copy()
        #filled_bindings :: ELBindingSlice
        if filled_bindings is None:
            self.filled_bindings = ELBindingSlice()
        else:
            self.filled_bindings = ELBindingSlice(filled_bindings)
        if r is True:
            self.data.insert(0,ELROOT())
        for x in data:
            self.insert(x)
            

    def expand(self):
        """ Takes a fact with a terminal array,
        and converts it into a list of facts """
        logging.info("Expanding Fact")
        current = self[0:-1]
        term = self[-1]
        if not isinstance(term, list):
            return [self]
        output = []
        #Add the root fact up to the terminal
        #output.append(ELFACT(current))
        #Now expand out each element in the list
        for i,x in enumerate(term):
            index_pair = [ELPAIR(i)]
            if isinstance(x, ELFACT):
                #lop off the duplicated root
                new_fact = ELFACT(current + x[1:])
            elif isinstance(x, list):
                new_fact = ELFACT(current + x)
            elif isinstance(x, ELARITH_FACT) or isinstance(x, ELComparison):
                local_string = current.copy() + index_pair
                local_string.append(x.expand())
                new_fact = ELFACT(local_string)
            else:
                new_fact = ELFACT(current)
                new_fact.pair(x)

            #recurse down, extending as necessary:
            flattened = new_fact.expand()
            output.extend(flattened)

        if len(term) == 0:
            output.append(ELFACT(current))
            
        logging.info("Result of expanded Fact: {}".format(output))
        return output

            
    def hasForAllBinding(self):
        """ Return true if any binding is a forall binding """
        #todo: this doesn't account for forall variables that are array accessors
        allforalls = [x.scope is ELVARSCOPE.FORALL for x in self.bindings]
        return any(allforalls)


    def bind(self, binding_slice, all_sub_slice=None):
        #return a copy of the fact, where the var has been switched out
        #TODO: CONVERT PATH_VARS TO NODE IDS TO RETRIEVE AND MOD LATER?
        logging.info("Binding to fact: {}".format(binding_slice))
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
        logging.info("Binding Result: {}".format(new_fact))
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
        copy = self.copy()
        copy.negated = not self.negated
        return copy

    def __eq__(self, other):
        return all([x == y for x, y in zip(self.data, other.data)])

    def __repr__(self):
        strings = [repr(x) for x in self.data]
        
        joined_strings = "".join(strings)
        if self.negated:
            return "| ~{} |".format(joined_strings)
        else:
            return "| {} |" .format(joined_strings)

    def __str__(self):
        strings = [str(x) for x in self.data]
        joined_strings = "".join(strings)
        if self.negated:
            return "~{}".format(joined_strings)
        else:
            return joined_strings

    def short_str(self):
        """ Get the string up to, but not including,
        the last entry in the fact """
        value = "".join([str(x) for x in self.data[0:-1]])
        if value[-1] == '.' or value[-1] == '!':
            return value[0:-1]
        else:
            return value

    def __len__(self):
        return len(self.data[:])

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, i):
        return self.data[i]


    # Construction Utilities:
    def root(self):
        return self.data[0]

    def insert(self, statement, prepend=False):
        """ Utility for easy construction of a fact """
        if not prepend:
            self.data.append(statement)
        elif isinstance(self.data[0], ELROOT):
            self.data.insert(1, statement)
        else:
            self.data.insert(0, statement)
        #update binding record:
        if isinstance(statement, ELPAIR) and isinstance(statement.value, ELVAR):
            self.bindings.append(statement.value)
            if isinstance(statement.value.access_point, ELVAR):
                self.bindings.append(statement.value.access__point)
        elif isinstance(statement, ELVAR):
            self.bindings.append(statement)
            if isinstance(statement.access_point, ELVAR):
                self.bindings.append(statement.access_point)
        return self

    
    def query(self):
        copy = self.copy()
        copy.insert(ELQUERY())
        return copy
    
    def var(self, *args, prepend=False):
        """ Utility for easy construction of a variable """
        var = ELVAR(*args)
        pair = ELPAIR(var)
        return self.insert(pair, prepend=prepend)

    def pair(self, *args, prepend=False):
        """ Utility for easy construction of a fact:
        Internally create a new ELPAIR
        """
        return self.insert(ELPAIR(*args), prepend=prepend)

    def evar(self, *args, prepend=False):
        """ Utility for easy construction of an exclusive variable """
        var = ELVAR(*args)
        pair = ELPAIR(var, EL.EX)
        self.insert(pair, prepend=prepend)

    def epair(self, arg, prepend=False):
        """ Utility for easy construction of a fact:
        Internally create a new Exclusive ELPair
        """
        return self.insert(ELPAIR(arg, EL.EX), prepend=prepend)

    def pop(self, start=False):
        """ Get the last element of the fact """
        if start:
            return self.data.pop(0)
        else:
            return self.data.pop()


class ELComparison(ELExpandable):
    """ Holds a comparison operation between two bindings """
    def __init__(self, b1, op, b2):
        self.op = op[0]
        #only used for ~= operator
        self.nearVal = op[1]
        #VARS:
        self.b1 = b1
        self.b2 = b2

    def expand(self):
        """ Convert the IR representation of the comparison to a 
        true Trie representation in the form:
        .operator!{op}
        .near!{nearVal}
        .focus!{b1}
        .value!{b2}
        """
        logging.info("Expanding comparison: {}".format(str(self)))
        #focus:
        if isinstance(self.b1, ELFACT):
            focus = self.b1.copy().epair('focus', prepend=True)
        else:
            focus = ELFACT(r=True).epair('focus').pair(self.b1)
        #value:
        if isinstance(self.b2, ELFACT):
            value = self.b2.copy().epair('value', prepend=True)
        else:
            value = ELFACT(r=True).epair('value').pair(self.b2)
        #operator:
        operator = ELFACT(r=True).epair('operator').pair(self.op)
        #nearVal:
        if self.nearVal is not None and isinstance(self.nearVal, ELFACT):
            near = self.nearVal.copy().epair('near', prepend=True)
        elif self.nearVal is not None:
            near = ELFACT(r=True).epair('near').pair(self.nearVal)
        else:
            near = None
            
        if near is not None:
            return [focus, value, operator, near]
        else:
            return [focus, value, operator]
        
        
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


class ELARITH_FACT(ELExpandable):
    """ An internal representation of an arithmetic operator fact,
    for use in actions
    Essentially a wrapper to house a fact, an operation, and a value to apply
    """
    def __init__(self, data=None, op=None, val=None):
        if not (isinstance(data, ELFACT) or isinstance(data, ELVAR) or isinstance(data, UUID)):
            raise ELE.ELConsistencyException('All Arith facts need a fact or variable as a base')
        if not isinstance(op, ELARITH):
            raise ELE.ELConsistencyException('Arith Fact missing an operator')
        if val is None:
            raise ELE.ELConsistencyException('Arith fact must have a value')
        ####
        self.data = data #A fact or Var
        self.op = op   #an operator
        self.val = val #a value or binding
        self.bindings = []
        ####
        if isinstance(data, ELVAR):
            self.bindings.append(data)
        elif isinstance(data, ELPAIR):
            self.bindings.extend(data.bindings)
        if isinstance(val, ELVAR):
            self.bindings.append(val)

        #retrieve sub vars
        self.bindings.extend([x.access_point for x in self.bindings if isinstance(x.access_point, ELVAR)])

    def expand(self):
        """ Take the IR representation of an arithmetic fact,
        and turn it into a true trie representation of form:
        .focus!{data}
        .operator!{op}
        .value!{val}
        """
        logging.info("Expanding Arith: {}".format(str(self)))
        operator = ELFACT(r=True)
        value = ELFACT(r=True)
        #Add focus data:
        if isinstance(self.data, ELVAR):
            focus = ELFACT(r=True).epair('focus').pair(self.data)
        elif isinstance(self.data, ELFACT):
            focus = self.data.copy().epair('focus', prepend=True)

        #add op data:
        operator.epair('operator').pair(self.op)
        #add value data:
        if isinstance(self.val, ELVAR):
            value.epair('value').pair(self.val)
        elif isinstance(self.val, ELFACT):
            value = self.val
            value.epair('value', prepend=True)
                
        return [focus, operator, value ]

        
    def hasForAllBinding(self):
        """ If one of the bindings is scoped to forall, return true """
        forallbindings = [x.scope is ELVARSCOPE.FORALL for x in self.bindings]
        return any(forallbindings)

    def apply(self, node):
        """ An encapuslated way to perform an arithmetic action, just add a target """
        func = get_EL_FUNC(self.op, comp=False)
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
        val = str(self.val)
        if isinstance(self.val, float):
            val = str(self.val).replace(".", "d")

        return "{} {} {}".format(str(self.data),
                                 op,
                                 val)

    def copy(self):
        return ELARITH_FACT(self.data.copy(), self.op, self.val.copy())

    
