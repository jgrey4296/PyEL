"""
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
from fractions import Fraction
import re
from . import ELExceptions as ELE
from .ELUtil import ELCOMP_lookup, ELARITH_lookup, EL, ELVARSCOPE
from .ELCompFunctions import ELCOMP
from .ELStructure import ELVAR, ELPAIR
from .ELFactStructure import ELFACT, ELARITH_FACT, ELROOT, ELComparison
from .ELActions import ELBIND
import IPython

##############################
# INTERNAL ENUMS
####################
#Allows management of Components in the parse, but remember to wrap in str()
#Not intended to be human usable, or anywhere other than the parser.
PARSENAMES = Enum('PARSENAMES', 'BASEFACT ARRAY FACT TERMINAL ROOT CONDITIONS ACTIONS BINDINGS BINDCOMPS NOT ARITH_OP STANDARDCOMP_OP NEARCOMP_OP')

##############################
# Utilities
####################
#Shortcuts:
s = pp.Suppress
op = pp.Optional
opLn = s(op(pp.LineEnd()))

def debugPA(toks):
    IPython.embed(simple_prompt=True)

def array_template(element, brackets_optional=False):
    """ An template function to create different types of arrays,
    pass in the element form you want to parse, get back the generated parser
    """
    o_bracket = s(O_BRACKET)
    c_bracket = s(C_BRACKET)
    if brackets_optional:
        o_bracket = op(o_bracket)
        c_bracket = op(c_bracket)
    parser = o_bracket + \
             op(opLn \
                + element
                + pp.ZeroOrMore(s(COMMA) + opLn \
                                + element)) \
                + c_bracket
    return parser


##############################
# PARSE focused Constructors
####################
def construct_el_fact(toks):
    if str(PARSENAMES.BASEFACT) not in toks:
        raise ELE.ELParseException('No BaseFact provided', toks)
    negated = str(PARSENAMES.NOT) in toks
    root = toks[str(PARSENAMES.ROOT)]
    base = toks[str(PARSENAMES.BASEFACT)][:]
    new_fact = ELFACT(negated=negated)
    new_fact.insert(root)
    for x in base:
        new_fact.insert(x)

    term = toks[str(PARSENAMES.TERMINAL)][0]
        
    if term is not None and isinstance(term, list):
        new_fact.insert(term)
    elif term is not None:
        new_fact.pair(term)
            
    return new_fact

def construct_el_query(toks):
    if not isinstance(toks[0], ELFACT):
        raise ELE.ELConsistencyException("Query constructed on non-fact")
    return toks[0].query()

def construct_arith_fact(toks):
    if not (isinstance(toks[0], ELFACT) or isinstance(toks[0], ELVAR)):
        raise ELE.ELParseException('Arith fact constructor not passed a fact or variable')
    return ELARITH_FACT(data=toks[0], op=toks[1][0], val=toks[1][1])


def construct_num(toks):
    underscore_removed = toks.replace('_', '')
    if 'd' in toks:
        return float(underscore_removed.replace('d', '.'))
    elif '/' in toks:
        return Fraction(underscore_removed)
    else:
        return int(underscore_removed)

def construct_comp_op(toks):
    if str(PARSENAMES.STANDARDCOMP_OP) in toks:
        if toks[str(PARSENAMES.STANDARDCOMP_OP)][0] in ELCOMP_lookup:
            return (ELCOMP_lookup[toks[str(PARSENAMES.STANDARDCOMP_OP)][0]], None)
        else:
            raise ELE.ELParseException('Unrecognised comparison operator')
    elif str(PARSENAMES.NEARCOMP_OP) in toks:
        return (ELCOMP.NEAR, toks[str(PARSENAMES.NEARCOMP_OP)][0])
    else:
        raise ELE.ELParseException("Comparison isn't standard OR the near operator")

def construct_arith_op(tok):
    if tok in ELARITH_lookup:
        return ELARITH_lookup[tok]
    else:
        raise ELE.ELParseException('Unrecognised arithmetic operator')

def construct_el_var(toks):
    is_a_path_var = 'PATH_ACCESS' in toks
    scope_type = toks['VAR_SCOPE'][0]
    var_name = toks['VARNAME']
    has_array_access = 'ARR_ACCESS' in toks
    if has_array_access:
        arr_access_value = toks['ARR_ACCESS'][0]
    else:
        arr_access_value = None
    return ELVAR(var_name, arr_access_value, is_a_path_var, scope_type)

def construct_el_root_fact(toks):
    if toks[0][0] is EL.DOT:
        return ELROOT(EL.DOT)
    elif toks[0][0] is EL.ROOT:
        return ELROOT(elop=toks[0][1], var=EL.ROOT)
    elif isinstance(toks[0][0], ELVAR):
        return ELROOT(elop=toks[0][1], var=toks[0][0])
    else:
        raise ELE.ELParseException('Unrecognised element of el_root_fact')

def construct_bind_statement(toks):
    if len(toks) == 2:
        return ELBIND(toks[0], toks[1])
    else:
        return ELBIND(toks[0], None)


##############################
# Main Grammar
####################
#Symbols
COMMENTS  = pp.Suppress(pp.Literal('#') + pp.SkipTo(pp.LineEnd()))
DOT       = pp.Keyword('.', identChars='!')
EX        = pp.Keyword('!', identChars='.')
NOT       = pp.Keyword('~')
ARROW     = pp.Keyword('->')
BIND      = pp.Keyword('<-')
COMMA     = pp.Keyword(',', '.')
QUERYOP   = pp.Literal('?')
VBAR      = pp.Literal('|')
O_BRACKET = pp.Literal('[')
C_BRACKET = pp.Literal(']')
O_BRACE   = pp.Literal('{')
C_BRACE   = pp.Literal('}')
O_PAREN   = pp.Literal('(')
C_PAREN   = pp.Literal(')')
DOLLAR    = pp.Literal('$')
AT        = pp.Literal('@')
SLASH     = pp.Literal('/')
DBL_VLINE      = pp.Literal('||')

#Subtree application and testing
S_APP     = pp.Keyword('::', identChars='?!')
S_APP_EX  = pp.Keyword('::!', identChars='?')
S_TEST    = pp.Keyword('::?')

ARITH     = pp.Word('-+*/^%', exact=1)

NAME      = pp.Word(pp.alphas)
IG_NAME   = pp.Word('_', pp.alphas)
NUM       = pp.Word(pp.nums + '-_d/') #negation, formatting, decimal, and fraction
STRING    = pp.dblQuotedString


NON_PATH_VAR = pp.Forward()
PATH_VAR   = pp.Forward()

VAR_HEADER = pp.Group(DOLLAR | AT)


PATH_VAR << VAR_HEADER.setResultsName('VAR_SCOPE') + \
    pp.Group(pp.Keyword('..', ' .')).setResultsName('PATH_ACCESS') + \
    pp.Word(pp.alphas + pp.nums).setResultsName('VARNAME') - \
    op(s(O_PAREN) + (NUM | NON_PATH_VAR) + s(C_PAREN)).setResultsName('ARR_ACCESS')

NON_PATH_VAR << VAR_HEADER.setResultsName('VAR_SCOPE') + \
           pp.Word(pp.alphas + pp.nums).setResultsName('VARNAME') - \
           op(s(O_PAREN) + (NUM | NON_PATH_VAR) + s(C_PAREN)).setResultsName('ARR_ACCESS')




ELEMENT   = (NON_PATH_VAR | NAME | STRING | NUM)

NEAR      = s(pp.Word('~=', exact=2)) + s(O_PAREN) + (NUM | NON_PATH_VAR) + s(C_PAREN)
COMP      = pp.Group(pp.Word('=><@!', max=2)).setResultsName(str(PARSENAMES.STANDARDCOMP_OP)) | \
            pp.Group(NEAR).setResultsName(str(PARSENAMES.NEARCOMP_OP))


#Comparison: $v1 < $V2
EL_COMPARISON = NON_PATH_VAR - COMP - ELEMENT

#Forward declaraction of fact:
FACT = pp.Forward()

#An array for rules, as it contains facts
CONDITION = FACT + s(QUERYOP)
EL_CONDITIONS = array_template(CONDITION, brackets_optional=True)

#An arithmetic action fact: .a.b.c + 20
ARITH_FACT = (FACT | NON_PATH_VAR | PATH_VAR) + \
             pp.Group(ARITH + (NON_PATH_VAR | NUM)).setResultsName(str(PARSENAMES.ARITH_OP))

#Regex Action?
REGEX_OP = pp.Word('>>')
REGEX = s(SLASH) + pp.Regex(r'[a-zA-Z0-9*+?()\[\]\\\'" <>,.$]+') + s(SLASH) + \
        pp.Regex(r'[a-zA-Z0-9*+?()\[\]\\\'"<> ,.$]+') + s(SLASH)
REGEX_ACTION = (FACT | NON_PATH_VAR) + pp.Group(REGEX_OP + (NON_PATH_VAR | REGEX))

#TODO: EL_ARRAY -> SEQUENCE
#a basic array of values in EL: [ e1, e2 ... en ]
EL_ARRAY = array_template(CONDITION | FACT | EL_COMPARISON | ARITH_FACT | REGEX_ACTION | ELEMENT)

#TODO:Other Actions? Stack/Queue/sample_from?
#TODO: add a negated path var fact special case.
# (ie: {.a.b.$x? -> ~@..x }
ACTION_ARRAY = array_template(ARITH_FACT | REGEX_ACTION | FACT, brackets_optional=True)

#Fact Components, [Root ... pairs ... terminal]
#Core part of a fact: a.b!c => (a,DOT),(b.EX)
EL_PAIR = ELEMENT + pp.NotAny(pp.LineEnd()) + (DOT | EX)
EL_FACT_ROOT = pp.Group(((PATH_VAR | DBL_VLINE) + (DOT | EX)) | DOT).setResultsName(str(PARSENAMES.ROOT))
EL_FACT_TERMINAL = ELEMENT | pp.Group(EL_ARRAY)
#An Entire sequence, note the stopOn to not continue over lines
FACT << op(NOT).setResultsName(str(PARSENAMES.NOT)) + \
                              EL_FACT_ROOT + \
                              pp.Group(pp.ZeroOrMore(EL_PAIR)).setResultsName(str(PARSENAMES.BASEFACT)) + \
                              pp.Group(EL_FACT_TERMINAL).setResultsName(str(PARSENAMES.TERMINAL))

BIND_STATEMENT = NON_PATH_VAR + s(BIND) + op(FACT)

#Execute Statements?

#The entire grammar:
ROOT = pp.OneOrMore((BIND_STATEMENT | CONDITION | FACT) + \
                    s(COMMA | pp.LineEnd())).ignore(COMMENTS) \
                    + pp.StringEnd()

##############################
# PARSE NAMES
##############################

DOT.setName('DOT')
EX.setName('EX')
NOT.setName('NOT')
NAME.setName('Name')
IG_NAME.setName('IG_NAME')
NUM.setName('Nums')
STRING.setName('String')
PATH_VAR.setName('PathVar')
COMP.setName('Comp')
EL_COMPARISON.setName('Comparison')
FACT.setName('Fact')
CONDITION.setName('Condition')
ARITH_FACT.setName('Arith Fact')
BIND_STATEMENT.setName('Binding')

##############################
# PARSE ACTIONS
##############################

#Straight forward creation of Symbols/Enums
DOT.setParseAction(lambda toks: EL.DOT)
EX.setParseAction(lambda toks: EL.EX)
DOLLAR.setParseAction(lambda toks: ELVARSCOPE.EXIS)
AT.setParseAction(lambda toks: ELVARSCOPE.FORALL)
DBL_VLINE.setParseAction(lambda toks: EL.ROOT)

#Creating the lowest level data structures:
COMP.setParseAction(construct_comp_op)
ARITH.setParseAction(lambda toks: construct_arith_op(toks[0]))
NUM.setParseAction(lambda toks: construct_num(toks[0]))
STRING.setParseAction(pp.removeQuotes)

#Regex Action:
#todo: make a substitute action
REGEX.setParseAction(lambda toks: re.compile(toks[0]))

#Variable construction
PATH_VAR.setParseAction(construct_el_var)
NON_PATH_VAR.setParseAction(construct_el_var)

#wapping a fact in a query:
CONDITION.setParseAction(lambda toks: construct_el_query(toks))
EL_COMPARISON.setParseAction(lambda toks: ELComparison(toks[0], toks[1], toks[2]))
EL_PAIR.setParseAction(lambda tok: ELPAIR(tok[0], tok[1]))
EL_FACT_ROOT.setParseAction(construct_el_root_fact)
#tok[0][0] for the group wrapping then element/array wrapping
EL_FACT_TERMINAL.setParseAction(lambda tok: tok[0])
EL_ARRAY.setParseAction(lambda toks: [toks[:]])
ARITH_FACT.setParseAction(construct_arith_fact)
FACT.setParseAction(construct_el_fact)
BIND_STATEMENT.setParseAction(construct_bind_statement)

##############################
# MAIN PARSER FUNCTION:
####################
def ELPARSE(string):
    results = []
    try:
        results = ROOT.parseString(string, parseAll=True)[:]
    except pp.ParseBaseException as pe:
        logging.warning("ParseException: L:{}_C:{}: {}".format(pe.lineno, pe.col, pe.line))
        raise ELE.ELParseException("ELParseException: L:{}_C:{}: {}".format(pe.lineno, pe.col, pe.line))
    except ELE.ELException as ele:
        print('ELE Exception: {}'.format(ele))
        logging.warning("ELException: {}".format(ele))
        raise ele
    return results


########################################
if __name__ == "__main__":
    LOGLEVEL = root_logger.DEBUG
    LOG_FILE_NAME = "genTest.log"
    root_logger.basicConfig(filename=LOG_FILE_NAME, level=LOGLEVEL, filemode='w')
    console = root_logger.StreamHandler()
    console.setLevel(root_logger.INFO)
    root_logger.getLogger('').addHandler(console)
    logging = root_logger.getLogger(__name__)
    #An Example of usage:
    parse_results = ROOT.parseString('.this.is.a.test\n.here.is!another\n.and.one.more.[1,2,3]')
    IPython.embed(simple_prompt=True)
