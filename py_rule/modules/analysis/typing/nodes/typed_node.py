import logging as root_logger

from py_rule.abstract.trie.nodes.trie_node import TrieNode
from py_rule.modules.analysis.typing.util import TYPE_DEC_S
import py_rule.error.type_exceptions as te

logging = root_logger.getLogger(__name__)


class MonoTypedNode(TrieNode):
    """ Base Node for a Type Trie """

    def __init__(self, value):
        super().__init__(value)
        self._type = None

    def type_match_wrapper(self, node):
        if TYPE_DEC_S not in node._data:
            return None
        return self.type_match(node._data[TYPE_DEC_S])

    def type_match(self, _type):
        if self._type is None:
            self._type = _type
            return self
        elif self._type != _type:
            raise te.TypeConflictException(self._type, _type, self._value)
        return None
