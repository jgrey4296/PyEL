"""
Internal Structure of EL Statements
"""
from .ELUtil import EL, ELVARSCOPE, ELOP2STR
from .ELBinding import ELBindingSlice

##########
# Internal Fact Structure
##########

class ELSTRUCTURE:
    #todo: refactor this to is_var
    def isVar(self):
        return False


class ELROOT(ELSTRUCTURE):
    """ The Representation of the Trie root """
    def __init__(self, elop=EL.DOT, var=None):
        self.elop = elop
        self.value = var

    def __hash__(self):
        return hash("ELROOT")

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

class ELQUERY(ELSTRUCTURE):
    """ A structural representation of a query, as a terminal """
    def __repr__(self):
        return "?"


class ELPAIR(ELSTRUCTURE):
    """ Internal pairs of statements of |test.|blah!|something.|
    Does not represent terminals
    """
    def __init__(self, value, elop=EL.DOT, ex=False):
        self.value = value
        if not ex:
            self.elop = elop
        else:
            self.elop = EL.EX

    #todo: refactor names to is_arr, and is_var
    def isArr(self):
        return isinstance(self.value, list)

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

    def __hash__(self):
        return hash(repr(self))

    def __repr__(self):
        if self.access_point is None:
            return "VAR({})".format(self.value)
        else:
            return "VAR({}@{})".format(self.value, self.access_point)

    def __str__(self):
        output = ""
        if self.scope is ELVARSCOPE.EXIS:
            output += "$"
        else:
            output += "@"
        if self.is_path_var:
            output += ".."
        output += self.value
        if self.access_point is not None:
            output += "({})".format(str(self.access_point))

        return output

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
            return_val = focus_slice[self.value].uuid
        elif self.access_point:
            if isinstance(self.access_point, ELVAR):
                focus_array = focus_slice[self.value].value
                index = self.access_point.get_val(binding_slice, all_sub_slice)
                return_val = focus_array[index]
            else:
                return_val = focus_slice[self.value].value[self.access_point]
        else:
            return_val = focus_slice[self.value].value

        return return_val
