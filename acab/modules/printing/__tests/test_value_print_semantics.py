#!/usr/bin/env python3

import logging as root_logger
import re
import unittest
import unittest.mock as mock
from os.path import split, splitext

import pyparsing as pp

logging = root_logger.getLogger(__name__)
##############################

import acab

config = acab.setup()


import acab.modules.parsing.exlo.parsers.ActionParser as AP
import acab.modules.parsing.exlo.parsers.FactParser as FP
import acab.modules.parsing.exlo.parsers.QueryParser as QP
import acab.modules.parsing.exlo.parsers.RuleParser as RP
import acab.modules.parsing.exlo.parsers.TransformParser as TP
import acab.modules.printing.printers as Printers
from acab.core.config.config import AcabConfig
from acab.core.data.production_abstractions import (ProductionComponent,
                                                        ProductionContainer,
                                                        ProductionOperator)
from acab.core.data.values import AcabStatement, AcabValue, Sentence
from acab.interfaces.handler_system import Handler
from acab.modules.printing.basic_printer import BasicPrinter

NEGATION_S        = config.prepare("Value.Structure", "NEGATION")()
QUERY_S           = config.prepare("Value.Structure", "QUERY")()
BIND_S            = config.prepare("Value.Structure", "BIND")()
AT_BIND_S         = config.prepare("Value.Structure", "AT_BIND")()
TYPE_INSTANCE_S   = config.prepare("Value.Structure", "TYPE_INSTANCE")()

NEGATION_SYMBOL_S = config.prepare("Symbols", "NEGATION")()
ANON_VALUE_S      = config.prepare("Symbols", "ANON_VALUE")()
FALLBACK_MODAL_S  = config.prepare("Symbols", "FALLBACK_MODAL", actions=[config.actions_e.STRIPQUOTE])()
QUERY_SYMBOL_S    = config.prepare("Symbols", "QUERY")()

SEN_JOIN_S        = config.prepare("Print.Patterns", "SEN_JOIN", actions=[AcabConfig.actions_e.STRIPQUOTE])()

STR_PRIM_S        = Sentence.build([config.prepare("Type.Primitive", "STRING")()])
REGEX_PRIM_S      = Sentence.build([config.prepare("Type.Primitive", "REGEX")()])

EXOP              = config.prepare("exop", as_enum=True)()
DOT_E             = EXOP.DOT


class PrintValueSemanticTests(unittest.TestCase):
    """ Test the basic Print Semantics using default settings """

    @classmethod
    def setUpClass(cls):
        LOGLEVEL = root_logger.DEBUG
        LOG_FILE_NAME = "log.{}".format(splitext(split(__file__)[1])[0])
        root_logger.basicConfig(filename=LOG_FILE_NAME, level=LOGLEVEL, filemode='w')

        console = root_logger.StreamHandler()
        console.setLevel(root_logger.INFO)
        root_logger.getLogger('').addHandler(console)
        logging = root_logger.getLogger(__name__)

        FP.HOTLOAD_ANNOTATIONS << pp.MatchFirst([QP.word_query_constraint])

        FP.HOTLOAD_SEN_ENDS << pp.MatchFirst([QP.query_sen_end,
                                              QP.query_statement,
                                              TP.transform_statement,
                                              AP.action_definition])

    def test_initial(self):
        sem_sys = BasicPrinter(init_handlers=[Printers.AtomicPrinter().as_handler("_:ATOM"),
                                              Printers.ConfigBackedSymbolPrinter().as_handler("_:SYMBOL"),
                                              Printers.SimpleTypePrinter().as_handler("_:TYPE_INSTANCE"),
                                              Printers.ModalPrinter().as_handler("_:MODAL")])
        result = sem_sys.pprint(AcabValue("Test"))
        self.assertEqual(result, "Test")

    def test_multiple(self):
        sem_sys = BasicPrinter(init_handlers=[Printers.AtomicPrinter().as_handler("_:ATOM"),
                                              Printers.SimpleTypePrinter().as_handler("_:TYPE_INSTANCE"),
                                              Printers.ConfigBackedSymbolPrinter().as_handler("_:SYMBOL"),
                                              Printers.ModalPrinter().as_handler("_:MODAL")])
        result = sem_sys.pprint(AcabValue("a"), AcabValue("b"), AcabValue("c"))
        self.assertEqual(result, "a\nb\nc")


    def test_string_wrap(self):
        sem_sys = BasicPrinter(init_handlers=[Printers.PrimitiveTypeAwarePrinter().as_handler("_:ATOM"),
                                              Printers.SimpleTypePrinter().as_handler("_:TYPE_INSTANCE"),
                                              Printers.ConfigBackedSymbolPrinter().as_handler("_:SYMBOL"),
                                              Printers.ModalPrinter().as_handler("_:MODAL")])

        test = AcabValue(name="blah", data={TYPE_INSTANCE_S: STR_PRIM_S})
        result = sem_sys.pprint(test)
        self.assertEqual(result, '"blah"')

    def test_regex_wrap(self):
        sem_sys = BasicPrinter(init_handlers=[Printers.PrimitiveTypeAwarePrinter().as_handler("_:ATOM"),
                                              Printers.SimpleTypePrinter().as_handler("_:TYPE_INSTANCE"),
                                              Printers.ConfigBackedSymbolPrinter().as_handler("_:SYMBOL"),
                                              Printers.ModalPrinter().as_handler("_:MODAL")])
        test = AcabValue(value=re.compile("blah"), data={TYPE_INSTANCE_S: REGEX_PRIM_S})
        result = sem_sys.pprint(test)
        self.assertEqual(result, r'/blah/')

    def test_var_wrap(self):
        sem_sys = BasicPrinter(init_handlers=[Printers.PrimitiveTypeAwarePrinter().as_handler("_:ATOM"),
                                              Printers.SimpleTypePrinter().as_handler("_:TYPE_INSTANCE"),
                                              Printers.ConfigBackedSymbolPrinter().as_handler("_:SYMBOL"),
                                              Printers.ModalPrinter().as_handler("_:MODAL")])
        test = AcabValue("blah", data={BIND_S : True})
        result = sem_sys.pprint(test)
        self.assertEqual(result, r'$blah')

    def test_pprint_at_var(self):
        sem_sys = BasicPrinter(init_handlers=[Printers.PrimitiveTypeAwarePrinter().as_handler("_:ATOM"),
                                              Printers.SimpleTypePrinter().as_handler("_:TYPE_INSTANCE"),
                                              Printers.ConfigBackedSymbolPrinter().as_handler("_:SYMBOL"),
                                              Printers.ModalPrinter().as_handler("_:MODAL")])
        value = AcabValue("test")
        value.data.update({BIND_S: AT_BIND_S})
        result = sem_sys.pprint(value)
        self.assertEqual(result, r'@test')

    def test_modal_print(self):
        sem_sys = BasicPrinter(init_handlers=[Printers.ModalAwarePrinter().as_handler("_:ATOM"),
                                              Printers.ConfigBackedSymbolPrinter().as_handler("_:SYMBOL"),
                                              Printers.SimpleTypePrinter().as_handler("_:TYPE_INSTANCE"),
                                              Printers.ModalPrinter().as_handler("_:MODAL")
                                              ],
                               settings={"MODAL" : "exop"})
        test = AcabValue(value="blah",
                         data={'exop': config.default("exop")})
        result = sem_sys.pprint(test)
        self.assertEqual(result, r'blah.')

    def test_modal_print2(self):
        sem_sys = BasicPrinter(init_handlers=[Printers.ModalAwarePrinter().as_handler("_:ATOM"),
                                              Printers.SimpleTypePrinter().as_handler("_:TYPE_INSTANCE"),
                                              Printers.ConfigBackedSymbolPrinter().as_handler("_:SYMBOL"),
                                              Printers.ModalPrinter().as_handler("_:MODAL")
                                              ],
                              settings={"MODAL" : "exop"})

        test = AcabValue(value="blah",
                         data={'exop': EXOP.EX})
        result = sem_sys.pprint(test)
        self.assertEqual(result, r'blah!')

    def test_modal_print_override(self):
        sem_sys = BasicPrinter(init_handlers=[Printers.ModalAwarePrinter().as_handler("_:ATOM"),
                                              Printers.SimpleTypePrinter().as_handler("_:TYPE_INSTANCE"),
                                              Printers.ConfigBackedSymbolPrinter(overrides={DOT_E : "^"}).as_handler("_:SYMBOL"),
                                              Printers.ModalPrinter().as_handler("_:MODAL")
                                              ],
                              settings={"MODAL": "exop"})
        test = AcabValue(value="blah",
                         data={'exop': DOT_E})
        result = sem_sys.pprint(test)
        self.assertEqual(result, r'blah^')

    def test_symbol_override(self):
        sem_sys = BasicPrinter(init_handlers=[Printers.ModalAwarePrinter().as_handler("_:ATOM"),
                                              Printers.SimpleTypePrinter().as_handler("_:TYPE_INSTANCE"),
                                              Printers.ConfigBackedSymbolPrinter(overrides={config.prepare("Symbols", "BIND") : "%"}).as_handler("_:SYMBOL"),
                                              Printers.NoOpPrinter().as_handler("_:MODAL")
                                              ])

        test = AcabValue(value="blah",
                         data={BIND_S : True})
        result = sem_sys.pprint(test)
        self.assertEqual(result, r'%blah')

    def test_value_uuid(self):
        val = AcabValue("test")
        sem_sys = BasicPrinter(init_handlers=[Printers.UUIDAwarePrinter().as_handler("_:ATOM")])
        result = sem_sys.pprint(val)
        self.assertEqual(result, "({} : {})".format(val.uuid, val.name))


    def test_constraints(self):
        sem_sys = BasicPrinter(init_handlers=[
            Printers.AnnotationAwareValuePrinter().as_handler("_:ATOM"),
            Printers.AnnotationPrinter().as_handler("_:ANNOTATIONS"),
            Printers.BasicSentenceAwarePrinter().as_handler("_:SENTENCE"),
            Printers.ConfigBackedSymbolPrinter().as_handler("_:SYMBOL"),
            Printers.ConstraintPrinter().as_handler("_:CONSTRAINT"),
            Printers.ModalPrinter().as_handler("_:MODAL"),
            Printers.ProductionComponentPrinter().as_handler("_:COMPONENT"),
            Printers.SimpleTypePrinter().as_handler("_:TYPE_INSTANCE"),
                                              ],
                              settings={"MODAL": "exop"})
        value = FP.parseString("con.test(λa.test.op $x)")[0][-1]
        result = sem_sys.pprint(value)
        self.assertEqual(result, "test(λa.test.op $x).")

    def test_constraints_multi_var(self):
        sem_sys = BasicPrinter(init_handlers=[Printers.BasicSentenceAwarePrinter().as_handler("_:SENTENCE"),
                                              Printers.SimpleTypePrinter().as_handler("_:TYPE_INSTANCE"),
                                              Printers.AnnotationAwareValuePrinter().as_handler("_:ATOM"),
                                              Printers.ProductionComponentPrinter().as_handler("_:COMPONENT"),
                                              Printers.ModalPrinter().as_handler("_:MODAL"),
                                              Printers.ConfigBackedSymbolPrinter().as_handler("_:SYMBOL"),
                                              Printers.AnnotationPrinter().as_handler("_:ANNOTATIONS")],
                              settings={"MODAL": "exop"})
        value = FP.parseString("con.test(λa.test.op $x $y)")[0][-1]
        result = sem_sys.pprint(value)
        self.assertEqual(result, "test(λa.test.op $x $y).")
