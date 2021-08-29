import logging as root_logger
import pyparsing as pp
import re

from acab.abstract.config.config import AcabConfig

from acab.abstract.parsing import funcs as Pfunc
from acab.abstract.parsing import consts as PConst
from acab.abstract.parsing.consts import emptyLine, s, op, orm, zrm, N, NG, s_lit, s_key
from acab.abstract.parsing.consts import gap, component_gap, OPAR, CPAR, DBLCOLON, opLn, ln

from acab.abstract.core import default_structure as CDS
from acab.abstract.parsing import default_structure as PDS
from acab.abstract.parsing import default_symbols as PDSYM
from acab.abstract.parsing.consts import TAG

logging = root_logger.getLogger(__name__)

config = AcabConfig.Get()

Fwd_ArgList = pp.Forward()
Fwd_TagList = pp.Forward()

def DELIMIST(expr, delim=None, stopOn=None):
    dlName = f"[{expr} {delim}...]"
    return (expr + pp.ZeroOrMore(delim + expr,
                                 stopOn=stopOn)).setName(dlName)

def PARAM_CORE(mid=None, end=None):
    """ Construct a parameterised core parser
    Can handle wrapped annotations, and a modality as suffix
    """
    if mid is None:
        mid = pp.Empty()
    if end is None:
        end = MODAL(PDS.MODAL)
    else:
        end = pp.Empty()
    parser = N(PDS.NODE, VALBIND) \
        + op(OPAR + NG(PDS.ANNOTATION, mid) + CPAR) + end
    parser.setParseAction(Pfunc.add_annotations)
    return parser




def STATEMENT_CONSTRUCTOR(name_p,
                          body_p,
                          end=None,
                          args=True,
                          single_line=False,
                          parse_fn=None):
    """ Construct a parser for statements of the form:
    a.location: |args| components end
    """
    line_p     = PConst.emptyLine
    line_end_p = PConst.opLn
    end_p      = PConst.END
    arg_p      = pp.empty

    if single_line:
        line_p     = pp.empty
        line_end_p = pp.empty
        end_p      = pp.lineEnd
    elif end is not None:
        end_p = end

    if args:
        arg_p = Fwd_ArgList(PDS.ARG)

    parser = NG(PDS.NAME, name_p) + PConst.COLON + line_end_p \
        + op(arg_p + emptyLine ) \
        + op(Fwd_TagList + emptyLine) \
        + NG(PDS.STATEMENT, body_p) + ln + end_p

    if parse_fn is not None:
        parser.addParseAction(parse_fn)
    else:
        parser.addParseAction(Pfunc.construct_statement)
    return parser


HOTLOAD_VALUES = pp.Forward()


# Basic Parsers
OPERATOR_SUGAR = pp.Word(PDSYM.OPERATOR_SYNTAX)

# TODO use config for type sentences
ATOM           = pp.Word(PDSYM.WORD_COMPONENT)
ATOM.setParseAction(lambda s, l, t: (CDS.TYPE_BOTTOM_NAME, t[0]))

STRING      = pp.dblQuotedString
# Remove quotes from around strings:
STRING.setParseAction(pp.removeQuotes)
STRING.addParseAction(lambda toks: (CDS.STRING_PRIM, toks[0]))

# TODO add re.RegexFlag 's to parser: g and i
REGEX       = pp.Regex(r'/.+?/')
REGEX.setParseAction(lambda s, l, t: (CDS.REGEX_PRIM, re.compile(t[0][1:-1])))


# Generalised modal operator, which is converted to appropriate data later
MODAL      = pp.Word("".join(config.syntax_extension.keys()))
MODAL.setParseAction(lambda s, l, t: config.syntax_extension[t[0]])

BASIC_VALUE = ATOM | STRING | REGEX
BIND        = s_lit(PDSYM.BIND) + ATOM
AT_BIND     = s_lit(PDSYM.AT_BIND) + ATOM

VALBIND = pp.MatchFirst([N(PDS.BIND, BIND),
                         N(PDS.AT_BIND, AT_BIND),
                         N(PDS.VALUE, BASIC_VALUE),
                         N(PDS.VALUE, HOTLOAD_VALUES)])
VALBIND.setParseAction(Pfunc.make_value)

Fwd_ArgList <<= PConst.VBAR + DELIMIST(BIND, delim=PConst.COMMA) + PConst.VBAR

tagName = TAG + ATOM

Fwd_TagList <<= DELIMIST(tagName, delim=PConst.DELIM)(PDS.TAG)

# NAMING
# HOTLOAD_VALUES.setName("HotloadValues")
VALBIND.setName("ValBind")
# ATOM.setName("NameWord")
# STRING.setName("StringWord")
# REGEX.setName("RegexWord")
# BASIC_VALUE.setName("BasicValue")
# BIND.setName("Binding")
# AT_BIND.setName("AtBinding")
# tagName.setName("TagName")
# Fwd_TagList.setName("StatementTagList")
# Fwd_ArgList.setName("StatementArgumentList")
