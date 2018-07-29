"""
Utilities for ielpy
"""
from enum import Enum
from .ELFunctions import ELCOMP, ELARITH
from . import ELExceptions as ELE

##############################
# ENUMS
####################
#Exclusion Type of a fact component
EL = Enum('EL', 'DOT EX ROOT')
#Subtypes of leaves
ELV = Enum('ELV', 'ARR RULE')
#Scope Applicability of a Variable:
ELVARSCOPE = Enum('ELVARSCOPE', 'EXIS FORALL EXFORALL')
#Execution Types:
ELEXT = Enum('EL_Ex_t','TRIE TREE FSM SEL INS')
#EL Array var types, definition(), and access[]
ELARR = Enum('EL_Arr_t', 'DEFINE ACCESS')

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

