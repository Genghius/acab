from py_rule.util import FUNC_S
from py_rule.abstract.printing import util as PrU
from py_rule.util import VALUE_TYPE_S, NAME_S

from .type_definition import TypeDefinition
from .type_instance import TypeInstance
from .util import OP_DEF_S, TYPE_DEF_S


class OperatorDefinition(TypeDefinition):
    """ Defines the type signature of an operator"""

    def __init__(self, structure, sugar_syntax=None):
        """ The name of an operator and its type signature,
        with the binding to a ProductionOperator that is
        syntax sugared, and its inline place"""
        # eg: operator.+.$x(::num).$y(::num).$z(::num).num_plus
        if not isinstance(structure, list):
            structure = [structure]
        super().__init__(structure, type_str=OP_DEF_S)
        self._func_name = sugar_syntax

    def pprint(self, **kwargs):
        return PrU.print_statement(self, is_structured=True, **kwargs)

    def build_type_declaration(self):
        just_path = self.path.copy()
        return TypeInstance(just_path, args=self.vars)
