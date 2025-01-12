from fractions import Fraction
import logging as root_logger
import pyparsing as pp

from acab.core.parsing import parsers as PU
from acab.core.parsing.consts import SLASH, op, s
from acab.modules.values.numbers import util as NU
from acab.core.config.config import AcabConfig

logging = root_logger.getLogger(__name__)

config = AcabConfig.Get()
DECIMAL_SYMBOL_S = config.prepare("Module.Numbers", "DECIMAL")()
USE_PARSER       = config.prepare("Module.Numbers", "USE_PARSER")()
ALLOW_NEG        = config.prepare("Module.Numbers", "ALLOW_NEG")()


def construct_num(toks):
    num = toks[0]
    mul = 1
    if 'neg' in toks:
        mul = -1
        num = toks[1]

    return (num[0], num[1] * mul)

# This avoids trying to parse rebind arrows as numbers
NEG = pp.Group(pp.Keyword("-", identChars=">")).setResultsName("neg")
DECIMAL_MARK = s(pp.Literal(DECIMAL_SYMBOL_S))

INT = pp.Word(pp.nums)
DEC = INT + DECIMAL_MARK + INT
FRACT = INT + SLASH + INT
# TODO: parse octal and hex numbers?
OCT = pp.empty
HEX = pp.empty

def build_int(s, loc, toks):
    return (NU.INT_t, int(toks[0]))

def build_decimal(s, loc, toks):
    the_num = float("{}.{}".format(toks[0][1],toks[1][1]))
    return (NU.FLOAT_t, the_num)

def build_fraction(s, loc, toks):
    the_num = Fraction(toks[0][1], toks[1][1])
    return (NU.FRACT_t, the_num)


INT.addParseAction(build_int)
DEC.setParseAction(build_decimal)
FRACT.setParseAction(build_fraction)

# INT.addCondition(lambda toks: isinstance(toks[0], tuple))
# DEC.addCondition(lambda toks: isinstance(toks[0], tuple))
# FRACT.addCondition(lambda toks: isinstance(toks[0], tuple))
# NUM = (FRACT | DEC | INT)("num")
# NEG_NUM = op(NEG) + NUM
INT.setName("int")
DEC.setName("decimal")
FRACT.setName("fraction")

parsers = {
    'int'      : INT,
    'decimal'  : DEC,
    'fraction' : FRACT,
    'all'      : FRACT | DEC | INT
    }

chosen_parser = parsers[USE_PARSER]
parse_point = chosen_parser

if ALLOW_NEG:
    NEG_NUM = op(NEG) + chosen_parser.setResultsName("num")
    NEG_NUM.addParseAction(construct_num)
    NEG_NUM.setName("NumP")
    parse_point = NEG_NUM

def parseString(s):
    return parse_point.parseString(s)[0]
