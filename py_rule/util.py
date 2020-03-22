""" Cross-module utilities for the rule engines """
from enum import Enum
from random import choice
import pyparsing as pp

# Globally constant strings:

# Basic constants
NAME_S       = "name"
BIND_S       = "bind"
AT_BIND_S    = "at_bind_"
CONSTRAINT_S = "constraints"
OPERATOR_S   = "operator"
VALUE_S      = "value"
VALUE_TYPE_S = "value_type"
SEN_S        = "sentence"
NEGATION_S = "negated"
FALLBACK_S = "fallback"

# Core Value Types
FLOAT_S      = "float"
INT_S        = "int"
#Use to signify a decimal, eg: 34d423 = 34.423
DECIMAL_S    = "d"

REGEX_S      = "regex"
STRING_S     = "string"

ACTION_S     = "action"
QUERY_S      = "query"
TRANSFORM_S  = "transform"

# Trie Root Node Name
ROOT_S       = "__root"

# Parser Constants
WORD_COMPONENT_S  = pp.alphas + "_"
OPERATOR_SYNTAX_S = "%^&*_-+={}[]|<>?~§';⊂⊃∨∧⧼⧽¿£ΔΣΩ∩∪√∀∈∃¬∄⟙⟘⊢∴◇□⚬"

# Rule Constants
LAYER_QUERY_RULE_BIND_S = "rule"
RULE_S = "rule"

# Higher Level Structure Heads
MACRO_S     = "μ"
STRUCTURE_S = "σ"
FUNC_S      = "λ"

def build_rebind_dict(formal, usage):
    """ Build a dictionary for action macro expansion,
    to swap internal formal params for provided usage params """
    assert(all([BIND_S in x._data for x in formal]))
    fvals = [x._value for x in formal]
    return dict(zip(fvals, usage))

def has_equivalent_vars_pred(node):
    """ A Predicate to use with Trie.get_nodes
    Finds nodes with multiple vars as children that can be merged """
    if node._op == EX_OP.ROOT:
        return False
    var_children = [x for x in node._children.values() if x._is_var]
    return len(var_children) > 1
