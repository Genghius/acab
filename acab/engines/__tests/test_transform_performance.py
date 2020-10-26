"""
"""
#https://docs.python.org/3/library/unittest.html
from os.path import splitext, split
from math import isclose
import pyparsing as pp
import unittest
import logging

from acab.config import AcabConfig
AcabConfig.Get().read("acab/util.config")

from acab.abstract.core.value import AcabValue as PV
from acab.abstract.core.sentence import Sentence
from acab.abstract.data.contexts import Contexts

from acab.engines.trie_engine import TrieEngine

from acab.working_memory.trie_wm.parsing import TransformParser as TP
from acab.working_memory.trie_wm.parsing import FactParser as FP

from acab.modules.values import numbers as NS

from acab.abstract.core.type_system import build_simple_type_system

def S(*words):
    return Sentence.build(words)

class TransformTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # setup class
        type_sys = build_simple_type_system()
        AcabValue._set_type_system(type_sys)

    def setUp(self):
        self.e = TrieEngine(modules=["acab.modules.values.numbers",
                                     "acab.modules.operators.standard_operators"])
        self.e.alias_module(S("acab", "modules", "values", "numbers"), S("N"))
        self.e.alias_module(S("acab", "modules", "operators", "standard", "operators"), S("S"))
        self.e.build_DSL()

    def tearDown(self):
        return 1

    #----------
    #use testcase snippets
    def test_run_transform(self):
        stub_ctx = Contexts()
        stub_ctx.append([({'a': PV(2), 'b': PV(4)}, 'blah')])

        stub_transform = TP.parseString(r'λN.AddOp $a 20 -> $y, λN.MulOp $b 2 -> $z')

        # result = self.e._run_transform(stub_ctx[0], stub_transform)
        result = stub_transform(stub_ctx[0], self.e)[0]
        self.assertIsInstance(result, dict)
        self.assertEqual(result['a'].value, 2)
        self.assertEqual(result['b'].value, 4)
        self.assertEqual(result['y'].value, 22)
        self.assertEqual(result['z'].value, 8)

    def test_run_transform_rebind(self):
        stub_ctx = Contexts()
        stub_ctx.append([({'a': PV(2), 'b': PV(8)}, "blah")])

        stub_transform = TP.parseString(r'λN.AddOp $a 20 -> $q, λN.MulOp $b $a -> $w')
        result = stub_transform(stub_ctx[0], self.e)[0]
        self.assertIsInstance(result, dict)
        self.assertEqual(result['a'].value, 2)
        self.assertEqual(result['b'].value, 8)
        self.assertEqual(result['q'].value, 22)
        self.assertEqual(result['w'].value, 16)

    def test_run_unary_transform(self):
        stub_ctx = Contexts()
        stub_ctx.append([({'a': PV(2), 'b': PV(-2), 'c': PV(2.53)}, 'blah')])

        stub_transform = TP.parseString(r'λN.NegOp $a -> $x, λN.NegOp $b -> $y, λN.RoundOp $c -> $z')
        result = stub_transform(stub_ctx[0], self.e)[0]
        self.assertIsInstance(result, dict)
        self.assertEqual(result['a'].value, 2)
        self.assertEqual(result['b'].value, -2)
        self.assertEqual(result['c'].value, 2.53)
        self.assertEqual(result['x'].value, -2)
        self.assertEqual(result['y'].value, 2)
        self.assertEqual(result['z'].value, 2)

    def test_run_unary_transform_rebind(self):
        stub_ctx = Contexts()
        stub_ctx.append([({'a': PV(2), 'b':PV(-2), 'c': PV(2.53)}, 'blah')])

        stub_transform = TP.parseString(r'λN.NegOp $a -> $x, λN.NegOp $b -> $y, λN.RoundOp $c -> $z')
        result = stub_transform(stub_ctx[0], self.e)[0]
        self.assertIsInstance(result, dict)
        self.assertEqual(result['a'].value, 2)
        self.assertEqual(result['b'].value, -2)
        self.assertEqual(result['c'].value, 2.53)
        self.assertEqual(result['x'].value, -2)
        self.assertEqual(result['y'].value, 2)
        self.assertEqual(result['z'].value, 2)

    def test_run_binary_transform(self):
        stub_ctx = Contexts()
        stub_ctx.append([({'a':PV(2),
                          'b':PV(-2),
                          'c':PV(2.53)},
                          "blah")])

        stub_transform = TP.parseString(r'λN.AddOp $a 20 -> $x, λN.SubOp $b 20 -> $y, λN.AddOp $c $x -> $z')
        result = stub_transform(stub_ctx[0], self.e)[0]
        self.assertIsInstance(result, dict)
        self.assertEqual(result['a'].value, 2)
        self.assertEqual(result['b'].value, -2)
        self.assertEqual(result['c'].value, 2.53)
        self.assertEqual(result['x'].value, 22)
        self.assertEqual(result['y'].value, -22)
        self.assertTrue(isclose(result['z'].value, 24.53))

    def test_run_binary_transform_rebind(self):
        stub_ctx = Contexts()
        stub_ctx.append([({'a': PV(2), 'b':PV(-2), 'c': PV(2.53)}, 'blah')])

        stub_transform = TP.parseString(r'λN.AddOp $a 20 -> $x, λN.SubOp $b 20 -> $y, λN.AddOp $c $a -> $z')
        result = stub_transform(stub_ctx[0], self.e)[0]
        self.assertIsInstance(result, dict)
        self.assertEqual(result['a'].value, 2)
        self.assertEqual(result['b'].value, -2)
        self.assertEqual(result['c'].value, 2.53)
        self.assertEqual(result['x'].value, 22)
        self.assertEqual(result['y'].value, -22)
        self.assertTrue(isclose(result['z'].value, 4.53))

    def test_run_ternary_regex_transform(self):
        stub_ctx = Contexts()
        stub_ctx.append([({'a': PV("blah"),
                           'b': PV("aaablah"),
                           'c': PV("awefblahawef"),
                           'd': PV("AAAA")}, "blah")])

        stub_transform = TP.parseString(r'λS.RegexOp $a /blah/ bloo -> $x, λS.RegexOp $b /aaa\w+/ $d -> $y, λS.RegexOp $c /awef(\w+)awef/ $d -> $z')
        result = stub_transform(stub_ctx[0], self.e)[0]
        self.assertIsInstance(result, dict)
        self.assertEqual(result['a'].value, 'blah')
        self.assertEqual(result['b'].value, 'aaablah')
        self.assertEqual(result['c'].value, 'awefblahawef')
        self.assertEqual(result['x'].value, 'bloo')
        self.assertEqual(result['y'].value, 'AAAA')
        self.assertEqual(result['z'].value, 'AAAA')

    def test_run_ternary_regex_rebind(self):
        stub_ctx = Contexts()
        stub_ctx.append([({
            'a': PV("blah"),
            'b': PV("aaablah"),
            'c': PV("awefblahawef"),
            'd':  PV("AAAA")}, "blah")])

        stub_transform = TP.parseString(r'λS.RegexOp $a /blah/ bloo -> $x, λS.RegexOp $b /aaa\w+/ $d -> $y, λS.RegexOp $c /awef(\w+)awef/ "\g<1> \g<1>" -> $z')
        result = stub_transform(stub_ctx[0], self.e)[0]
        self.assertIsInstance(result, dict)
        self.assertEqual(result['a'].value, 'blah')
        self.assertEqual(result['b'].value, 'aaablah')
        self.assertEqual(result['c'].value, 'awefblahawef')
        self.assertEqual(result['x'].value, 'bloo')
        self.assertEqual(result['y'].value, 'AAAA')
        self.assertEqual(result['z'].value, 'blah blah')

    def test_run_unary_format(self):
        stub_ctx = Contexts()
        stub_ctx.append([({'a': PV("AAA"),
                          'b': PV("BBB"),
                          'c': PV("CCC"),
                          'x': PV("{a}"),
                          'y': PV("{a} blah {b}"),
                           'z': PV("{c} {b} {a}")}, "blah")])

        stub_transform = TP.parseString(r'λS.FormatOp $x -> $q, λS.FormatOp $y -> $w, λS.FormatOp $z -> $e')
        result = stub_transform(stub_ctx[0], self.e)[0]
        self.assertIsInstance(result, dict)
        self.assertEqual(result['x'].value, '{a}')
        self.assertEqual(result['y'].value, '{a} blah {b}')
        self.assertEqual(result['z'].value, '{c} {b} {a}')
        self.assertEqual(result['q'].value, 'AAA')
        self.assertEqual(result['w'].value, 'AAA blah BBB')
        self.assertEqual(result['e'].value, 'CCC BBB AAA')

    def test_run_unary_format_rebind(self):
        stub_ctx = Contexts()
        stub_ctx.append([({'a': PV("AAA"),
                          'b': PV("BBB"),
                          'c': PV("CCC"),
                          'x': PV("{a}"),
                          'y': PV("{a} blah {b}"),
                           'z': PV("{c} {b} {a}")}, "blah")])

        stub_transform = TP.parseString(r'λS.FormatOp $x -> $xa, λS.FormatOp $y -> $ya, λS.FormatOp $z -> $za')
        result = stub_transform(stub_ctx[0], self.e)[0]
        self.assertIsInstance(result, dict)
        self.assertEqual(result['xa'].value, 'AAA')
        self.assertEqual(result['ya'].value, 'AAA blah BBB')
        self.assertEqual(result['za'].value, 'CCC BBB AAA')



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
