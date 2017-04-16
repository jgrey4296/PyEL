"""
Internal Structure to hold data relating to failable operations
"""
from .ELBinding import ELBindingFrame

##########
#  Results
##########

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
        return other is False
    def __repr__(self):
        return "(ELFailure)"

class ELSuccess(ELRESULT):
    """ A Successful result """
    def __init__(self, path=None, bindings=None, nodes=None):
        # bindings :: ELBindingFrame
        if bindings is None:
            bindings = ELBindingFrame()
        if nodes is None:
            nodes = []
        self.bindings = bindings
        #path :: el_string with open variables applicable
        self.path = path
        #a specifically retrieved node
        self.nodes = nodes

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
