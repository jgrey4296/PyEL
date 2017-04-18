"""
The exception classes used for iEL
"""

class ELException(Exception):
    """ The Base class for all iEL exceptions """
    None

class ELParseException(ELException):
    """ The Exception Raised when a parse error occurs """
    None

class ELTrieException(ELException):
    """ The Exception Raised when a Trie error occurs """
    None

class ELRuntimeException(ELException):
    """ The Exception raised when a runtime error occurs """
    None

class ELConsistencyException(ELException):
    """ The Exception raised when a static analysis exception occurs """
    None

class ELRuleException(ELException):
    """ A Failure occured in the course of running a rule """
    None

class ELNotImplementedException(ELException):
    """ Raised when a not-implemented feature is called """
    None
