"""
EngineBase: The Core Interface and implementation independent code for the production systems

Engine's are the main programming dsl_fragments.
You create one with a working memory, load some modules,
and can then parse and run an agent DSL pipeline.
"""
import logging as root_logger
from dataclasses import dataclass, field
from os.path import abspath, exists, expanduser, split
from re import compile
from typing import (Any, Callable, ClassVar, Dict, Generic, Iterable, Iterator,
                    List, Mapping, Match, MutableMapping, Optional, Sequence,
                    Set, Tuple, TypeVar, Union, cast)

from acab.abstract.config.config import AcabConfig
from acab.abstract.core.production_abstractions import (ProductionContainer,
                                                        ProductionOperator)
from acab.abstract.engine.module_load_interface import ModuleLoaderInterface
from acab.abstract.engine.rewind_interface import RewindEngineInterface
from acab.abstract.engine.util import EnsureDSLInitialised
from acab.abstract.interfaces.dsl_interface import DSLBuilderInterface
from acab.abstract.interfaces.printing_interfaces import PrintSemanticSystem
from acab.abstract.interfaces.semantic_interfaces import SemanticSystem
from acab.error.acab_base_exception import AcabBaseException

logging = root_logger.getLogger(__name__)
config = AcabConfig.Get()

@dataclass
class Engine(RewindEngineInterface, ModuleLoaderInterface, DSLBuilderInterface):
    """ The Abstract class of a production system engine. """

    # TODO add initialisation control of sem system
    _working_memory : SemanticSystem      = field()
    _printer        : PrintSemanticSystem = field()
    init_strs       : List[str]           = field(default_factory=list)
    load_paths      : List[str]           = field(default_factory=list)

    # Blocks engine use until build_DSL has been called:
    initialised     : bool               = field(init=False, default=False)
    _cached_bindings : List[Any]         = field(init=False, default_factory=list)

    def __post_init__(self):
        # initialise modules
        if bool(self.modules):
            self.load_modules(*self.modules)

        # Initialise DSL
        self.build_DSL()

        # Now Load Text files:
        if bool(self.load_paths):
            for x in self.load_paths:
                self.load_file(x)



    @property
    def bindings(self):
        return self._cached_bindings


    @EnsureDSLInitialised
    def load_file(self, filename):
        """ Load a file spec for the facts / rules / layers for this engine """
        return self._load_file(filename)

    def _load_file(self, filename):
        """ Given a filename, read it, and interpret it as an EL DSL string """
        assert(isinstance(filename, str))
        filename = abspath(expanduser(filename))
        logging.info("Loading: {}".format(filename))
        assert exists(filename), filename
        with open(filename) as f:
            # everything should be an assertion
            try:
                assertions = self._main_parser.parseFile(f)
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

    def save_file(self, filename:str, printer:PrintSemanticSystem=None):
        """ Dump the content of the kb to a file to reload later """
        assert(exists(split(abspath(expanduser(filename)))[0]))
        if printer is None:
            printer = self._printer

        as_sentences = self._working_memory.to_sentences()
        as_strings = printer.pprint(*as_sentences)
        with open(abspath(expanduser(filename)), 'w') as f:
            f.write(as_strings)

    @EnsureDSLInitialised
    def insert(self, s: str):
        """ Assert a new fact into the engine """
        data = self._main_parser.parseString(s)
        self._working_memory(data)


    @EnsureDSLInitialised
    def query(self, s: str, ctxs=None, cache=True):
        """ Ask a question of the working memory """
        data = self._query_parser.parseString(s)
        # TODO ensure instruction is a query?
        result = self._working_memory(data, ctxs=ctxs)
        if cache:
            self._cached_bindings = result
        return result

    @EnsureDSLInitialised
    def __call__(self, thing, bindings=None):
        """ Where a thing could be an:
        rule/agenda/layer/pipeline,
        action/query/transform
        """
        result = False
        # if thing is string, query it
        if isinstance(thing, str):
            thing = [thing]

        if isinstance(thing, list) and all([isinstance(x, str) for x in thing]):
            result = [self._working_memory(x) for x in thing]
        else:
            assert(isinstance(thing, ProductionContainer))
            logging.info("Running thing: {}".format(thing))
            # TODO pass instruction to sem system
            result = self._working_memory(thing, ctxs=bindings)

        if not bool(result):
            logging.info("Thing Failed")

        return result

    def to_sentences(self):
        """
        Triggers the working memory to produce a full accounting,
        in canonical style (able to be used by typechecker)
        All statements are output as leaves,
        and all paths with non-leaf statements convert to simple formats
        """
        return self._working_memory.to_sentences()
