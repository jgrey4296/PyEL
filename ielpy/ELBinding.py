"""
Classes relating to the structuring of binding
"""
import logging as root_logger
logging = root_logger.getLogger(__name__)

from random import randrange

##########
# Binding
##########
#Binding: Stack<Frame>, Frame, Slice, Entry
class ELBindingStack(list):
    """ The stack of assignments to keep between rules
    [ ELBindingFrame, ELBindingFrame... ]
    """
    def __init__(self):
        super().__init__([ELBindingFrame()])
    def top(self):
        return self[-1].copy()
    def push_stack(self):
        self.append(self.top())
    def __repr__(self):
        return "ELBStack({})".format(super().__repr__())    

class ELBindingFrame(list):
    """ All possibilites across current slices
    [ ELBindingSlice(x=2..), ELBindingSlice(x=4...) ]
    #todo: encode weights?
    """
    def __init__(self, data=None):
        #todo: add a inter_frame ELBinding, make sure its copied
        if data is None:
            super().__init__([ELBindingSlice()])
        else:
            super().__init__(data)

    def copy(self):
        return ELBindingFrame(data=self)
    def select(self,i=None):
        if i is None:
            i = randrange(0,len(self))
        if i >= len(self):
            raise Exception('Trying to designate a slice not in frame')
        self.selected = i

    def has_selection(self):
        return self.selected is not None

    def get_selected(self):
        if len(self) == 1:
            return self[0]
        if self.selected is None:
            raise Exception('Trying to select from an unselected frame')
        return self[self.selected]
    
    def __repr__(self):
        return "ELBFrame({})".format(super().__repr__())
            
class ELBindingSlice(dict):
    """ The dictionaries of a rule possibility,
    { x : (ELBindingEntry), y: (ELBinding Entry ... }
    """
    def __init__(self, data=None, node_uuid=None):
        if isinstance(data, ELBindingSlice):
            super().__init__(data)
            self.uuid = data.uuid
            if node_uuid is not None:
                self.uuid = node_uuid
        else:
            if data is None:
                data = []
            super().__init__(data)
            self.uuid = node_uuid

    def __repr__(self):
        return "ELBSlice({})".format(super().__repr__())
            
    def copy(self):
        return ELBindingSlice(self)

    def to_simple_dict(self):
        """
        utility to turn a binding slice into a normal dictionary,
        to allow a string to be format_map'd 
        """
        return {x.key: x.value for x in self.values()}
    

class ELBindingEntry:
    """ Contains a single data point, $x = 5.
    Stores both the node uuid and the value itself
    """
    def __init__(self, key, node_uuid, value):
        self.key = key
        self.uuid = node_uuid
        self.value = value

    def __repr__(self):
        return "ELBindEntry({}, {}, +uuid)".format(self.key, self.value)
