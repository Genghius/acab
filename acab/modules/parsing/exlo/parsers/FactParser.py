"""
Pyparsing based parser to turn strings into [FactNode],
capable of parsing  multiple facts
"""
import logging as root_logger

import pyparsing as pp
from acab.abstract.parsing import funcs as Pfunc
from acab.abstract.parsing import parsers as PU
from acab.abstract.parsing.consts import (COLLAPSE_CONTEXT, COMMA, DELIM, END, emptyLine,
                                          FACT_HEAD, NEGATION, NG, N, op, opLn, zrm, ln)
from acab.abstract.parsing.default_structure import OPERATOR, SEN, VALUE
from acab.modules.parsing.exlo import constructors as PConst

logging = root_logger.getLogger(__name__)
# Hotload insertion points:
HOTLOAD_ANNOTATIONS = pp.Forward()
HOTLOAD_QUERY_OP    = pp.Forward()

# Basic Sentences without Annotations:
BASIC_SEN = ~END + PU.op(NEGATION) \
    + NG(SEN, pp.ZeroOrMore(PU.PARAM_CORE()) + PU.PARAM_CORE(end=True))
BASIC_SEN.setParseAction(Pfunc.construct_sentence)
BASIC_SEN.setName("BasicSentence")

# TODO shift this to config
func_headed_sen = pp.Suppress(pp.Literal('λ')) + BASIC_SEN

# Build After comparison operators have been constructed:
op_path = HOTLOAD_QUERY_OP | func_headed_sen

QUERY_OP_Internal = N(OPERATOR, op_path) \
    + N(VALUE, zrm(BASIC_SEN))

QUERY_OP_Internal.setParseAction(PConst.build_query_component)

COLLAPSE_CONTEXT = COLLAPSE_CONTEXT.copy()
COLLAPSE_CONTEXT.setParseAction(lambda x: CTX_OP.collapse)

query_or_annotation = pp.MatchFirst([QUERY_OP_Internal,
                                     COLLAPSE_CONTEXT,
                                     HOTLOAD_ANNOTATIONS])
constraints = PU.DELIMIST(query_or_annotation, delim=COMMA)
constraints.setParseAction(PConst.build_constraint_list)
constraints.setName("ConstraintList")

# Core = a. | b! | $a. | $b!....
PARAM_BINDING_CORE = PU.PARAM_CORE(constraints)
PARAM_BINDING_END = PU.PARAM_CORE(constraints, end=True)


SEN_STATEMENT = pp.Forward()

# Sentences with basic sentences as annotations
PARAM_SEN = ~END + PU.op(NEGATION) \
    + NG(SEN, pp.ZeroOrMore(PARAM_BINDING_CORE) + PARAM_BINDING_END)
PARAM_SEN.setParseAction(Pfunc.construct_sentence)
PARAM_SEN.setName("ParameterisedSentence")

PARAM_SEN_PLURAL = PU.DELIMIST(PARAM_SEN, delim=DELIM)
PARAM_SEN_PLURAL.setName("Sentences")

SEN_STATEMENT_BODY = PARAM_SEN_PLURAL | SEN_STATEMENT
# Statement to specify multiple sub sentences
SEN_STATEMENT << PU.STATEMENT_CONSTRUCTOR(PARAM_SEN,
                                          SEN_STATEMENT_BODY,
                                          parse_fn=Pfunc.construct_multi_sentences)


# Naming
# PARAM_BINDING_CORE.setName("ParamBindCore")
# PARAM_BINDING_END.setName("ParamBindEnd")
# PARAM_SEN_PLURAL.setName("ParamSentencePlural")
# HOTLOAD_ANNOTATIONS.setName("Annotations")
SEN_STATEMENT.setName("SentenceStatement")
# HOTLOAD_QUERY_OP.setName("QueryOperators")
# QUERY_OP_Internal.setName("Query_Statements")
# query_or_annotation.setName("QueryOrAnnotation")

parse_point = PARAM_SEN_PLURAL

# MAIN PARSER:
def parseString(in_string):
    """ str -> [[Value]] """
    return parse_point.parseString(in_string)[:]
