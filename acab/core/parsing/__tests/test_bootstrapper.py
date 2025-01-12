import logging as root_logger
import unittest
import unittest.mock as mock
from os.path import split, splitext

import pyparsing as pp

logging = root_logger.getLogger(__name__)

import acab

acab.setup()

from acab.core.data.values import AcabValue
from acab.core.parsing.trie_bootstrapper import TrieBootstrapper

class BootstrapParserTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        LOGLEVEL = root_logger.DEBUG
        LOG_FILE_NAME = "log.{}".format(splitext(split(__file__)[1])[0])
        root_logger.basicConfig(filename=LOG_FILE_NAME, level=LOGLEVEL, filemode='w')

        console = root_logger.StreamHandler()
        console.setLevel(root_logger.INFO)
        root_logger.getLogger('').addHandler(console)
        logging = root_logger.getLogger(__name__)

    def setUp(self):
        self.bp = TrieBootstrapper()

    def tearDown(self):
        return 1

    #----------
    #use testcase snippets
    def test_init(self):
        self.assertIsNotNone(self.bp)


    def test_add(self):
        self.assertFalse(bool(self.bp))
        self.bp.add("test", "awef")
        self.assertTrue(bool(self.bp))

    def test_query(self):
        self.assertFalse(bool(self.bp))
        self.bp.add("test", "awef")
        result = self.bp.query("test")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, pp.ParserElement)
        self.assertEqual(str(result), '"awef"')

    def test_query_empty(self):
        self.assertFalse(bool(self.bp))
        result = self.bp.query("*")
        self.assertEqual(result, pp.NoMatch())

    def test_add_two(self):
        self.assertFalse(bool(self.bp))
        self.bp.add("test", "awef")
        self.assertEqual(len(self.bp), 1)
        self.bp.add("other", "blah")
        self.assertEqual(len(self.bp), 2)

    def test_query_two(self):
        self.assertFalse(bool(self.bp))
        self.bp.add("test", "awef")
        self.bp.add("other", "blah")

        result = self.bp.query("*")
        self.assertTrue("awef" in result.exprs)
        self.assertTrue("blah" in result.exprs)

    def test_add_chain(self):
        self.assertFalse(bool(self.bp))
        self.bp.add("test.chain", "awef")
        result = self.bp.query("test.chain")
        self.assertIsNotNone(result)
        self.assertEqual(str(result), '"awef"')

    def test_query_on_chain(self):
        self.assertFalse(bool(self.bp))
        self.bp.add("test.chain", "awef")
        result = self.bp.query("test.*")
        self.assertIsNotNone(result)
        self.assertEqual(str(result), '"awef"')

    def test_query_on_chain_multi_response(self):
        self.assertFalse(bool(self.bp))
        self.bp.add("test.chain", "awef")
        self.bp.add("test.other", "blah")
        result = self.bp.query("test.*")
        self.assertIsNotNone(result)
        self.assertTrue("awef" in result.exprs)
        self.assertTrue("blah" in result.exprs)

    def test_multi_add(self):
        self.assertFalse(bool(self.bp))
        self.bp.add("test.first", "awef",
                 "test.second", "blah")
        result = self.bp.query("test.*")
        self.assertIsNotNone(result)
        self.assertTrue("awef" in result.exprs)
        self.assertTrue("blah" in result.exprs)





