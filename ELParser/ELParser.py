"""
An experiment in generating text using a combinator parser
There are a couple of main segments to this file:
1) Constant names / enums for internal use of the parser
2) Utility functions to construct data structures from parse data, 
	to interface with the runtime
3) The actual grammar combinators themselves
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
import ELParser.ELExceptions as ELE
import IPython

#Shortcuts:
s = pp.Suppress
op = pp.Optional
opLn = s(op(pp.LineEnd()))


#Allows management of Components in the parse, but remember to wrap in str()
#Not intended to be human usable, or anywhere other than the parser.
PARSENAMES = Enum('PARSENAMES','BASEFACT ARRAY FACT TERMINAL ROOT RULE CONDITIONS ACTIONS BINDINGS BINDCOMPS NOT')

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
    term = [toks[str(PARSENAMES.TERMINAL)][0]]
    return ELBD.ELFACT(root + base + term)

def construct_num(toks):
    underscore_removed = toks.replace('_','')
    if 'd' in toks:
        return float(underscore_removed.replace('d','.'))
    elif '/' in toks:
        return Fraction(underscore_removed)
    else:
        return int(underscore_removed)

def construct_comp_op(tok):
    if tok in ELBD.ELCOMP_lookup:
        return ELBD.ELCOMP_lookup[tok]
    else:
        raise ELE.ELParseException('Unrecognised comparison operator')

def construct_arith_op(tok):
    if tok in ELBD.ELARITH_lookup:
        return ELBD.ELARITH_lookup[tok]
    else:
        raise ELE.ELParseException('Unrecognised arithmetic operator')

    
def construct_rule(toks):
    conditions = toks[str(PARSENAMES.CONDITIONS)][:]
    actions = toks[str(PARSENAMES.ACTIONS)][:]
    if str(PARSENAMES.BINDINGS) in toks:
        bindings = toks[str(PARSENAMES.BINDINGS)][:]
    else:
        bindings = []
    if str(PARSENAMES.BINDCOMP) in toks:
        bind_comp = toks[str(PARSENAMES.BINDCOMP)][:]
    else:
        bind_comp = []
    return ELBD.ELRULE(conditions,actions,bindings,bind_comp)

    
#####################
# Grammar
#Reference
# Group, Suppress, ParseResults, Forward
# OnlyOnce, , FollowedBy, NotAny, OneOrMore, ZeroOrMore, Optional, SkipTo, Combine, Dict
# And, Each, MatchFirst, Or, CharsNotIn, Empty, Keyword, CaselessKeyword, Literal, CaselessLiteral,
# NoMatch, QuotedString, Regex, White, Word
#PARSER.setParseAction(lambda toks: toks))
#PARSER.setResultsName('')
#PARSER.parseString('')


#The Grammar Combinators, parse actions come later
COMMENTS  = pp.Suppress(pp.Literal('#') + pp.SkipTo(pp.LineEnd()))
DOT       = pp.Keyword('.', identChars='!')
EX        = pp.Keyword('!', identChars='.')
NOT       = pp.Keyword('~')
ARROW     = pp.Keyword('->')
BIND      = pp.Keyword('<-')
#Subtree application and testing
S_APP     = pp.Keyword('::', identChars='?')
S_TEST    = pp.Keyword('::?')


ARITH     = pp.Word('-+*/^',exact=1)
COMP      = pp.Word('><',exact=1)

O_BRACKET = pp.Literal('[')
C_BRACKET = pp.Literal(']')
O_BRACE   = pp.Literal('{')
C_BRACE   = pp.Literal('}')
O_PAREN   = pp.Literal('(')
C_PAREN   = pp.Literal(')')

VAR       = pp.Word('$', pp.nums | pp.nums)
NAME      = pp.Word(pp.alphas)
IG_NAME   = pp.Word('_',pp.alphas)
NUM       = pp.Word(pp.nums + '-_d/') #negation, formatting, decimal, and fraction
STRING    = pp.dblQuotedString
ELEMENT   = (VAR | NAME | STRING | NUM)

#Forward declaraction of fact:
FACT = pp.Forward()


#An array in EL: [ e1, e2 ... en ]
EL_ARRAY = s(O_BRACKET) + \
           op( opLn \
               + ELEMENT
               + pp.ZeroOrMore(s(pp.Literal(',')) + opLn \
               + ELEMENT)) \
        + s(C_BRACKET)

#An array for rules, as it contains facts
EL_RULE_ARRAY = s(O_BRACKET) + \
                op( opLn \
                    + FACT
                    + pp.ZeroOrMore(s(pp.Literal(',')) + opLn \
        	    + FACT)) \
                + s(C_BRACKET)

#a Rule of conditions -> actions
EL_RULE = s(O_BRACE) + opLn + \
          EL_RULE_ARRAY.setResultsName(str(PARSENAMES.CONDITIONS)) + \
          opLn + ARROW + opLn + \
          EL_RULE_ARRAY.setResultsName(str(PARSENAMES.ACTIONS)) + \
          opLn + s(C_BRACE)

#Core part of a fact:
EL_PAIR = ELEMENT + pp.NotAny(pp.LineEnd()) + (DOT | EX)
#Fact Components, [Root ... pairs ... terminal]
EL_FACT_ROOT = pp.Group(DOT)
EL_FACT_TERMINAL = pp.Group(ELEMENT | EL_ARRAY | EL_RULE)
#An Entire sequence, note the stopOn to not continue over lines
FACT << EL_FACT_ROOT + \
        pp.Group(pp.ZeroOrMore(EL_PAIR)).setResultsName(str(PARSENAMES.BASEFACT)) + \
        pp.Group(EL_FACT_TERMINAL).setResultsName(str(PARSENAMES.TERMINAL))

#The entire grammar:
ROOT = pp.OneOrMore(FACT + s(pp.LineEnd() | pp.StringEnd())).ignore(COMMENTS)


#Top Level entry:
def ELPARSE(string):
    results = []
    try:
        results =  ROOT.parseString(string)
    except pp.ParseException as e:
        logging.exception(e)
    finally:
        return results


##############################
# PARSE ACTIONS
##############################
DOT.setParseAction(lambda toks: ELBD.EL.DOT)
EX.setParseAction(lambda toks : ELBD.EL.EX)
NUM.setParseAction(lambda toks: construct_num(toks[0]))
EL_ARRAY.setParseAction(lambda toks: [toks[:]])
EL_RULE.setParseAction(lambda toks: construct_rule(toks))
EL_RULE_ARRAY.setParseAction(lambda toks: [toks[:]])
EL_PAIR.setParseAction(lambda tok: ELBD.ELPAIR(tok[0],tok[1]))
EL_FACT_ROOT.setParseAction(lambda tok: ELBD.ELROOT(ELBD.EL.DOT))
#tok[0][0] for the group wrapping then element/array wrapping
EL_FACT_TERMINAL.setParseAction(lambda tok: ELBD.ELTERM(tok[0][0]))
FACT.setParseAction(lambda toks: construct_el_fact(toks))
FACT.setResultsName(FACTNAME)

##############################
# TODO : FAIL ACTIONS
##############################



########################################
if __name__ == "__main__":
    LOGLEVEL = root_logger.DEBUG
    LOG_FILE_NAME = "genTest.log"
    root_logger.basicConfig(filename=LOG_FILE_NAME, level=LOGLEVEL, filemode='w')
    console = root_logger.StreamHandler()
    console.setLevel(root_logger.INFO)
    root_logger.getLogger('').addHandler(console)
    logging = root_logger.getLogger(__name__)
    results = ROOT.parseString('.this.is.a.test\n.here.is!another\n.and.one.more.[1,2,3]')
    IPython.embed(simple_prompt=True)
    
