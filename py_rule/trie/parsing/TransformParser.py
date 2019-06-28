""" Trie-based parser for the transform component of rules """
import logging as root_logger
import pyparsing as pp
import IPython
import py_rule.utils as util
from py_rule.abstract.transforms import TROP, SelectionTransform, OperatorTransform, Transform, TransformOp
from .FactParser import COMMA, PARAM_CORE, N, param_fact_string, NG, VALBIND
from .QueryParser import OPAR, CPAR, REGEX

logging = root_logger.getLogger(__name__)
pp.ParserElement.setDefaultWhitespaceChars(' \t\r')
#utils
s = pp.Suppress
op = pp.Optional
opLn = s(op(pp.LineEnd()))
ARROW = s(pp.Literal('->'))

#Builders:
def buildBinaryTransformComponent(toks):
    return OperatorTransform(toks.op, (toks.left, toks.right))

def buildUnaryTransformComponent(toks):
    return OperatorTransform(toks.op, tuple([toks.value]))

def buildTernaryTransformComponent(toks):
    return OperatorTransform(toks.op, (toks.source, toks.regex, toks.replace))

def buildSelection(toks):
    bound1 = toks.source
    bound2 = toks.sub
    return SelectionTransform(bound1, bound2)

def addRebind(toks):
    if 'target' in toks:
        toks.transform[0].set_rebind(toks.target[0])
    return toks.transform[0]


SUB = s(pp.Literal('-'))

#Transform Operators
BINARY_TRANS_OP = pp.Or([pp.Literal(k) for k,v in TransformOp.op_list.items() if 2 in v])
UNARY_TRANS_OP = pp.Or([pp.Literal(k) for k,v in TransformOp.op_list.items() if 1 in v])
TERNARY_TRANS_OP = pp.Or([pp.Literal(k) for k,v in TransformOp.op_list.items() if 3 in v])

rebind = ARROW + VALBIND
selAll = pp.Literal('_')

select = s(pp.Literal('select')) + N("source", param_fact_string)\
    + SUB + N("sub", param_fact_string)


#transform: ( bind op val|bind -> bind)
unary_transform_core = N("op", UNARY_TRANS_OP) + N("value", VALBIND)
binary_transform_core = N("left", VALBIND) + N("op", BINARY_TRANS_OP) + N("right", VALBIND)
ternary_transform_core = N("source", VALBIND) + N("op", TERNARY_TRANS_OP) + N("regex", REGEX) + N("replace", VALBIND)

transform_core = NG("transform", pp.Or([binary_transform_core,
                                        ternary_transform_core,
                                        unary_transform_core])) \
                + op(N("target", rebind))

transforms = pp.Or([select, transform_core]) \
             + pp.ZeroOrMore(COMMA + transform_core)

#Actions
binary_transform_core.setParseAction(buildBinaryTransformComponent)
unary_transform_core.setParseAction(buildUnaryTransformComponent)
ternary_transform_core.setParseAction(buildTernaryTransformComponent)
select.setParseAction(buildSelection)

transform_core.setParseAction(addRebind)
transforms.setParseAction(lambda toks: Transform(toks[:]))

def parseString(in_string):
    return transforms.parseString(in_string)[0]
