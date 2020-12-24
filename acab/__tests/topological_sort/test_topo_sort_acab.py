#!/usr/bin/env python3

#https://docs.python.org/3/library/unittest.html
# https://docs.python.org/3/library/unittest.mock.html

from os.path import splitext, split

import unittest
import unittest.mock as mock

import logging as root_logger

from acab.abstract.config.config import AcabConfig
config = AcabConfig.Get("acab/abstract/config")


from acab.abstract.core.values import AcabValue, AcabStatement, Sentence
from acab.abstract.core.node import AcabNode
from acab.abstract.core.contexts import Contexts

from acab.modules.structures.trie.trie import Trie
from acab.abstract.core.acab_struct import AcabStruct
from acab.abstract.interfaces.data_interfaces import StructureInterface


from acab.abstract.core import production_abstractions as PA

from acab.modules.operators.query.query_operators import EQ


OPERATOR_TYPE_PRIM_S  = config.value("Type.Primitive", "OPERATOR")
CONTAINER_TYPE_PRIM_S = config.value("Type.Primitive", "CONTAINER")
COMPONENT_TYPE_PRIM_S = config.value("Type.Primitive", "COMPONENT")
ANON_VALUE       = config.value("Symbols", "ANON_VALUE")

# TODO duplicate this, but for failures
class TopologicalOrderedAcabTests(unittest.TestCase):

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


    def setUp(self):
        return 1

    def tearDown(self):
        return 1

    #----------
    # use testcase snippet
    # mock.Mock / MagicMock
    # create_autospec
    # @patch(' ') / with patch.object(...)


    # Configuration
    def test_config_singleton(self):
        """ Check the config obj is a singleton"""
        config = AcabConfig.Get()
        self.assertIsInstance(config, AcabConfig)
        config2 = AcabConfig.Get()
        self.assertIs(config, config2)

    def test_config_value(self):
        """
        Check values can be retrieved
        """
        config = AcabConfig.Get()
        value = config.value("Data", "ROOT")
        self.assertEqual(value, "__root")

    def test_config_prepare(self):
        """ Check values can be prepared """
        config = AcabConfig.Get()
        prep_tuple = config.prepare("Data", "ROOT")
        self.assertIsInstance(prep_tuple, tuple)
        self.assertEqual(len(prep_tuple), 5)

    def test_modal_spec(self):
        """ Check modal fields exist """
        config = AcabConfig.Get()
        self.assertTrue(config.modal_enums)
        self.assertTrue(config.modal_defaults)
        self.assertTrue(config.modal_printing)
        self.assertTrue(config.modal_syntax_lookup)
        # TODO Check values *in* the modal structures

    def test_config_value_missing(self):
        """ Check error is thrown for missing value """
        config = AcabConfig.Get()
        with self.assertRaises(Exception):
            config.value("blah", "bloo")

    def test_config_prepare_missing(self):
        """ Check config errors if you prepare
        a missing value """
        config = AcabConfig.Get()
        with self.assertRaises(Exception):
            config.prepare("blah", "bloo")

    def test_modal_spec_missing(self):
        """
        Check config errors when you try to use missing modal values
        """
        config = AcabConfig.Get()
        with self.assertRaises(Exception):
            config.modal_enums['blah']


    # -> ClosedSet[Values, Node]
    # Creation,
    def test_value_create(self):
        """ Check AcabValues construct well"""
        value = AcabValue("test")
        self.assertIsInstance(value, AcabValue)
        self.assertEqual(value.name, "test")
        self.assertEqual(value.value, "test")
        self.assertEqual(value.type, Sentence.build([config.value("Data", "TYPE_BOTTOM_NAME")]))


    def test_value_safe_make(self):
        """ Check AcabValues don't nest """
        value1 = AcabValue("value")
        self.assertEqual(value1, value1)
        value2 = AcabValue.safe_make(value1)
        self.assertEqual(value1, value2)
        self.assertFalse(isinstance(value2.value, AcabValue))

    def test_value_safe_make_2(self):
        """ Check AcabValues don't nest """
        value1 = "test"
        value2 = AcabValue.safe_make(value1)
        self.assertIsInstance(value1, str)
        self.assertIsInstance(value2, AcabValue)
    def test_sentence_creation(self):
        """ Check Sentences form from multiple Values """
        basic_sentence = Sentence.build(["a", "test", "sentence"])
        self.assertIsInstance(basic_sentence, Sentence)
        self.assertEqual(len(basic_sentence), 3)
        words = basic_sentence.words
        self.assertEqual(len(words), 3)
        self.assertTrue(all([isinstance(x, AcabValue) for x in words]))
        self.assertEqual("test", basic_sentence[1])
    def test_node_creation(self):
        """ Check nodes construct to contain values """
        value = AcabValue("test")
        node = AcabNode(value)
        self.assertEqual(node.value, value)
        self.assertFalse(node.children)


    def test_context_creation(self):
        """ Check Contexts create to hold bindings """
        ctxs = Contexts()
        self.assertIsInstance(ctxs, Contexts)


    # node root, containment, core add, get, remove, has etc
    def test_value_equality(self):
        """ Check two values can equal each other in simple cases """
        value1 = AcabValue("test")
        value2 = AcabValue("test")
        self.assertEqual(value1, value2)

    def test_value_inequality(self):
        value1 = AcabValue("test")
        value2 = AcabValue("blah")
        self.assertNotEqual(value1, value2)


    def test_value_copy(self):
        """ Check a value can be copied, and is independent """
        value1 = AcabValue("test")
        valueCopy = value1.copy()
        self.assertEqual(value1, valueCopy)

    def test_value_bind(self):
        """ Check a value binds appropriately """
        bind_data = {"test" : "blah"}
        value = AcabValue("test", data={config.value("Value.Structure", "BIND"): True})
        bind_result = value.bind(bind_data)
        self.assertIsInstance(bind_result, AcabValue)
        self.assertEqual(bind_result, "blah")


    def test_sentence_containment(self):
        """ Check values can be detected in a sentence """
        sen = Sentence.build(["a", "test", "sentence"])
        value = AcabValue("test")
        self.assertTrue(value in sen)

    def test_sentence_containment_fail(self):
        sen = Sentence.build(["a", "test", "sentence"])
        value = AcabValue("blah")
        self.assertFalse(value in sen)

    def test_sentence_bind(self):
        """ Check sentences can bind sub words to values"""
        bind_data = {"test": "aweg"}
        sen = Sentence.build(["a", AcabValue("test", data={config.value("Value.Structure", "BIND"): True}), "sentence"])
        sen_copy = sen.bind(bind_data)
        self.assertIsInstance(sen_copy, Sentence)
        self.assertNotEqual(sen, sen_copy)

        self.assertFalse("aewf" in sen)
        self.assertTrue("aweg" in sen_copy)



    def test_sentence_attach_statement(self):
        """ Check sentences can attach statements to leaf words """
        master_sen = Sentence.build(["a", "test", "sentence"])
        to_attach = Sentence.build(["another", "blah"])
        to_attach_copy = Sentence.build(["another", "blah"])

        attached = master_sen.attach_statement(to_attach)

        self.assertNotEqual(master_sen, attached)
        self.assertNotEqual(to_attach, attached)

        self.assertEqual(len(master_sen), len(attached))
        self.assertTrue(to_attach_copy in attached)

    def test_node_root(self):
        """ Check a node constructs the most basic root """
        node = AcabNode.Root()
        self.assertIsNotNone(node)
        self.assertIsInstance(node, AcabNode)


    def test_node_has(self):
        node = AcabNode.Root()
        node2 = AcabNode(AcabValue("test"))
        node.children["test"] = node2
        self.assertTrue(node.has_child(node2))
        self.assertTrue(node2 in node)


    def test_node_has_fail(self):
        """ Check node child testing """
        node = AcabNode.Root()
        self.assertFalse(node.has_child(node))
        self.assertFalse(node in node)

    def test_node_add(self):
        """ Check adding children to nodes """
        node = AcabNode.Root()
        node2 = AcabNode(AcabValue("test"))
        node.add_child(node2)
        self.assertTrue(node.has_child(node2))
        self.assertTrue(node2 in node)

    def test_node_get(self):
        """ Check node child retrieval """
        node = AcabNode.Root()
        node2 = AcabNode(AcabValue("test"))
        node.add_child(node2)
        got_back = node.get_child(AcabValue("test"))
        self.assertEqual(node2, got_back)

    def test_node_remove(self):
        node = AcabNode.Root()
        node2 = AcabNode(AcabValue("test"))
        node.add_child(node2)
        self.assertTrue(node2 in node)
        node.remove_child(AcabValue("test"))
        self.assertFalse(node2 in node)




    # -> Abstractions[Structures, Rule]
    # creation
    def test_structure_creation(self):
        """ Check The most Basic Structure: The Trie"""
        the_trie = Trie()
        self.assertIsInstance(the_trie, Trie)
        self.assertIsInstance(the_trie, StructureInterface)

    def test_production_abstraction_operator(self):
        abstract_op = PA.ProductionOperator()
        self.assertIsInstance(abstract_op, PA.ProductionOperator)
        self.assertEqual(abstract_op.name, PA.ProductionOperator.__name__)
        self.assertEqual(abstract_op.type, Sentence.build([OPERATOR_TYPE_PRIM_S]))

    def test_real_operator(self):
        abstract_op = EQ()
        self.assertIsInstance(abstract_op, PA.ProductionOperator)
        self.assertEqual(abstract_op.name, EQ.__name__)
        self.assertEqual(abstract_op.type, Sentence.build([OPERATOR_TYPE_PRIM_S]))

    def test_production_component_construction(self):
        component = PA.ProductionComponent(value=Sentence.build(["test"]))
        self.assertIsInstance(component, PA.ProductionComponent)
        self.assertEqual(component.name, ANON_VALUE)
        self.assertEqual(component.value, Sentence.build(["test"]))
        self.assertEqual(component.type, Sentence.build([COMPONENT_TYPE_PRIM_S]))

    def test_production_component_construction_params(self):
        # TODO add sugared and rebind checks
        component = PA.ProductionComponent(value=Sentence.build(["test"]), params=[Sentence.build(["a", "b", "c"])])
        self.assertIsInstance(component, PA.ProductionComponent)
        self.assertEqual(component.name, ANON_VALUE)
        self.assertEqual(component.value, Sentence.build(["test"]))
        self.assertEqual(len(component.params), 1)
        self.assertEqual(component.params[0], Sentence.build(["a", "b", "c"]))

    def test_production_container_construction(self):
        container = PA.ProductionContainer(value=[])
        self.assertIsInstance(container, PA.ProductionContainer)
        self.assertEqual(container.name, ANON_VALUE)
        self.assertIsInstance(container.value, list)
        self.assertEqual(len(container.value), 0)
        self.assertEqual(container.type, Sentence.build([CONTAINER_TYPE_PRIM_S]))


    def test_production_structure_construction(self):
        structure = PA.ProductionStructure(structure={})
        self.assertIsInstance(structure, PA.ProductionContainer)
        self.assertEqual(structure.name, ANON_VALUE)
        self.assertIsInstance(structure.value, list)
        self.assertEqual(len(structure.value), 0)
        self.assertEqual(structure.type, Sentence.build([CONTAINER_TYPE_PRIM_S]))


    def test_production_component_bind(self):
        value = AcabValue("test", data={config.value("Value.Structure", "BIND"): True})
        component = PA.ProductionComponent(value=Sentence.build(["test"]), params=[value])
        bind_data = {"test" : "blah"}
        bind_result = component.bind(bind_data)
        self.assertNotEqual(component, bind_result)
        self.assertIsInstance(bind_result, PA.ProductionComponent)
        self.assertEqual(bind_result.params[0], "blah")


    def test_production_container_bind(self):
        value = AcabValue("test", data={config.value("Value.Structure", "BIND"): True})
        container = PA.ProductionContainer(value=[], params=[value])
        bind_data = {"test" : "blah"}
        bind_result = container.bind(bind_data)
        self.assertNotEqual(container, bind_result)
        self.assertIsInstance(bind_result, PA.ProductionContainer)
        self.assertEqual(bind_result.params[0], "blah")



    def test_production_structure_bind(self):
        value = AcabValue("test", data={config.value("Value.Structure", "BIND"): True})
        structure = PA.ProductionStructure(structure={}, params=[value])
        bind_data = {"test" : "blah"}
        bind_result = structure.bind(bind_data)
        self.assertNotEqual(structure, bind_result)
        self.assertIsInstance(bind_result, PA.ProductionStructure)
        self.assertEqual(bind_result.params[0], "blah")





    # -> Semantics[ClosedSet, Abstractions]
    def test_node_semantics(self):
        """ Test basic node semantic actions """
        pass

    def test_context_semantics(self):
        """ Check basic context semantics """
        pass

    def test_structure_semantics(self):
        """ Check basic trie structure semantics """
        pass

    def test_struct_semantics_retrieval(self):
        """ Check node semantics can be retrieved for a value """
        pass

    def test_basic_node_semantics(self):
        """ Check basic node semantic actions """
        pass

    # Trie *Implementation*
    def test_trie(self):
        # construction
        pass

    # -> Bootstrap, Working Memory, Engine
    # uses trie
    def test_bootstrap_constructor(self):
        pass

    def test_working_memory_creation(self):
        pass

    def test_engine_constructor(self):
        pass

    def test_bootstrap_add(self):
        pass

    def test_wm_construct_parsers(self):
        pass

    def test_wm_interrupt(self):
        pass

    def test_engine_loading(self):
        pass

    def test_engine_operator_retrieval(self):
        pass

    # -> Reduction
    # to_sentences of everything
    def test_to_sentences(self):
        pass

    # -> Core Input/Output[Actions, Printing, Parsing]
    def test_parse_utils(self):
        pass

    def test_print_utils(self):
        pass

    def test_basic_output_print(self):
        pass

    def test_trie_wm_parsing(self):
        pass

    # assembled semantics

    # -> Modules[Values, Parsers, Semantics]
    # Typing
    # Repl
    # Time
    # Numbers
    # Operators