#https://docs.python.org/3/library/unittest.html
from os.path import splitext, split
from os import listdir
import unittest
import logging as root_logger
logging = root_logger.getLogger(__name__)

import acab
config = acab.setup()

from acab.core.data.values import AcabValue, Sentence

BIND_S = config.prepare("Value.Structure", "BIND")()

def S(*values):
    return Sentence.build(values)

class SentenceTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        LOGLEVEL = root_logger.DEBUG
        LOG_FILE_NAME = "log.{}".format(splitext(split(__file__)[1])[0])
        root_logger.basicConfig(filename=LOG_FILE_NAME, level=LOGLEVEL, filemode='w')

        console = root_logger.StreamHandler()
        console.setLevel(root_logger.INFO)
        root_logger.getLogger('').addHandler(console)
        logging = root_logger.getLogger(__name__)

    def test_construction(self):
        val = S("a","test","value")
        self.assertIsInstance(val, Sentence)
        self.assertIsInstance(val, AcabValue)

    def test_length(self):
        val = S("a","test","value")
        self.assertEqual(len(val), 3)

    def test_eq(self):
        val = S("a","test","value")
        val2 = S("a","test","value")
        self.assertEqual(val, val2)
        self.assertEqual(val, val)

    def test_eq_fail(self):
        val = S("a", "test", "value")
        val2 = S("a", "test", "difference")
        self.assertNotEqual(val, val2)


    def test_build(self):
        val = S("a","test","value")
        val2 = Sentence.build(["a", "test","value"])
        self.assertEqual(val, val2)


    def test_iter(self):
        val = Sentence.build(["a","test","value"])
        for x,y in zip(val, ["a","test","value"]):
            self.assertEqual(x.value, y)

    def test_get_item(self):
        val = Sentence.build(["a","test","value"])
        self.assertIsInstance(val[0], AcabValue)
        self.assertEqual(val[0].value, "a")
        self.assertEqual(val[1].value, "test")
        self.assertEqual(val[2].value, "value")

    def test_copy(self):
        val = Sentence.build(["a","test","value"])
        val2 = val.copy()
        self.assertEqual(val, val2)

    def test_copy_independence(self):
        val = Sentence.build(["a","test","value"])
        val2 = val.copy()
        val.words.append(Sentence.build(["test"])[0])
        self.assertNotEqual(val, val2)

    def test_copy_data_independence(self):
        val = Sentence.build(["a","test","value"])
        val2 = val.copy()
        val.data.update({"blah" : "bloo"})
        self.assertFalse("blah" in val2.data)


    def test_add(self):
        val = Sentence.build(["a","test","value"])
        val2 = Sentence.build(["additional", "sentence"])
        val3 = val.add(val2)

        self.assertIsInstance(val, Sentence)
        self.assertIsInstance(val2, Sentence)
        self.assertIsInstance(val3, Sentence)

        for x,y in zip(val3, ["a","test","value","additional","sentence"]):
            self.assertEqual(x.value, y)

    def test_bind(self):
        val = Sentence.build(["a","test","value"])
        var = Sentence.build(["var"])
        var[0].data.update({BIND_S : True})
        sen = val.add(var)

        bound = sen.bind({"var" : "blah"})

        self.assertFalse(bound[-1].is_var)
        self.assertEqual(bound[-1].value, "blah")

    def test_bind_nop(self):
        val = Sentence.build(["a","test","value"])
        var = Sentence.build(["var"])
        var[0].data.update({BIND_S: True})
        val[2].data.update({BIND_S : True})
        sen = val.add(var)

        bound = sen.bind({"not_var" : "blah"})

        self.assertEqual(sen,bound)
        self.assertTrue(bound[2].is_var)
        self.assertTrue(bound[-1].is_var)
        self.assertEqual(bound[-1].value, "var")



    def test_get_item_slice(self):
        val = Sentence.build(["a","test","value"])
        self.assertIsInstance(val[1:], Sentence)
        for x,y in zip(val[1:], ["test", "value"]):
            self.assertIsInstance(x, AcabValue)
            self.assertEqual(x.value, y)

    def test_attach_statement(self):
        sen = Sentence.build(["a","test","value"])
        to_attach = Sentence.build(["blah","bloo"])

        attached = sen.attach_statement(to_attach)

        self.assertNotEqual(sen, attached)
        self.assertEqual(sen[0:2], attached[0:2])
        self.assertTrue(all([x == y for x,y in zip(attached[-1].words, to_attach.words)]))
        self.assertEqual(attached[-1].name, "value")

    def test_detach_statement(self):
        sen = Sentence.build(["a","test","value"])
        to_attach = Sentence.build(["blah","bloo"])
        attached = sen.attach_statement(to_attach)

        self.assertNotEqual(sen, attached)
        detached, statements = attached.detach_statement()

        self.assertEqual(detached, sen)
        self.assertEqual(statements[0][:], to_attach)

    def test_detach_complete(self):
        sen = Sentence.build(["a","test","value"])
        to_attach = Sentence.build(["blah","bloo"])
        attached_first = sen.attach_statement(to_attach)

        sen2 = Sentence.build(["aweg"])
        second_attach = Sentence.build(["qwer", "qwop"])
        attached_second = sen2.attach_statement(second_attach)

        combined = attached_first.add(attached_second)
        combined_simple = Sentence.build(["a","test","value","aweg"])

        self.assertNotEqual(combined, combined_simple)

        detached, statements = combined.detach_statement()

        self.assertEqual(len(statements), 2)
        self.assertEqual(combined_simple, detached)


    def test_contains(self):
        sen = S("a", "test", "sentence")
        self.assertIn("test", sen)

    def test_contains_fail(self):
        sen = S("a", "test", "sentence")
        self.assertNotIn("blah", sen)

    def test_clear(self):
        sen = S("a", "test", "sentence")
        sen.data["test data"] = True
        sen_cleared = sen.clear()
        self.assertEqual(len(sen_cleared), 0)
        self.assertNotEqual(sen_cleared, sen)
        self.assertIn("test data", sen_cleared.data)

    def test_is_var_fail(self):
        sen = S("a", "test", "sentence")
        self.assertFalse(sen.is_var)

    def test_is_var_fail_2(self):
        sen = S("a", "test", "sentence")
        sen[-1].data.update({BIND_S: True})
        self.assertTrue(sen[-1].is_var)
        self.assertFalse(sen.is_var)

    def test_is_var_pass(self):
        sen = S("single word")
        sen[0].data.update({BIND_S: True})
        self.assertTrue(sen.is_var)
