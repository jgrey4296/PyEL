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
PARSENAMES = Enum('PARSENAMES','BASEFACT ARRAY FACT TERMINAL ROOT RULE CONDITIONS ACTIONS BINDINGS BINDCOMPS NOT ARITH_OP')

#Human usable names of the parser:
FACTNAME = "Fact"

#Utilities
def debugPA(toks):
    IPython.embed(simple_prompt=True)

#ELBD construction functions, only intended to be used in the parser 
def construct_el_fact(toks):
    if str(PARSENAMES.BASEFACT) not in toks:
        raise ELE.ELParseException('No BaseFact provided',toks)
    negated = str(PARSENAMES.NOT) in toks
    root = [toks[str(PARSENAMES.ROOT)]]
    base = toks[str(PARSENAMES.BASEFACT)][:]
    term = [toks[str(PARSENAMES.TERMINAL)][0]]
    #values in basefact are wrapped in elpairs, need to unwrap:
    bindings = [x.value for x in toks[str(PARSENAMES.BASEFACT)] if isinstance(x.value,ELBD.ELVAR)]
    if isinstance(toks[str(PARSENAMES.TERMINAL)][0].value,ELBD.ELVAR):
        bindings.append(toks[str(PARSENAMES.TERMINAL)][0].value)
    return ELBD.ELFACT(root + base + term,bindings=bindings, negated=negated)

def construct_arith_fact(toks):
    if not (isinstance(toks[0], ELBD.ELFACT) or isinstance(toks[0], ELBD.ELVAR)):
        raise ELE.ELParseException('Arith fact constructor not passed a fact or variable')
    return ELBD.ELARITH_FACT(data=toks[0],op=toks[1][0],val=toks[1][1])
    

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
    if str(PARSENAMES.BINDCOMPS) in toks:
        bind_comp = toks[str(PARSENAMES.BINDCOMPS)][:]
    else:
        bind_comp = []
    constructed_rule = ELBD.ELRULE(conditions,actions,bind_comp)
    if not constructed_rule.balanced_bindings():
        raise ELE.ELConsistencyException("Rule bindings are not balanced")
    return constructed_rule

    
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


def array_template(element,brackets_optional=False):
    """ An template function to create different types of arrays, 
    pass in the element form you want to parse, get back the generated parser
    """
    o_bracket = s(O_BRACKET)
    c_bracket = s(C_BRACKET)
    if brackets_optional:
        o_bracket = op(o_bracket)
        c_bracket = op(c_bracket)
    parser = o_bracket + \
             op( opLn \
                 + element
                 + pp.ZeroOrMore(s(pp.Literal(',')) + opLn \
                                 + element)) \
                + c_bracket
    return parser

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


ARITH     = pp.Word('-+*/^%',exact=1)
COMP      = pp.Word('=><@!~',max=2)

O_BRACKET = pp.Literal('[')
C_BRACKET = pp.Literal(']')
O_BRACE   = pp.Literal('{')
C_BRACE   = pp.Literal('}')
O_PAREN   = pp.Literal('(')
C_PAREN   = pp.Literal(')')

VAR       = pp.Word('$', pp.alphas + pp.nums)
NAME      = pp.Word(pp.alphas)
IG_NAME   = pp.Word('_',pp.alphas)
NUM       = pp.Word(pp.nums + '-_d/') #negation, formatting, decimal, and fraction
STRING    = pp.dblQuotedString
ELEMENT   = (VAR | NAME | STRING | NUM)

#Comparison:
EL_COMPARISON = VAR + COMP + VAR
EL_COMPARISON_ARRAY = array_template(EL_COMPARISON)

#Forward declaraction of fact:
FACT = pp.Forward()

#An array in EL: [ e1, e2 ... en ]
EL_ARRAY = array_template(ELEMENT)

#An array for rules, as it contains facts
EL_RULE_ARRAY = array_template(FACT)

#a Rule of conditions -> actions
EL_RULE = s(O_BRACE) + opLn + \
          EL_RULE_ARRAY.setResultsName(str(PARSENAMES.CONDITIONS)) + \
          op(s(pp.Literal('|')) + pp.Group(EL_COMPARISON_ARRAY).setResultsName(str(PARSENAMES.BINDCOMPS))) + \
          opLn + ARROW + opLn + \
          EL_RULE_ARRAY.setResultsName(str(PARSENAMES.ACTIONS)) + \
          opLn + s(C_BRACE)

#Fact Components, [Root ... pairs ... terminal]
#Core part of a fact: a.b!c => (a,DOT),(b.EX)
EL_PAIR = ELEMENT + pp.NotAny(pp.LineEnd()) + (DOT | EX)
EL_FACT_ROOT = pp.Group(DOT).setResultsName(str(PARSENAMES.ROOT))
EL_FACT_TERMINAL = pp.Group(ELEMENT | EL_ARRAY | EL_RULE)
#An Entire sequence, note the stopOn to not continue over lines
FACT << op(NOT).setResultsName(str(PARSENAMES.NOT)) + \
    EL_FACT_ROOT + \
    pp.Group(pp.ZeroOrMore(EL_PAIR)).setResultsName(str(PARSENAMES.BASEFACT)) + \
    pp.Group(EL_FACT_TERMINAL).setResultsName(str(PARSENAMES.TERMINAL))

#The entire grammar:
ROOT = pp.OneOrMore(FACT + s(pp.LineEnd() | pp.StringEnd())).ignore(COMMENTS)


#Top Level entry:
def ELPARSE(string):
    results = []
    results =  ROOT.parseString(string)
    return results


##############################
# PARSE ACTIONS
##############################
DOT.setParseAction(lambda toks: ELBD.EL.DOT)
EX.setParseAction(lambda toks : ELBD.EL.EX)
COMP.setParseAction(lambda toks: construct_comp_op(toks[0]))
ARITH.setParseAction(lambda toks: construct_arith_op(toks[0]))
NUM.setParseAction(lambda toks: construct_num(toks[0]))

#Get the binding, and lop off the $:
VAR.setParseAction(lambda tok: ELBD.ELVAR(tok[0][1:]))

EL_COMPARISON.setParseAction(lambda toks: ELBD.ELComparison(toks[0], toks[1], toks[2]))

EL_ARRAY.setParseAction(lambda toks: [toks[:]])

EL_RULE.setParseAction(construct_rule)

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
    
