#https://docs.python.org/3/library/unittest.html
from os.path import splitext, split
import unittest
import logging

from py_rule.abstract.printing import util as PrU
from py_rule.abstract.value import PyRuleValue, PyRuleStatement
from py_rule.abstract.node import PyRuleNode
from py_rule.abstract.sentence import Sentence
from py_rule.util import AT_BIND_S, BIND_S

class PyRuleValueTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        return

    def setUp(self):
        return 1

    def tearDown(self):
        return 1

    #----------
    #use testcase snippets
    def test_construction(self):
        value = PyRuleValue("test")
        self.assertIsInstance(value, PyRuleValue)

    def test_var_set(self):
        value = PyRuleValue("test")
        var_set = value.var_set
        self.assertIsInstance(var_set, dict)
        self.assertTrue("in" in var_set)
        self.assertTrue("out" in var_set)

    def test_var_set_with_vars(self):
        value = PyRuleValue("test")
        value._vars = ["a","b","c"]
        var_set = value.var_set
        self.assertTrue(all([x in var_set['in'] for x in ["a","b","c"]]))

    def test_attach_statement(self):
        value = PyRuleStatement("test")
        value._tags.add('testval')
        sen = Sentence([PyRuleValue(x) for x in range(5)])
        self.assertEqual(sen[-1].value, 4)
        self.assertIsInstance(sen[-1].value, int)
        copied = sen.attach_statement(value)
        self.assertIsInstance(copied[-1], PyRuleStatement)
        self.assertEqual(copied[-1]._value, "test")
        self.assertEqual(copied[-1].name, 4)

    def test_attach_statement_with_tags(self):
        value = PyRuleStatement("test")
        value._tags.add('testval')
        sen = Sentence([PyRuleValue(x) for x in range(5)])
        self.assertEqual(sen[-1]._value, 4)
        self.assertIsInstance(sen[-1]._value, int)
        copied = sen.attach_statement(value)

        self.assertIsInstance(copied[-1], PyRuleStatement)

    def test_attach_statement_fail(self):
        value = PyRuleValue("test")
        value._tags.add('testval')
        sen = Sentence([PyRuleValue(x) for x in range(5)])
        self.assertEqual(sen[-1]._value, 4)
        self.assertIsInstance(sen[-1]._value, int)

        with self.assertRaises(AssertionError):
            copied = sen.attach_statement(value)


    def test_has_tag(self):
        value = PyRuleValue("test")
        value._tags.update(["a"])
        self.assertTrue(value.has_tag("a"))

    def test_has_tag_fail(self):
        value = PyRuleValue("test")
        value._tags.update(["a"])
        self.assertFalse(value.has_tag("q"))

    def test_has_tag_multi(self):
        value = PyRuleValue("test")
        value._tags.update(["a", "b", "c"])
        self.assertTrue(value.has_tag("a", "b", "c"))

    def test_has_tag_multi_fail(self):
        value = PyRuleValue("test")
        value._tags.update(["a", "b", "c"])
        self.assertFalse(value.has_tag("a", "b", "c", "q"))

    def test_pprint_at_var(self):
        value = PyRuleValue("test")
        value._data.update({BIND_S: AT_BIND_S})
        self.assertTrue(value.is_at_var)
        self.assertEqual(value.pprint(PrU.default_opts()), "@test")

    @unittest.skip('TODO')
    def test_verify(self):
        return


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
