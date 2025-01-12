from typing import List, Set, Dict, Tuple, Optional, Any
from typing import Callable, Iterator, Union, Match
from typing import Mapping, MutableMapping, Sequence, Iterable
from typing import cast, ClassVar, TypeVar, Generic

from dataclasses import dataclass, field, InitVar

from .acab_exception import AcabException

@dataclass
class AcabHandlerException(AcabException):

    msg : str = field(init=False, default="Handler Failure: {}")

    def __str__(self):
        return self.msg.format(self.detail)
