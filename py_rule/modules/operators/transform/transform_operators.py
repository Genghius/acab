"""
Defintions for Core Transform Operators
"""
from py_rule.abstract.transform import TransformOp
from random import uniform, sample, randint
from math import floor
from re import sub

class RegexOp(TransformOp):
    def __init__(self):
        super().__init__("~=", 3)

    def __call__(self, a, b, replacement, data):
        """ Substitute a pattern with a value from passed in data
        a : the replacement
        b: the pattern

        """
        return sub(b, replacement, a)


class FormatOp(TransformOp):
    def __init__(self):
        super().__init__("~{}", 1)

    def __call__(self, a, data):
        """ Use str.format variant with a data dictionary
        Replaces variables in the string with bound values
        """
        return a.format(**data)

