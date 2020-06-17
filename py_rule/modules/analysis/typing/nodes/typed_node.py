import logging as root_logger

from acab.abstract.node import AcabNode
from acab.modules.analysis.typing.util import TYPE_DEC_S
import acab.error.type_exceptions as te

from acab.modules.analysis.typing.values.type_instance import TypeInstance
logging = root_logger.getLogger(__name__)


class MonoTypedNode(AcabNode):
    """ Base Node for a Type Trie """

    def __init__(self, value, _type=None):
        assert(_type is None or isisntance(_type, TypeInstance))
        super().__init__(value)
        self._type_instance = _type


    @property
    def is_var(self):
        return self.value.is_var
    @property
    def type_instance(self):
        return self._type_instance


    def type_match_wrapper(self, node):
        if TYPE_DEC_S not in node._data:
            return None
        return self.type_match(node._data[TYPE_DEC_S])

    def type_match(self, _type):
        assert(isinstance(_type, TypeInstance))
        result = None
        if self._type_instance is None:
            self._type_instance = _type
            result = self
        elif self._type_instance != _type:
            raise te.TypeConflictException(self._type_instance, _type, self.name)

        return result
