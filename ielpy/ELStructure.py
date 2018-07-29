"""
Internal Structure of EL Statements
"""
from .ELUtil import EL, ELVARSCOPE, ELARR, ELOP2STR
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
    def __init__(self,
                 bindName,
                 scope=ELVARSCOPE.EXIS,
                 path_var=False,
                 arr_type=None,
                 arr_point=None):
        self.value = bindName            #ie: x
        self.scope = scope               #ie: $ or @ or @!
        self.is_path_var = path_var      #True if $..x 
        
        self.array_type = arr_type       #[] or ()
        self.array_point = arr_point     #2, $x, 

    def __hash__(self):
        return hash(repr(self))

    def __repr__(self):
        output = "VAR({})".format(str(self))
        return output
                
    def __str__(self):
        output = ""
        if self.scope is ELVARSCOPE.EXIS:
            output += "$"
        elif self.scope is ELVARSCOPE.EXFORALL:
            output += '@!'
        else:
            output += "@"
        if self.is_path_var:
            output += ".."
        output += self.value
        if self.array_type is ELARR.DEFINE:
            output += "({})".format(str(self.array_point))
        elif self.array_type is ELARR.ACCESS:
            output += "[{}]".format(str(self.array_point))
        return output
            
        
    def __eq__(self, other):
        return self.value == other.value and self.array_point == other.array_point
    
    def copy(self):
        return ELVAR(self.value)

    ##############################
    
    def get_val(self, binding_slice, trie=None): # binding_frame=None, trie=None):
        """ Given some bindings, reify this variable """
        # if self.scope is ELVARSCOPE.FORALL:
        #     return_val = self.get_value_all_values(binding_frame)
        # else:
        return_val = self._get_value(binding_slice, trie=trie)
        return return_val



    # $x, $..x, $x[2], $..x[2], $x[$y], $..x[$y]
    def _get_value(self, binding_slice, arr_point=None, trie=None):
        if self.is_path_var:
            field = 'uuid'
        else:
            field = 'value'
        if self.array_point is not None:
            arr_point = self.array_point
            
        el_bind_entry = binding_slice[self.value]
        #to get ELBindingEntry.uuid or ELBE.value, dynamically:
        field_value = getattr(el_bind_entry, field)
        if arr_point is not None:
            if isinstance(arr_point, ELVAR):
                reified_arr_point = arr_point._get_value(binding_slice)
            elif hasattr(arr_point, '_isElFact'): #avoid circular dep
                reified_arr_point = get_arr_point_from_trie(arr_point, binding_slice, trie)
            else:
                reified_arr_point = arr_point
            value = field_value[reified_arr_point]
        else:
            value = field_value
        return value


#utility functions:

def get_arr_point_from_trie(fact, binding_slice, trie):
    assert trie is not None
    #reify string:
    bound = fact.bind(binding_slice)
    result = trie.get(bound.query())
    trie_node = trie[result.nodes[0]]
    value = trie_node.child_value()
    return value
