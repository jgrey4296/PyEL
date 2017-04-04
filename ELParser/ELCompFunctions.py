import logging as root_logger
logging = root_logger.getLogger(__name__)
from enum import Enum
from math import log, exp
from random import random

#Enums, moved here from base data to stop circular dependence
ELCOMP = Enum('ELCOMP','GREATER LESSER GREATEREQUAL LESSEREQUAL EQUAL NOTEQUAL CONTAINS NOTCONTAINS NEAR')
ELARITH = Enum('ELARITH','MINUS PLUS MUL DIV POW MOD RAND LOG')


#Comparison Functions:
#These keys must match the ELBD.ELCOMP enum
COMP_FUNCS = {
    ELCOMP.GREATER : lambda a, b: a > b,
    ELCOMP.LESSER  : lambda a, b: a < b,
    ELCOMP.GREATEREQUAL : lambda a, b: a >= b,
    ELCOMP.LESSEREQUAL : lambda a, b: a <= b,
    ELCOMP.EQUAL : lambda a, b: a == b,
    ELCOMP.NOTEQUAL : lambda a, b: a != b,
    ELCOMP.CONTAINS : lambda a, b: a in b,
    ELCOMP.NOTCONTAINS : lambda a, b: a not in b,
    ELCOMP.NEAR : lambda a, v, b: (a-v) <= b <= (a+v)
}

#Arithmetic Functions:
#These keys must match the ELBD.ELARITH enum
ARITH_FUNCS = {
    ELARITH.MINUS : lambda a, b: a - b,
    ELARITH.PLUS : lambda a, b: a + b,
    ELARITH.MUL : lambda a, b: a * b,
    ELARITH.DIV : lambda a, b : a / b,
    ELARITH.POW : lambda a, b : pow(a,b),
    ELARITH.MOD : lambda a, b : a % b,
    ELARITH.RAND : lambda a, b : False,
    ELARITH.LOG : lambda a, b : False
}

def get_COMP_FUNC(op):
    if op in COMP_FUNCS:
        return COMP_FUNCS[op]
    raise Exception('Op not found in Comp Funcs: {}'.format(op))

def get_ARITH_FUNC(op):
    if op in ARITH_FUNCS:
        return ARITH_FUNCS[op]
    raise Exception('Op not found in Arith Funcs: {}'.format(op))
