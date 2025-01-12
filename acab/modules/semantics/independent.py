import logging as root_logger
from dataclasses import dataclass
from enum import Enum
from typing import TypeVar

import acab.error.semantic_exception as ASErr
from acab.core.config.config import AcabConfig
from acab.core.data.node import AcabNode
from acab.core.data.values import AcabValue, Sentence
from acab.interfaces import semantic as SI

Value = AcabValue
Node  = AcabNode
T     = TypeVar('T')

config       = AcabConfig.Get()
NEGATION_S   = config.prepare("Value.Structure", "NEGATION")()
CONSTRAINT_S = config.prepare("Value.Structure", "CONSTRAINT")()
AT_BIND_S    = config.prepare("Value.Structure", "AT_BIND")()
BIND         = config.prepare("Value.Structure", "BIND")()

CTX_OP = Enum("ctx", "collect_var")
# TODO replace operator with specific modal name
EXOP         = config.prepare("MODAL", "exop")()
DEFAULT_EXOP = config.default(EXOP)
EXOP_enum    = config.prepare(EXOP, as_enum=True)()

logging = root_logger.getLogger(__name__)

Sentence = 'Sentence'
Node     = 'Node'
Engine   = 'Engine'

# Independent Semantics
class BasicNodeSemantics(SI.IndependentSemantics_i):

    def make(self, val, data=None) -> AcabNode:
        return self.up(AcabNode(val), data)

    def up(self, node: AcabNode, data=None) -> AcabNode:
        """ The Most Basic Lift, does nothing """
        return node

    def access(self, node, term, data=None):
        potentials = []
        if term is None:
            potentials += node.children.values()
        elif node.has_child(term):
            potentials.append(node.get_child(term))

        return potentials

    def insert(self, node, new_node, data=None) -> Node:
        assert(isinstance(node, AcabNode))
        assert(isinstance(new_node, AcabNode))
        if new_node in node:
            raise ASErr.AcabSemanticIndependentFailure("Node is already child", (node, new_node))

        return node.add_child(new_node)

    def remove(self, node, to_delete: AcabValue, data=None) -> Node:
        assert(isinstance(node, AcabNode))
        assert(isinstance(to_delete, AcabValue))

        if to_delete not in node:
            raise ASErr.AcabSemanticIndependentFailure("Value not in node", (node, to_delete))

        return node.remove_child(to_delete)

class ExclusionNodeSemantics(SI.IndependentSemantics_i):
    def make(self, val, data=None) -> AcabNode:
        return self.up(AcabNode(val), data)

    def up(self, node: Node, data=None) -> Node:
        # Add an exop if necessary
        if EXOP in node.data:
            return node

        node.data[EXOP] = DEFAULT_EXOP
        word = node.value
        if EXOP in word.data:
            node.data[EXOP] = word.data[EXOP]

        if bool(data) and EXOP in data:
            node.data[EXOP] = data[EXOP]

        return node

    def access(self, node, term, data=None):
        potentials = []
        value = None
        if term is None:
            potentials += node.children.values()
        elif node.has_child(term):
            potentials.append(node.get_child(term))

        # TODO add hook for additional test fragments here?


        if bool(term) and EXOP in term.data and any([x.data[EXOP] != term.data[EXOP] for x in potentials]):
            raise ASErr.AcabSemanticIndependentFailure(f"EXOP MisMatch, expected {term.data[EXOP]}",
                                                       term)


        return potentials

    def insert(self, node, new_node, data=None) -> Node:
        assert(isinstance(node, AcabNode))
        assert(isinstance(new_node, AcabNode))

        if new_node in node:
            raise ASErr.AcabSemanticIndependentFailure("Node is already child", (node, new_node))

        if node.data[EXOP] is EXOP_enum.EX and len(node.children) >= 1:
            node.clear_children()

        result = node.add_child(new_node)
        return result

    def remove(self, node, to_delete, data=None):
        assert(isinstance(node, AcabNode))
        assert(isinstance(to_delete, AcabValue))

        if to_delete not in node:
            raise ASErr.AcabSemanticIndependentFailure("Value not in node", (node, to_delete))

        return node.remove_child(to_delete)

