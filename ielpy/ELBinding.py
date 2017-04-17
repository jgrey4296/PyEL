"""
Classes relating to the structuring of binding
"""
import logging as root_logger
logging = root_logger.getLogger(__name__)

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

    def copy(self):
        return ELBindingFrame(data=self)
            
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

    def copy(self):
        return ELBindingSlice(self)


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
        
