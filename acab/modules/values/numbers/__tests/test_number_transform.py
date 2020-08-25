#https://docs.python.org/3/library/unittest.html
from os.path import splitext, split
import pyparsing as pp
import unittest
import logging

from acab.config import AcabConfig
AcabConfig.Get().read("acab/util.config")

from acab.abstract.printing import util as PrU
from acab.modules.values.numbers.parsing import NumberParser as NP
from acab.working_memory.trie_wm.parsing import ActionParser as AP
from acab.working_memory.trie_wm.parsing import TransformParser as TP
from acab.working_memory.trie_wm.parsing import FactParser as FP
from acab.working_memory.trie_wm.parsing import QueryParser as QP
from acab.abstract import action
from acab.abstract.query import QueryComponent, QueryOp
from acab.abstract.sentence import Sentence
from acab.abstract import transform
from acab.modules.values import numbers
from acab.working_memory.trie_wm.trie_working_memory import TrieWM
from acab.working_memory.trie_wm import util as KBU


class NumberTransformTests(unittest.TestCase):
    ns = None

    @classmethod
    def setUpClass(cls):
        NumberTransformTests.ns = numbers.MODULE()

    def setUp(self):
        self.trie = TrieWM()
        self.trie.construct_parsers_from_fragments([NumberTransformTests.ns])

    def tearDown(self):
        return 1

    #----------
    #use testcase snippets
    def test_number_parsing(self):
        pass


    def test_basic_transform_core(self):
        result = TP.transform_core.parseString('$x \operator.transform.n_ary.add 20 -> $y')[0]
        self.assertIsInstance(result, transform.TransformComponent)
        self.assertEqual(result.op.pprint(), "operator.transform.n_ary.add")
        self.assertEqual(len(result._params), 2)


    def test_basic_transform_core_rebind(self):
        result = TP.transform_core.parseString('$y \operator.transform.n_ary.mul 20 -> $z')[0]
        self.assertIsInstance(result, transform.TransformComponent)
        self.assertEqual(result.op.pprint(), "operator.transform.n_ary.mul")
        self.assertEqual(result._params[0]._value, "y")
        self.assertTrue(result._params[0].is_var)
        self.assertEqual(result._params[1]._value, 20)
        self.assertIsNotNone(result._rebind)
        self.assertEqual(result._rebind._value, 'z')


    def test_basic_transform(self):
        result = TP.parseString('$x \operator.transform.n_ary.add 20 -> $y, $y \operator.transform.n_ary.add 5 -> $z')
        self.assertIsInstance(result, transform.Transform)
        self.assertEqual(len(result.clauses), 2)


    def test_binary_operator(self):
        result = TP.parseString('$x \operator.transform.n_ary.add 20 -> $y')
        self.assertIsInstance(result, transform.Transform)
        self.assertEqual(len(result.clauses), 1)
        self.assertEqual(result.clauses[0].op.pprint(), "operator.transform.n_ary.add")
        self.assertEqual(result.clauses[0]._params[0]._value, 'x')
        self.assertEqual(result.clauses[0]._params[1]._value, 20)
        self.assertIsNotNone(result.clauses[0]._rebind)


    def test_binary_rebind(self):
        result = TP.parseString('$x \operator.transform.n_ary.add 20 -> $y')
        self.assertIsInstance(result, transform.Transform)
        self.assertEqual(len(result.clauses), 1)
        self.assertEqual(result.clauses[0].op.pprint(), "operator.transform.n_ary.add")
        self.assertEqual(result.clauses[0]._params[0]._value, 'x')
        self.assertEqual(result.clauses[0]._params[1]._value, 20)
        self.assertEqual(result.clauses[0]._rebind._value, 'y')

    def test_unary_round(self):
        result = TP.parseString('\operator.transform.n_ary.round $x -> $y')
        self.assertEqual(result.clauses[0].op.pprint(), 'operator.transform.n_ary.round')

    def test_binary_rand_operator(self):
        result = TP.parseString('$x \operator.transform.n_ary.rand $y -> $z')
        self.assertEqual(len(result.clauses), 1)
        self.assertEqual(result.clauses[0].op.pprint(), 'operator.transform.n_ary.rand')

    def test_unary_operator(self):
        result = TP.parseString(r'\operator.transform.n_ary.neg $x -> $y')
        self.assertIsInstance(result, transform.Transform)
        self.assertEqual(len(result.clauses), 1)
        self.assertEqual(result.clauses[0].op.pprint(), "operator.transform.n_ary.neg")
        self.assertEqual(result.clauses[0]._params[0]._value, "x")
        self.assertIsNotNone(result.clauses[0]._rebind)

    def test_unary_rebind(self):
        result = TP.parseString(r'\operator.transform.n_ary.neg $x -> $y')
        self.assertIsInstance(result, transform.Transform)
        self.assertEqual(len(result.clauses), 1)
        self.assertEqual(result.clauses[0].op.pprint(), "operator.transform.n_ary.neg")
        self.assertEqual(result.clauses[0]._params[0]._value, "x")
        self.assertIsNotNone(result.clauses[0]._rebind)
        self.assertEqual(result.clauses[0]._rebind._value, 'y')



    def test_fact_str_equal(self):
        transforms = ["$x λoperator.transform.n_ary.add 20 -> $y",
                      "$x λoperator.transform.n_ary.add 20 -> $y\n$y λoperator.transform.n_ary.add 5 -> $z",
                      "$x λoperator.transform.n_ary.sub 10 -> $y",
                      "$x λoperator.transform.n_ary.mul 100 -> $y",
                      "$x λoperator.transform.n_ary.add 20 -> $y",
                      "$Blah λoperator.transform.n_ary.add $bloo -> $BLEE",
                      r"λoperator.transform.n_ary.neg $x -> $y",
                      r"λoperator.transform.n_ary.round $x -> $y",
                      r"λoperator.transform.n_ary.neg $x -> $y",
                      r"λoperator.transform.n_ary.round $x -> $y",
                      "$x λoperator.transform.n_ary.regex /blah/ $a -> $z",
                      "$x λoperator.transform.n_ary.regex /aw/ $b -> $blah",
                      "$x λoperator.transform.n_ary.add 2d5 -> $y"
        ]
        for a_string in transforms:
            try:
                parsed = TP.parseString(a_string)
                self.assertEqual(parsed.pprint(container_join="\n").strip(), a_string)
            except pp.ParseException:
                breakpoint()
                print("blah")


if __name__ == "__main__":
    #run python $filename to use this logging setup
    #using python -m unittest $filename won't
    LOGLEVEL = logging.INFO
    logFileName = "log.{}".format(splitext(split(__file__)[1])[0])
    logging.basicConfig(filename=logFileName, level=LOGLEVEL, filemode='w')
    console = logging.StreamHandler()
    console.setLevel(logging.WARN)
    logging.getLogger().addHandler(console)
    unittest.main()
    #reminder: user logging.getLogger().setLevel(logging.NOTSET) for log control
