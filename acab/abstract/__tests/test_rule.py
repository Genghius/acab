#https://docs.python.org/3/library/unittest.html
from os.path import splitext, split
import unittest
import logging

from acab.config import AcabConfig
AcabConfig.Get().read("acab/util.config")


class RuleTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        return

    def setUp(self):
        return 1

    def tearDown(self):
        return 1

    #----------
    #use testcase snippets

    # TODO: test rule call  with no query/transform/action


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
