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
import acab.modules.printing.printers as Printers
from acab.core.config.config import AcabConfig
from acab.core.data.production_abstractions import (ProductionComponent,
                                                        ProductionContainer,
                                                        ProductionOperator)
from acab.core.data.values import AcabStatement, AcabValue, Sentence
from acab.interfaces.printing import PrintSystem_i
from acab.core.printing import wrappers as PW

class BasicPrintFunctionalityTests(unittest.TestCase):

    def test_basic(self):
        pass

    # sem system construction

    # override

    # handler registration

    # lookup

    # check

    # Test wrappers
