import unittest
import logging
from py_rule import util
from py_rule.abstract.printing import util as PrU
from py_rule.working_memory.trie_wm import util as KBU
from py_rule.working_memory.trie_wm.parsing import RuleParser as RP
from py_rule.working_memory.trie_wm.parsing import FactParser as FP
from py_rule.working_memory.trie_wm.parsing import ActionParser as AP
from py_rule.modules.operators.action import MODULE as ActMod
from py_rule.abstract.rule import Rule
from py_rule.abstract.sentence import Sentence
from py_rule.abstract.query import Query
from py_rule.abstract.bootstrap_parser import BootstrapParser

class Trie_Rule_Parser_Tests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        bp = BootstrapParser()
        am = ActMod()
        am.assert_parsers(bp)
        AP.HOTLOAD_OPERATORS << bp.query("operator.action.*")

    def setUp(self):
            return 1

    def tearDown(self):
            return 1

    #----------
    #use testcase snippets
    def test_init(self):
        self.assertIsNotNone(RP)

    def test_name_empty_rule_parse(self):
        result = RP.parseString("a.rule.x: (::ρ) end")
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0][-1]._value, Rule)
        self.assertEqual(result[0][-1]._value.pprint(leaf=True), "x: (::ρ) end")

    def test_multi_empty_rules(self):
        result = RP.parseString("a.rule.x: (::ρ) end\n\na.second.rule: (::ρ) end")
        self.assertEqual(len(result),2)
        self.assertTrue(all([isinstance(x[-1]._value,Rule) for x in result]))

    def test_rule_with_query(self):
        result = RP.parseString("a.rule.x: (::ρ)\na.b.c?\n\nend")
        self.assertEqual(len(result),1)
        self.assertIsInstance(result[0][-1]._value, Rule)
        self.assertIsNotNone(result[0][-1]._value._query)
        self.assertIsInstance(result[0][-1]._value._query, Query)

    def test_rule_with_multi_clause_query(self):
        result = RP.parseString("a.rule.x: (::ρ)\na.b.c?\na.b.d?\n\nend")
        self.assertEqual(len(result),1)
        self.assertIsInstance(result[0][-1]._value, Rule)
        self.assertIsNotNone(result[0][-1]._value._query)
        self.assertIsInstance(result[0][-1]._value._query, Query)
        self.assertEqual(len(result[0][-1]._value._query), 2)

    def test_rule_with_multi_clauses_in_one_line(self):
        result = RP.parseString("a.rule.x: (::ρ)\na.b.c?, a.b.d?\n\nend")
        self.assertEqual(len(result),1)
        self.assertIsInstance(result[0][-1]._value, Rule)
        self.assertIsNotNone(result[0][-1]._value._query)
        self.assertIsInstance(result[0][-1]._value._query, Query)
        self.assertEqual(len(result[0][-1]._value._query), 2)

    def test_rule_with_binding_query(self):
        result = RP.parseString("a.rule.x: (::ρ)\na.b.$x?\n\nend")
        self.assertEqual(len(result),1)
        self.assertIsInstance(result[0][-1]._value, Rule)
        self.assertIsNotNone(result[0][-1]._value._query)
        self.assertIsInstance(result[0][-1]._value._query, Query)
        self.assertEqual(len(result[0][-1]._value._query), 1)

    def test_rule_with_actions(self):
        result = RP.parseString("a.rule.x: (::ρ)\nActionAdd(a.b.c)\nend")
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0][-1]._value, Rule)
        self.assertIsNone(result[0][-1]._value._query)
        self.assertIsNone(result[0][-1]._value._transform)
        self.assertEqual(len(result[0][-1]._value._action), 1)

    def test_multi_action_rule(self):
        result = RP.parseString("a.rule.x: (::ρ)\nActionAdd(a.b.c)\nActionAdd(~a.b.d)\nend")
        self.assertEqual(len(result[0]), 3)
        self.assertIsInstance(result[0], Sentence)
        self.assertIsInstance(result[0][-1]._value, Rule)
        self.assertIsNone(result[0][-1]._value._query)
        self.assertIsNone(result[0][-1]._value._transform)
        self.assertEqual(len(result[0][-1]._value._action), 2)

    def test_multi_action_single_line_rule(self):
        result = RP.parseString("a.rule.x: (::ρ)\n\nActionAdd(a.b.c), ActionAdd(~a.b.d)\nend")
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0][-1]._value, Rule)
        self.assertIsNone(result[0][-1]._value._query)
        self.assertIsNone(result[0][-1]._value._transform)
        self.assertEqual(len(result[0][-1]._value._action), 2)

    def test_rule_simple_binding_expansion(self):
        bindings = { "x" : FP.parseString('a.b.c')[0] }
        result = RP.parseString("a.rule.x: (::ρ)\n\n$x?\n\nend")[0]
        expanded = result[-1]._value.bind(bindings)
        self.assertEqual(expanded.pprint(),
                         "AnonRule: (::ρ)\n\ta.b.c?\nend")

    def test_rule_tags(self):
        result = RP.parseString('a.test.rule.x: (::ρ)\n\n#blah, #bloo, #blee\n\na.b.c?\n\nActionAdd(a.b.c)\nend')[0]
        self.assertIsInstance(result[-1]._value, Rule)
        self.assertEqual(result.pprint(), "a.test.rule.x: (::ρ)\n\t#blah, #blee, #bloo\n\n\ta.b.c?\n\n\tActionAdd(a.b.c)\nend")
        self.assertTrue(all(x in result[-1]._value._tags for x in ["blah","bloo","blee"]))


if __name__ == "__main__":
      LOGLEVEL = logging.INFO
      logFileName = "log.Trie_Rule_Parser_Tests"
      logging.basicConfig(filename=logFileName, level=LOGLEVEL, filemode='w')
      console = logging.StreamHandler()
      console.setLevel(logging.WARN)
      logging.getLogger().addHandler(console)
      unittest.main()
      #reminder: user logging.getLogger().setLevel(logging.NOTSET) for log control
