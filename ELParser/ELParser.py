"""
An experiment in generating text using a combinator parser
"""
# Setup root_logger:
import logging as root_logger
logging = root_logger.getLogger(__name__)

##############################
# IMPORTS
####################
from enum import Enum 
import pyparsing as pp
from pyparsing import pyparsing_common as ppc
from fractions import Fraction
import ELParser.ELBaseData as ELBD
import IPython

#Shortcuts:
s = pp.Suppress

#Allows management of Components in the parse, but remember to wrap in str()
#Not intended to be human usable, or anywhere other than the parser.
PARSENAMES = Enum('PARSENAMES','BASEFACT ARRAY FACT TERMINAL ROOT')

#Human usable names of the parser:
FACTNAME = "Fact"


#Utilities
def debugPA(toks):
    IPython.embed(simple_prompt=True)

#ELBD construction functions, only intended to be used in the parser 
def construct_el_fact(toks):
    if str(PARSENAMES.BASEFACT) not in toks:
        raise Exception('No BaseFact provided',toks)
    root = [toks[0]]
    base = toks[str(PARSENAMES.BASEFACT)][:]
    term = [toks[-1]]
    return ELBD.ELFACT(root + base + term)



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
#Reference
# Group, Suppress, ParseResults, Forward
# OnlyOnce, , FollowedBy, NotAny, OneOrMore, ZeroOrMore, Optional, SkipTo, Combine, Dict
# And, Each, MatchFirst, Or, CharsNotIn, Empty, Keyword, CaselessKeyword, Literal, CaselessLiteral,
# NoMatch, QuotedString, Regex, White, Word
#PARSER.setParseAction(lambda toks: toks))
#PARSER.setResultsName('')
#PARSER.parseString('')


DOT = pp.Keyword('.', identChars='!')
DOT.setParseAction(lambda toks: ELBD.EL.DOT)
EX = pp.Keyword('!', identChars='.')
EX.setParseAction(lambda toks : ELBD.EL.EX)

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
ARRAY.setParseAction(lambda toks: [toks[:]])
#The final part of a fact can be an array:
EL_ARRAY = ARRAY
#Core part of a fact:
EL_PAIR = ELEMENT + pp.NotAny(pp.LineEnd()) + (DOT | EX)
EL_PAIR.setParseAction(lambda tok: ELBD.ELPAIR(tok[0],tok[1]))
#Root part of a fact:
EL_FACT_ROOT = pp.Group(DOT)
EL_FACT_ROOT.setParseAction(lambda tok: ELBD.ELROOT(ELBD.EL.DOT))
EL_FACT_TERMINAL = pp.Group(ELEMENT | EL_ARRAY)
#tok[0][0] for the group wrapping then element wrapping
EL_FACT_TERMINAL.setParseAction(lambda tok: ELBD.ELTERM(tok[0][0]))

#An Entire sequence, note the stopOn to not continue over lines
FACT = EL_FACT_ROOT + pp.Group(pp.ZeroOrMore(EL_PAIR)).setResultsName(str(PARSENAMES.BASEFACT)) + EL_FACT_TERMINAL
FACT.setParseAction(lambda toks: construct_el_fact(toks))
FACT.setResultsName(FACTNAME)


#The entire grammar:
ROOT = pp.OneOrMore(FACT + s(pp.LineEnd() | pp.StringEnd())).ignore(COMMENTS)


#TODO: SET FAIL ACTIONS: .setFailAction(lambda s,loc,expr,err: 0)


########################################
if __name__ == "__main__":
    LOGLEVEL = root_logger.DEBUG
    LOG_FILE_NAME = "genTest.log"
    root_logger.basicConfig(filename=LOG_FILE_NAME, level=LOGLEVEL, filemode='w')
    console = root_logger.StreamHandler()
    console.setLevel(root_logger.INFO)
    root_logger.getLogger('').addHandler(console)
    logging = root_logger.getLogger(__name__)
    logging.info("Starting ")
    
