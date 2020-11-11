"""
Pyparsing based parser to turn strings into [FactNode],
capable of parsing  multiple facts
"""
import logging as root_logger
import pyparsing as pp

from acab.abstract.parsing import parsers as PU
from acab.abstract.parsing import funcs as Pfunc
from acab.abstract.parsing.consts import N, NG
from acab.abstract.parsing.consts import NEGATION_SYMBOL, END, opLn, FACT_HEAD, SEN_S
from acab.abstract.parsing.consts import COLLAPSE_CONTEXT, COMMA, DELIM
from acab.abstract.parsing.consts import BIND_S, AT_BIND_S, VALUE_S, OPERATOR_S

from acab.abstract.data.contexts import CTX_OP

from acab.working_memory.trie_wm import util as WMU

logging = root_logger.getLogger(__name__)
# Hotload insertion points:
HOTLOAD_ANNOTATIONS = pp.Forward()
HOTLOAD_QUERY_OP = pp.Forward()

# Basic Sentences without Annotations:
BASIC_SEN = PU.op(NEGATION_SYMBOL) + pp.NotAny(END) \
    + NG(SEN_S, pp.ZeroOrMore(PU.PARAM_CORE()) + PU.PARAM_CORE(end=True))
BASIC_SEN.setParseAction(Pfunc.construct_sentence)

func_headed_sen = pp.Suppress(pp.Literal('λ')) + BASIC_SEN

# Build After comparison operators have been constructed:
op_path = pp.Or([HOTLOAD_QUERY_OP, func_headed_sen])

QUERY_OP_Internal = N(OPERATOR_S, op_path) \
    + N(VALUE_S, PU.PARAM_CORE(end=True))

QUERY_OP_Internal.setParseAction(Pfunc.build_query_component)

COLLAPSE_CONTEXT = COLLAPSE_CONTEXT.copy()
COLLAPSE_CONTEXT.setParseAction(lambda x: (None, CTX_OP.collapse))

query_or_annotation = pp.Or([QUERY_OP_Internal, COLLAPSE_CONTEXT, HOTLOAD_ANNOTATIONS])
constraints = pp.delimitedList(query_or_annotation, delim=COMMA)
constraints.setParseAction(Pfunc.build_constraint_list)

# Core = a. | b! | $a. | $b!....
PARAM_BINDING_CORE = PU.PARAM_CORE(constraints)
PARAM_BINDING_END = PU.PARAM_CORE(constraints, end=True)


SEN_STATEMENT = pp.Forward()

# Sentences with basic sentences as annotations
PARAM_SEN = PU.op(NEGATION_SYMBOL) + pp.NotAny(END) \
    + NG(SEN_S, pp.ZeroOrMore(PARAM_BINDING_CORE) + PARAM_BINDING_END)
PARAM_SEN_PLURAL = pp.delimitedList(PARAM_SEN, delim=DELIM)
PARAM_SEN.setParseAction(Pfunc.construct_sentence)


SEN_STATEMENT_BODY = pp.OneOrMore(pp.Or([SEN_STATEMENT, PARAM_SEN_PLURAL]) + opLn)
# Statement to specify multiple sub sentences
SEN_STATEMENT << PU.STATEMENT_CONSTRUCTOR(FACT_HEAD,
                                          PARAM_SEN,
                                          SEN_STATEMENT_BODY,
                                          parse_fn=Pfunc.construct_multi_sentences)


# Naming
PARAM_BINDING_CORE.setName("ParamBindCore")
PARAM_BINDING_END.setName("ParamBindEnd")
BASIC_SEN.setName("BasicSentence")
PARAM_SEN.setName("ParameterisedSentence")
PARAM_SEN_PLURAL.setName("ParamSentencePlural")
HOTLOAD_ANNOTATIONS.setName("Annotations")
SEN_STATEMENT.setName("SentenceStatement")
HOTLOAD_QUERY_OP.setName("QueryOperators")
QUERY_OP_Internal.setName("Query_Statements")
query_or_annotation.setName("QueryOrAnnotation")
constraints.setName("ConstraintList")

parse_point = PARAM_SEN_PLURAL

# MAIN PARSER:
def parseString(in_string):
    """ str -> [[Value]] """
    return parse_point.parseString(in_string)[:]
