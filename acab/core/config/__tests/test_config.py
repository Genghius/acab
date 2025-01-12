#!/usr/bin/env python3

from typing import List, Set, Dict, Tuple, Optional, Any
from typing import Callable, Iterator, Union, Match
from typing import Mapping, MutableMapping, Sequence, Iterable
from typing import cast, ClassVar, TypeVar, Generic

import logging as root_logger
import unittest
import unittest.mock as mock
from os.path import split, splitext

from acab import setup

from acab.core.config.config import AcabConfig, ConfigSpec
from acab.error.config_exception import AcabConfigException

class ConfigTests(unittest.TestCase):

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

        # Setup default config with default files
        cls.config = setup()

    def setUp(self):
        return 1

    def tearDown(self):
        return 1

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
        spec = config.prepare("Data", "ROOT")
        value = config.value(spec)
        self.assertEqual(value, "__root")


    def test_modal_spec(self):
        """ Check modal fields exist """
        config = AcabConfig.Get()
        self.assertTrue(config.enums)
        self.assertTrue(config.defaults)
        self.assertTrue(config.printing_extension)
        self.assertTrue(config.syntax_extension)
        # TODO Check values *in* the modal structures

    def test_config_prepare(self):
        """ Check values can be prepared """
        config = AcabConfig.Get()
        prep_tuple = config.prepare("Data", "ROOT")
        self.assertIsInstance(prep_tuple, ConfigSpec)

    def test_config_value_missing(self):
        """ Check error is thrown for missing value """
        config = AcabConfig.Get()
        with self.assertRaises(AcabConfigException):
            config.prepare("blah", "bloo")

    def test_config_prepare_missing(self):
        """ Check config errors if you prepare
        a missing value """
        config = AcabConfig.Get()
        with self.assertRaises(AcabConfigException):
            config.prepare("blah", "bloo")

    def test_modal_spec_missing(self):
        """
        Check config errors when you try to use missing modal values
        """
        config = AcabConfig.Get()
        with self.assertRaises(Exception):
            config.enums['blah']


    # -> ClosedSet[Values, Node]
    # Creation,
