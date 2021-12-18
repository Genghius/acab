#https://docs.python.org/3/library/unittest.html
from os.path import splitext, split
import unittest
import logging as root_logger
logging = root_logger.getLogger(__name__)

import acab
config = acab.setup()

from acab.interfaces.value import Sentence_i
from acab.core.data.node import AcabNode
from acab.core.data.value import AcabValue

BIND_S = config.prepare("Value.Structure", "BIND")()
AV = AcabValue

class AcabNodeTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        LOGLEVEL = root_logger.DEBUG
        LOG_FILE_NAME = "log.{}".format(splitext(split(__file__)[1])[0])
        root_logger.basicConfig(filename=LOG_FILE_NAME, level=LOGLEVEL, filemode='w')

        console = root_logger.StreamHandler()
        console.setLevel(root_logger.INFO)
        root_logger.getLogger('').addHandler(console)
        logging = root_logger.getLogger(__name__)

    #----------
    def test_root_class_method(self):
        """ Check the Root method constructs a parameterless root node """
        root = AcabNode.Root()
        self.assertIsInstance(root, AcabNode)

    def test_basic_creation(self):
        """ Check the simplest form of node creation wraps a value """
        a_node = AcabNode(AV("test"))
        self.assertIsNotNone(a_node)
        self.assertEqual(a_node.value.name, "test")

    def test_creation_fail_no_value(self):
        """  Check a node has to take an AcabValue """
        with self.assertRaises(TypeError):
            AcabNode("blah")

    def test_creation_fail_internal_node(self):
        """ Check a node value can't be a node itself  """
        node = AcabNode(AV("test"))
        with self.assertRaises(TypeError):
            AcabNode(node)

    def test_length(self):
        """ Check __len__ works, counting children  """
        a_node = AcabNode(AV("test"))
        self.assertEqual(len(a_node), 0)
        a_node.children['a child'] = True
        self.assertEqual(len(a_node), 1)
        a_node.children['another child'] = True
        self.assertEqual(len(a_node), 2)

    def test_bool(self):
        """ Check __bool__ works, testing for children """
        a_node = AcabNode(AV("test"))
        self.assertEqual(bool(a_node), False)
        a_node.children['a child'] = True
        self.assertEqual(bool(a_node), True)
        a_node.children['another child'] = True
        self.assertEqual(bool(a_node), True)

    def test_contains_true(self):
        """ Check nodes can report on whether they have a particular child,
        identified by a string """
        a_node = AcabNode(AV("value"))
        a_node.children['child'] = True
        self.assertTrue(a_node.has_child('child'))

    def test_contains_false(self):
        """
        Check a node can report it doesn't have a child, identified by a string
        """
        a_node = AcabNode(AV("value"))
        self.assertFalse(a_node.has_child('blah'))

    def test_add_child(self):
        """
        Check a node can add a child to itself
        """
        a_val = AV(name='value')
        b_val = AV(name='value2')
        a_node = AcabNode(value=a_val, data={})
        b_node = AcabNode(value=b_val)
        self.assertFalse(bool(a_node))
        self.assertEqual(len(a_node), 0)
        a_node.add_child(b_node)
        self.assertTrue(bool(a_node))
        self.assertEqual(len(a_node), 1)
        self.assertTrue(a_node.has_child('value2'))

    def test_has_child(self):
        """
        Check a node can recognise it has added a child to itself
        """
        a_node = AcabNode(AV('value'))
        b_node = AcabNode(AV('value2'))
        self.assertFalse(bool(a_node))
        self.assertEqual(len(a_node), 0)
        a_node.add_child(b_node)
        self.assertTrue(bool(a_node))
        self.assertEqual(len(a_node), 1)
        self.assertTrue(a_node.has_child(b_node))

    def test_get_child(self):
        """
        Check a node can return a node it has added to itself
        """
        a_node = AcabNode(AV('value'))
        b_node = AcabNode(AV('value2'))
        self.assertFalse(bool(a_node))
        self.assertEqual(len(a_node), 0)
        a_node.add_child(b_node)
        self.assertTrue(bool(a_node))
        self.assertEqual(len(a_node), 1)
        self.assertTrue(a_node.has_child(b_node))
        gotten_node = a_node.get_child(b_node)
        gotten_node_b = a_node.get_child('value2')
        self.assertEqual(gotten_node, b_node)
        self.assertEqual(gotten_node_b, b_node)

    def test_remove_child(self):
        """
        Check a node can remove a child from itself
        """
        a_node = AcabNode(AV('value'))
        b_node = AcabNode(AV('value2'))
        self.assertFalse(bool(a_node))
        self.assertEqual(len(a_node), 0)
        a_node.add_child(b_node)
        self.assertTrue(bool(a_node))
        self.assertEqual(len(a_node), 1)
        self.assertTrue(a_node.has_child(b_node))
        removed = a_node.remove_child(b_node)
        self.assertEqual(len(a_node), 0)
        self.assertFalse(bool(a_node))
        self.assertEqual(removed, b_node)

    def test_clear_children(self):
        """
        Check a node can remove all children from itself
        """
        a_node = AcabNode(AV('value'))
        b_node = AcabNode(AV('value2'))
        c_node = AcabNode(AV('value3'))
        self.assertFalse(bool(a_node))
        self.assertEqual(len(a_node), 0)
        a_node.add_child(b_node)
        a_node.add_child(c_node)
        self.assertEqual(len(a_node),2)
        removed = a_node.clear_children()
        self.assertEqual(len(a_node),0)
        self.assertFalse(bool(a_node))
        self.assertEqual(len(removed), 2)
        self.assertIn(b_node, removed)
        self.assertIn(c_node, removed)


    def test_iter(self):
        """
        Check you can iterate over the children of a node
        """
        node = AcabNode(AV("blah"))
        node.add_child(AcabNode(AV("bloo")))
        node.add_child(AcabNode(AV("blee")))

        for x,y in zip(node, ["bloo", "blee"]):
            self.assertEqual(x.value, y)

    def test_eq_fail(self):
        """
        Check two nodes with equal values aren't the same
        """
        node1 = AcabNode(AV("blah"))
        node2 = AcabNode(AV("blah"))
        self.assertEqual(node1.value, node2.value)
        self.assertFalse(node1, node2)
    def test_eq(self):
        """
        Check a node is equal to itself
        """
        node1 = AcabNode(AV("blah"))
        self.assertFalse(node1, node1)

    def test_name(self):
        """
        Check a node's name is the name of its value
        """
        node = AcabNode(AV("blah"))
        self.assertEqual(node.name, "blah")

    def test_parentage(self):
        """
        Check a node can produce a sentence of it's path from root
        """
        node1 = AcabNode(AV("first"))
        node2 = AcabNode(AV("second"))
        node3 = AcabNode(AV("third"))
        node4 = AcabNode(AV("fourth"))

        node1.add_child(node2).add_child(node3).add_child(node4)

        parentage = node4.parentage
        self.assertIsInstance(parentage, Sentence_i)
        self.assertEqual(parentage[0], "first")
        self.assertEqual(parentage[1], "second")
        self.assertEqual(parentage[2], "third")
        self.assertEqual(parentage[3], "fourth")
