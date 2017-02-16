"""
An experiment in generating text using a combinator parser
"""
# Setup root_logger:
import logging as root_logger
LOGLEVEL = root_logger.DEBUG
LOG_FILE_NAME = "genTest.log"
root_logger.basicConfig(filename=LOG_FILE_NAME, level=LOGLEVEL, filemode='w')

console = root_logger.StreamHandler()
console.setLevel(root_logger.INFO)
root_logger.getLogger('').addHandler(console)
logging = root_logger.getLogger(__name__)
##############################
# IMPORTS
####################
from enum import Enum 
import pyparsing as pp
from pyparsing import pyparsing_common as ppc
from collections import namedtuple
from fractions import Fraction
import IPython


# Group, Suppress, ParseResults, Forward
# OnlyOnce, , FollowedBy, NotAny, OneOrMore, ZeroOrMore, Optional, SkipTo, Combine, Dict
# And, Each, MatchFirst, Or, CharsNotIn, Empty, Keyword, CaselessKeyword, Literal, CaselessLiteral,
# NoMatch, QuotedString, Regex, White, Word
#PARSER.setParseAction(lambda toks: toks))
#PARSER.setResultsName('')
#PARSER.parseString('')

#Shortcuts:
s = pp.Suppress

#Enums
EL = Enum('EL','DOT EX')
#Allows management of Components in the parse, but remember to wrap in str()
#Not intended to be human usable
PARSENAMES = Enum('PARSENAMES','BASEFACT ARRAY FACT')

#Human usable names:
FACTNAME = "Fact"

#Tuples, the main Intermediate Representations to feed to the runtime
t_ELFACT = namedtuple('ELFact','data array')
t_ELPAIR = namedtuple('ELPair','elop value')
t_ELARRAY = namedtuple('ELArray','elop value')

#Utilities
def debugPA(toks):
    IPython.embed(simple_prompt=True)

def construct_el_fact(toks):
    if str(PARSENAMES.BASEFACT) not in toks:
        raise Exception('No BaseFact provided',toks)
    if str(PARSENAMES.ARRAY) in toks:
        a = toks[str(PARSENAMES.ARRAY)][0]
    else:
        a = None
    return t_ELFACT(toks[str(PARSENAMES.BASEFACT)][:],a)

def construct_num(toks):
    underscore_removed = toks.replace('_','')
    if 'd' in toks:
        return float(underscore_removed.replace('d','.'))
    elif '/' in toks:
        return Fraction(underscore_removed)
    else:
        return int(underscore_removed)
        

#####################
# Grammar
COMMENTS = pp.Suppress(pp.Literal('#') + pp.SkipTo(pp.LineEnd()))

DOT = pp.Keyword('.', identChars='!')
DOT.setParseAction(lambda toks: EL.DOT)
EX = pp.Keyword('!', identChars='.')
EX.setParseAction(lambda toks : EL.EX)

#Individual entries in an ELString
NAME = pp.Word(pp.alphas, excludeChars='\n')
NUM = pp.Word(pp.nums + '-_d/')
NUM.setParseAction(lambda toks: construct_num(toks[0]))
STRING = pp.dblQuotedString

ELEMENT = (NAME | STRING | NUM)
#An array in EL: [ e1, e2 ... en ]
ARRAY = s(pp.Literal('[')) + pp.Optional(s(pp.Optional(pp.LineEnd()))
                                         + ELEMENT
                                         + pp.ZeroOrMore(s(pp.Literal(',')
                                                           + pp.Optional(pp.LineEnd()))
                                                         + ELEMENT)) \
                    + pp.Suppress(pp.Literal(']'))
#The final part of a fact can be an array:
EL_ARRAY = (DOT | EX) + ARRAY
EL_ARRAY.setParseAction(lambda tok: t_ELARRAY(tok[0],tok[1:]))
EL_PAIR = (DOT | EX) + ELEMENT
EL_PAIR.setParseAction(lambda tok: t_ELPAIR(tok[0],tok[1]))

#An Entire sequence, note the stopOn to not continue over lines
FACT = pp.Group(pp.OneOrMore(EL_PAIR,stopOn=pp.LineEnd())).setResultsName(str(PARSENAMES.BASEFACT)) + pp.Optional(EL_ARRAY).setResultsName(str(PARSENAMES.ARRAY))
FACT.setParseAction(lambda toks: construct_el_fact(toks))
FACT.setResultsName(FACTNAME)


#The entire grammar:
ROOT = pp.OneOrMore(FACT).ignore(COMMENTS)


########################################
if __name__ == "__main__":
    logging.info("Starting ")
    
