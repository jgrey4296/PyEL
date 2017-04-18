"""
IR Representations of actions the runtime can perform in EL
"""
import logging as root_logger
from .ELFactStructure import ELFACT
from . import ELExceptions as ELE

logging = root_logger.getLogger(__name__)


##########
# ACTIONS
##########
class ELAction:
    """ The Base class of actions """

class ELBIND(ELAction):
    """ An IR representation of the runtime 'bind' instruction """
    def __init__(self, var, root):
        logging.debug("Creating a Bind Action")
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
