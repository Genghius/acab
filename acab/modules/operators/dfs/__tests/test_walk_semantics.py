#https://docs.python.org/3/library/unittest.html
# https://docs.python.org/3/library/unittest.mock.html

from os.path import splitext, split

import unittest
import unittest.mock as mock

import logging as root_logger
logging = root_logger.getLogger(__name__)


import acab
config = acab.setup()

from acab.modules.operators.dfs.walk_semantics import WalkTrieSemantics
from acab.modules.semantics.basic_system import BasicSemanticSystem
from acab.modules.semantics.independent import ExclusionNodeSemantics
from acab.modules.semantics.abstractions import QueryPlusAbstraction
from acab.modules.engines.configured import exlo
from acab.core.data.production_abstractions import ProductionComponent, ProductionContainer
from acab.core.data.values import Sentence, AcabValue

BIND          = config.prepare("Value.Structure", "BIND")()
QUERY         = config.prepare("Value.Structure", "QUERY")()
SEM_HINT      = config.prepare("Value.Structure", "SEMANTIC_HINT")()
TYPE_INSTANCE = config.prepare("Value.Structure", "TYPE_INSTANCE")()
AT_BIND       = config.prepare("Value.Structure", "AT_BIND")()
default_modules = config.prepare("Module.REPL", "MODULES")().split("\n")

class TestWalkSemantics(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        root_logger.getLogger('').setLevel(root_logger.WARNING)
        LOG_FILE_NAME = "log.{}".format(splitext(split(__file__)[1])[0])

        file_h = root_logger.FileHandler(LOG_FILE_NAME, mode='w')
        file_h.setLevel(root_logger.DEBUG)

        console = root_logger.StreamHandler()
        console.setLevel(root_logger.WARNING)

        logging = root_logger.getLogger(__name__)
        logging.setLevel(root_logger.DEBUG)
        logging.addHandler(console)
        logging.addHandler(file_h)

        cls.eng = exlo()
        cls.eng.load_modules(*default_modules)
        query_plus = QueryPlusAbstraction().as_handler("_:QUERY")
        cls.eng.semantics._register_handler(query_plus)
        walker = WalkTrieSemantics().as_handler("_:WALK")
        cls.eng.semantics._register_handler(walker)

    def tearDown(self):
        self.eng("~a")

    def test_query_walk_only_below_start(self):
        """
        @x ᛦ $y(::target)?
        """
        self.eng("a.b.c.test.sub.blah(::target)")
        self.eng("a.b.d")
        self.eng("a.b.e.something(::target)")

        # Setup a ctx bonud to 'c'
        ctxs       = self.eng("a.b.$x.test?")

        # build a walk instruction
        source_var = AcabValue.safe_make("x", data={BIND: AT_BIND})
        test_var   = AcabValue.safe_make("y", data={BIND: True,
                                                    TYPE_INSTANCE: Sentence.build(["target"]),
                                                    QUERY : True})
        query_sen = Sentence.build([source_var, test_var],
                                   data={SEM_HINT : "_:WALK"})
        query = ProductionContainer(value=[query_sen],
                                    data={SEM_HINT : "_:QUERY"})

        # call walk

        result = self.eng(query, ctxset=ctxs)
        # check results
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].x, "c")
        self.assertEqual(result[0].y, "blah")

    def test_query_walk_multi_start(self):
        """
        @x ᛦ $y(::target)?
        """
        self.eng("a.b.c.test.sub.blah(::target)")
        self.eng("a.b.d")
        self.eng("a.b.e.test.something(::target)")

        # Setup a ctx bonud to 'c'
        ctxs       = self.eng("a.b.$x.test?")

        # build a walk instruction
        source_var = AcabValue.safe_make("x", data={BIND: AT_BIND})
        test_var   = AcabValue.safe_make("y", data={BIND: True,
                                                    TYPE_INSTANCE: Sentence.build(["target"]),
                                                    QUERY : True})
        query_sen = Sentence.build([source_var, test_var],
                                   data={SEM_HINT : "_:WALK"})
        query = ProductionContainer(value=[query_sen],
                                    data={SEM_HINT : "_:QUERY"})

        # call walk
        result = self.eng(query, ctxset=ctxs)
        # check results
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].x, "c")
        self.assertEqual(result[0].y, "blah")
        self.assertEqual(result[1].x, "e")
        self.assertEqual(result[1].y, "something")

    def test_query_walk_no_matches(self):
        """
        @x ᛦ $y(::target)?
        """
        self.eng("a.b.c.test.sub.blah(::nothing)")
        self.eng("a.b.d")
        self.eng("a.b.e.test.something(::nothing)")

        # Setup a ctx bonud to 'c'
        ctxs       = self.eng("a.b.$x.test?")

        # build a walk instruction
        source_var = AcabValue.safe_make("x", data={BIND: AT_BIND})
        test_var   = AcabValue.safe_make("y", data={BIND: True,
                                                    TYPE_INSTANCE: Sentence.build(["target"]),
                                                    QUERY : True})
        query_sen = Sentence.build([source_var, test_var],
                                   data={SEM_HINT : "_:WALK"})
        query = ProductionContainer(value=[query_sen],
                                    data={SEM_HINT : "_:QUERY"})

        # call walk
        result = self.eng(query, ctxset=ctxs)
        # check results
        self.assertEqual(len(result), 0)

    def test_query_walk_from_root(self):
        """
        ᛦ $y(::target)?
        """
        self.eng("a.b.c.test.sub.blah(::target)")
        self.eng("a.b.d")
        self.eng("a.b.e.test.something(::target)")

        # build a walk instruction
        test_var   = AcabValue.safe_make("y", data={BIND: True,
                                                    TYPE_INSTANCE: Sentence.build(["target"]),
                                                    QUERY : True})
        query_sen = Sentence.build([test_var], data={SEM_HINT: "_:WALK"})
        query = ProductionContainer(value=[query_sen],
                                    data={SEM_HINT : "_:QUERY"})

        # call walk
        result = self.eng(query)
        # check results
        self.assertEqual(len(result), 2)

    def test_query_walk_multi_patterns(self):
        """
        @x ᛦ $y(::target) $z(::other)?
        """
        self.eng("a.b.c.test.sub.blah(::target)")
        self.eng("a.b.d")
        self.eng("a.b.e.test.something(::other)")

        # Setup a ctx bonud to 'c'
        ctxs       = self.eng("a.b.$x.test?")

        # build a walk instruction
        source_var = Sentence.build([AcabValue.safe_make("x", data={BIND: AT_BIND})])
        test_var   = AcabValue.safe_make("y", data={BIND: True,
                                                    TYPE_INSTANCE: Sentence.build(["target"]),
                                                    QUERY : True})

        test_var2  = AcabValue.safe_make("z", data={BIND: True,
                                                    TYPE_INSTANCE: Sentence.build(["other"]),
                                                    QUERY : True})

        query_sen = Sentence.build([source_var, test_var, test_var2],
                                   data={SEM_HINT : "_:WALK"})
        query = ProductionContainer(value=[query_sen],
                                    data={SEM_HINT : "_:QUERY"})

        # call walk
        result = self.eng(query, ctxset=ctxs)
        # check results
        self.assertEqual(len(result), 2)
