"""
A DSL interface for the system, which

"""
import abc
import collections.abc as cABC
import pyparsing as pp
import traceback
import logging as root_logger
from dataclasses import dataclass, field
from typing import (Any, Callable, ClassVar, Dict, Generic, Iterable, Iterator,
                    List, Mapping, Match, MutableMapping, Optional, Sequence,
                    Set, Tuple, TypeVar, Union, cast)

logging = root_logger.getLogger(__name__)

from acab import types as AT
from acab.core.decorators.dsl import EnsureDSLInitialised
from acab.error.acab_exception import AcabException

Parser           = "pp.ParserElement"
Sentence         = AT.Sentence
Query            = AT.Container
ModuleComponents = AT.ModuleComponents
File             = 'FileObj'

#----------------------------------------
class Bootstrapper_i(cABC.MutableMapping):
    """ A Utility class for registering and retrieving
    interacting parsers """

    @abc.abstractmethod
    def add(self, *inputs: List[Union[str, Parser]]):
        """ for each pair in inputs (a,b):
        register parser b at location a
        """
        pass

    @abc.abstractmethod
    def query(self, *queries: List[str]) -> Parser:
        """ Get all parsers registered at the string locations
        and return an aggregate parser of them
        """
        pass

    def report(self) -> Any:
        """ Return a report on the bootstrap registrations """
        pass

    def __getitem__(self, key):
        return self.query(key)

    def __delitem__(self, key):
        raise NotImplementedError("Bootstrapper's for DSLs should not be able to remove data")

    def __setitem__(self, key, value):
        self.add(key, value)

    def __iter__(self):
        raise NotImplementedError("Iterating through a DSL Bootstrapper doesn't make sense")

#----------------------------------------
class DSL_Fragment_i(cABC.MutableMapping):
    """ """

    def set_word_exclusions(self, *words):
        pass

    def parse_string(self, string):
        """ Takes a String, parses it into Data format """
        raise NotImplementedError()

    def parse_file(self, file):
        raise NotImplementedError()

    @abc.abstractmethod
    def assert_parsers(self, bootstrapper: Bootstrapper_i):
        """
        Assert parsers from this module for integration later
        ie: values.number <= number_parser
        values.time      <= time_parser
        operators.set.add <=  set_add_op
        hotloads.value    <= HOTLOAD_VALUES
        """
        pass

    @abc.abstractmethod
    def query_parsers(self, bootstrapper: Bootstrapper_i):
        """
        Query the now complete parser trie for hotloads
        values.$xs?
        hotloads.values!$p(~= /values/)?

        parser.or($xs) -> $y
        parser.assign $p $y

        """
        pass



    def __delitem__(self, key):
        raise NotImplementedError("DSL Fragment's shouldn't delete parsers")

    def __getitem__(self, key):
        raise NotImplementedError("DSL Fragment's should get parsers using `query_parsers`")

    def __setitem__(self, key, value):
        raise NotImplementedError("DSL Fragment's should add parsers using `assert_parsers`")

    def __iter__(self):
        raise NotImplementedError("Iteration through DSL Fragment's is nonsensical")

    def __len__(self):
        raise NotImplementedError("Length of a DSL Fragment is nonsensical")

#----------------------------------------
@dataclass
class DSLBuilder_i(metaclass=abc.ABCMeta):
    root_fragment         : DSL_Fragment_i = field()

    _bootstrap_parser     : Bootstrapper_i = field(init=False)
    _main_parser          : Parser         = field(init=False)
    _parsers_initialised  : bool           = field(init=False, default=False)
    _loaded_DSL_fragments : Dict[Any, Any] = field(init=False, default_factory=dict)


    def build_DSL(self, modules: List[ModuleComponents]):
        """
        Using currently loaded modules, rebuild the usable DSL parser from fragments
        """
        logging.info("Building DSL")
        self.clear_bootstrap()
        fragments = [y for x in modules for y in x.dsl_fragments]
        self.construct_parsers_from_fragments(fragments)
        self._parsers_initialised = True

    def clear_bootstrap(self):
        self._bootstrap_parser = self._bootstrap_parser.__class__()

    @EnsureDSLInitialised
    def parse(self, s:str) -> List[Sentence]:
        try:
            return self._main_parser.parseString(s, parseAll=True)[:]
        except pp.ParseException as exp:
            logging.warning("\n--------------------\nParse Failure:\n")
            traceback.print_tb(exp.__traceback__)
            logging.warning(f"\n{exp.args[-1]}\n")
            logging.warning(f"Parser: {exp.parserElement}\n")
            logging.warning("Line: {}, Col: {} : {}".format(exp.lineno, exp.col, exp.markInputline()))
            return []

    @EnsureDSLInitialised
    def parseFile(self, f:File) -> List[Sentence]:
        logging.debug(f"Loading File: {f}")
        text = ""
        with open(f, "r") as the_file:
            text = the_file.read()

        logging.info(f"Loading File Text:\n{text}")
        return self.parse(text)

    @abc.abstractmethod
    def construct_parsers_from_fragments(self, fragments: List[DSL_Fragment_i]):
        """ Assemble parsers from the fragments of the wm and loaded modules """
        pass
