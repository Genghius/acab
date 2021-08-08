import abc
import logging as root_logger
from dataclasses import dataclass, field
from os.path import abspath, exists, expanduser, split
from typing import (Any, Callable, ClassVar, Dict, Generic, Iterable, Iterator,
                    List, Mapping, Match, MutableMapping, Optional, Sequence,
                    Set, Tuple, TypeVar, Union, cast)

logging = root_logger.getLogger(__name__)

from acab.abstract.interfaces.context import ContextContainer_i
from acab.abstract.interfaces.dsl import DSL_Fragment_i, DSLBuilder_i
from acab.abstract.interfaces.module_loader import ModuleLoader_i
from acab.abstract.interfaces.printing import PrintSystem_i
from acab.abstract.interfaces.semantic import SemanticSystem_i

# TODO add 'Tick' functionality
ModuleComponents = "ModuleComponents"

# Decorator for Engine:
def EnsureInitialised(method):
    def fn(self, *args, **kwargs):
        if not self.initialised:
            raise AcabBaseException("DSL Not Initialised")

        return method(self, *args, **kwargs)

    fn.__name__ = method.__name__
    return fn

@dataclass
class AcabEngine_i(metaclass=abc.ABCMeta):

    # Root components to extend
    parser         : DSL_Fragment_i   = field()
    semantics      : SemanticSystem_i = field()
    printer        : PrintSystem_i    = field()

    # Modules to load
    modules        : List[str]        = field(default_factory=list)
    # Files to load
    load_paths     : List[str]        = field(default_factory=list)
    init_strs      : List[str]        = field(default_factory=list)

    initialised    : bool             = field(init=False, default=False)
    # Abstract fields, need to be instantiated:
    _dsl_builder   : DSLBuilder_i     = field(init=False)
    _module_loader : ModuleLoader_i   = field(init=False)

    @EnsureInitialised
    def load_file(self, filename) -> bool:
        """ Given a filename, read it, and interpret it as an EL DSL string """
        assert(isinstance(filename, str))
        filename = abspath(expanduser(filename))
        logging.info("Loading: {}".format(filename))
        assert exists(filename), filename
        with open(filename) as f:
            # everything should be an assertion
            try:
                assertions = self._dsl_builder.parseFile(f)
            except pp.ParseException as exp:
                print("-----")
                print(str(exp))
                print(exp.markInputline())
                print("File Not Asserted into WM")
                return False

            # Assert facts:
            for x in assertions:
                logging.info("File load assertions: {}".format(x))
                self.add(x)

        return True

    def save_file(self, filename:str, printer:PrintSystem_i=None):
        """ Dump the content of the kb to a file to reload later """
        assert(exists(split(abspath(expanduser(filename)))[0]))
        if printer is None:
            printer = self.printer

        as_sentences = self.semantics.to_sentences()
        if not bool(as_sentences[0]):
            logging.info("Nothing to print")
            return

        as_strings = printer.pprint(*as_sentences)

        with open(abspath(expanduser(filename)), 'w') as f:
            f.write(as_strings)



    def to_sentences(self):
        """
        Triggers the working memory to produce a full accounting,
        in canonical style (able to be used by typechecker)
        All statements are output as leaves,
        and all paths with non-leaf statements convert to simple formats
        """
        return self.semantics.to_sentences()

    def pprint(self) -> str:
        sens = self.to_sentences()
        return self.printer.pprint(*sens)

    def load_modules(self, *modules: List[str]) -> List[ModuleComponents]:
        return self._module_loader.load_modules(*modules)
    @abc.abstractmethod
    def __call__(self, thing, bindings=None) -> ContextContainer_i:
        pass