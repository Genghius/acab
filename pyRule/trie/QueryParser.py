import logging as root_logger
import pyparsing as pp
from pyRule.utils import Bind,META_OP
from pyRule.Comparisons import COMP, Comparison, COMP_REVERSE_LOOKUP
from .FactParser import COMMA, VALBIND, PARAM_CORE
from .Query import Query
from .Clause import Clause

pp.ParserElement.setDefaultWhitespaceChars(' \t\r')
logging = root_logger.getLogger(__name__)

def buildClause(toks):
    #detect negation and annotate the clause with it
    if 'NOT' in toks:
        return Clause(toks[1:], negated=True)
    else:
        return Clause(toks)

def buildComparison(op, value):
    if isinstance(value, Bind):
        return Comparison(op, bind=value)
    else:
        return Comparison(op, value=value)

def buildQueryComponent(toks):
    node = toks[0]
    comparisons = toks[1:]
    node.set_meta_eval(META_OP.COMP, comparisons)
    return node


s = pp.Suppress
op = pp.Optional
opLn = s(op(pp.LineEnd()))

OPAR = s(pp.Literal('('))
CPAR = s(pp.Literal(')'))
QMARK = pp.Literal('?')

LT = pp.Literal(COMP_REVERSE_LOOKUP[COMP.LT])
GT = pp.Literal(COMP_REVERSE_LOOKUP[COMP.GT])
NE = pp.Literal(COMP_REVERSE_LOOKUP[COMP.NE])
EQ = pp.Literal(COMP_REVERSE_LOOKUP[COMP.EQ])
NOT = pp.Literal('~').setResultsName('NOT')

COMP_OP = pp.Or([LT, GT, NE, EQ])


COMP_Internal = COMP_OP + VALBIND

comparison = OPAR + COMP_Internal \
             + op(pp.OneOrMore(COMMA + COMP_Internal))\
             + CPAR

#core component of a query, a modified param_fact_string
QueryCore = PARAM_CORE + op(comparison)

#Core Query Chain
clause = op(NOT)  + pp.OneOrMore(QueryCore) + s(QMARK)

clauses = clause + pp.ZeroOrMore(COMMA + clause)

#Actions

COMP_Internal.setParseAction(lambda toks: buildComparison(toks[0], toks[1]))
LT.setParseAction(lambda toks: COMP.LT)
GT.setParseAction(lambda toks: COMP.GT)
NE.setParseAction(lambda toks: COMP.NE)
EQ.setParseAction(lambda toks: COMP.EQ)
QueryCore.setParseAction(buildQueryComponent)
#Clause, not negated:
clause.setParseAction(buildClause)


#Main parser:
def parseString(s):
    """ .a.b(>20)!d.$X, ... -> Query """
    data = clauses.parseString(s)[:]
    return Query(*data)
