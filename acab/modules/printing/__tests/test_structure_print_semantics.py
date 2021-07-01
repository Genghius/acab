#!/usr/bin/env python3


import logging as root_logger
import re
import unittest
import unittest.mock as mock
from os.path import split, splitext

logging = root_logger.getLogger(__name__)
##############################

import acab

config = acab.setup()

import acab.modules.parsing.exlo.parsers.FactParser as FP
import acab.modules.parsing.exlo.parsers.QueryParser as QP
import acab.modules.parsing.exlo.parsers.RuleParser as RP
import acab.modules.printing.printers as Printers
from acab.abstract.config.config import AcabConfig
from acab.abstract.core.production_abstractions import (ProductionComponent,
                                                        ProductionContainer,
                                                        ProductionStructure,
                                                        ProductionOperator)
from acab.abstract.core.values import AcabStatement, AcabValue, Sentence
from acab.abstract.interfaces.printing_interfaces import PrintSemanticSystem

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

class PrintStructureSemanticTests(unittest.TestCase):
    def test_component_simple(self):
        component = ProductionComponent(value=FP.parseString("testop.blah")[0])
        sem_sys = PrintSemanticSystem(handlers=[Printers.BasicSentenceAwarePrinter("_:SENTENCE"),
                                                Printers.ConstraintAwareValuePrinter("_:ATOM"),
                                                Printers.ProductionComponentPrinter("_:COMPONENT"),
                                                Printers.ConfigBackedSymbolPrinter("_:SYMBOL"),
                                                Printers.PrimitiveTypeAwarePrinter("_:NO_MODAL")],
                                      settings={"MODAL": "exop"})

        result = sem_sys.pprint(component)
        self.assertEqual(result, "λtestop.blah")

    def test_component_simple2(self):
        component = ProductionComponent(value=FP.parseString("testop.blah")[0],
                                        params=[FP.parseString("$x")[0][0]])
        sem_sys = PrintSemanticSystem(handlers=[Printers.BasicSentenceAwarePrinter("_:SENTENCE"),
                                                Printers.ConstraintAwareValuePrinter("_:ATOM"),
                                                Printers.ProductionComponentPrinter("_:COMPONENT"),
                                                Printers.ConfigBackedSymbolPrinter("_:SYMBOL"),
                                                Printers.PrimitiveTypeAwarePrinter("_:NO_MODAL")],
                                      settings={"MODAL": "exop"})

        result = sem_sys.pprint(component)
        self.assertEqual(result, "λtestop.blah $x")

    def test_transform_simple(self):
        component = ProductionComponent(value=FP.parseString("testop.blah")[0],
                                        params=[FP.parseString("$x")[0][0]],
                                        rebind=FP.parseString("$y")[0][0])
        sem_sys = PrintSemanticSystem(handlers=[Printers.BasicSentenceAwarePrinter("_:SENTENCE"),
                                                Printers.ConstraintAwareValuePrinter("_:ATOM"),
                                                Printers.ProductionComponentPrinter("_:COMPONENT"),
                                                Printers.ConfigBackedSymbolPrinter("_:SYMBOL"),
                                                Printers.PrimitiveTypeAwarePrinter("_:NO_MODAL")],
                                      settings={"MODAL": "exop"})

        result = sem_sys.pprint(component)
        self.assertEqual(result, "λtestop.blah $x -> $y")

    def test_container(self):
        sem_sys = PrintSemanticSystem(handlers=[Printers.BasicSentenceAwarePrinter("_:SENTENCE"),
                                                Printers.ConstraintAwareValuePrinter("_:ATOM"),
                                                Printers.ProductionComponentPrinter("_:COMPONENT"),
                                                Printers.ConfigBackedSymbolPrinter("_:SYMBOL"),
                                                Printers.ContainerPrinter("_:CONTAINER"),
                                                Printers.PrimitiveTypeAwarePrinter("_:NO_MODAL")],
                                      settings={"MODAL": "exop"})

        # combine some queries together
        queries = QP.parseString("a.b.c?\nd.e(λa.b.q $y).f?\ng.h.i?")
        self.assertIsInstance(queries, ProductionContainer)

        result = sem_sys.pprint(queries)
        self.assertEqual(result, "a.b.c?\nd.e(λa.b.q $y).f?\ng.h.i?")


    def test_rule(self):
        sem_sys = PrintSemanticSystem(handlers=[
            Printers.BasicSentenceAwarePrinter("_:SENTENCE"),
            Printers.ConstraintAwareValuePrinter("_:ATOM"),
            Printers.ProductionComponentPrinter("_:COMPONENT"),
            Printers.ContainerPrinter("_:CONTAINER"),
            Printers.StructurePrinter("_:STRUCTURE"),
            Printers.ConfigBackedSymbolPrinter("_:SYMBOL"),
            Printers.PrimitiveTypeAwarePrinter("_:NO_MODAL")
            ],
                                      settings={"MODAL": "exop"})

        # parse a rule
        rule = RP.parseString("a.test.rule:(::ρ)\na.b.c?\n\nλa.b.c\n\nend")[0]
        self.assertIsInstance(rule, Sentence)
        self.assertIsInstance(rule[-1], ProductionStructure)
        # print
        result = sem_sys.pprint(rule)
        self.assertEqual(result, "a.test.rule:(::ρ)\na.b.c?\n\nλa.b.c\n\nend")

    def test_rule_with_tags(self):
        sem_sys = PrintSemanticSystem(handlers=[
            Printers.BasicSentenceAwarePrinter("_:SENTENCE"),
            Printers.ConstraintAwareValuePrinter("_:ATOM"),
            Printers.ProductionComponentPrinter("_:COMPONENT"),
            Printers.ContainerPrinter("_:CONTAINER"),
            Printers.StructurePrinter("_:STRUCTURE"),
            Printers.ConfigBackedSymbolPrinter("_:SYMBOL"),
            Printers.PrimitiveTypeAwarePrinter("_:NO_MODAL")
            ],
                                      settings={"MODAL": "exop"})

        # parse a rule
        rule = RP.parseString("a.test.rule:(::ρ)\n#test\n#tag\n\na.b.c?\n\nλa.b.c\n\nend")[0]
        self.assertIsInstance(rule, Sentence)
        self.assertIsInstance(rule[-1], ProductionStructure)
        # print
        result = sem_sys.pprint(rule)
        self.assertEqual(result, "a.test.rule:(::ρ)\n#test\n#tag\n\na.b.c?\n\nλa.b.c\n\nend")


    def test_query_statement(self):
        pass

    def test_transform_statement(self):
        pass

    def test_action_statement(self):
        pass
