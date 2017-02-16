"""
Base Data for EL
"""
from enum import Enum
from collections import namedtuple

#Enums
EL = Enum('EL','DOT EX')


#Tuples, the main Intermediate Representations to feed to the runtime
ELROOT = namedtuple('ELROOT','elop') #always elop=DOT
ELFACT = namedtuple('ELFact','data')
ELPAIR = namedtuple('ELPair','value elop')
ELTERM = namedtuple('ELTerminal','value') #The terminal of an ELString

