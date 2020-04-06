"""
Actions: Describes the *ENGINE AGNOSTIC* basic actions that a working memory can
perform, along with associated enums, and IR data structures
"""
import logging as root_logger

from py_rule import util
from py_rule.abstract.node import PyRuleNode
from py_rule.abstract.sentence import Sentence
from py_rule.abstract.printing import util as PrU

from . import production_operator as PO

logging = root_logger.getLogger(__name__)


# Action function template:
class ActionOp(PO.ProductionOperator):
    """ Superclass of all Actions.
    Instantiation of subclasses auto-registers
    the action into ActionOp.op_list with an operator string
    """
    op_list = {}

    def __init__(self, num_params=2, infix=False):
        # Registers self with class name,
        # DSL later binds to an operator
        super().__init__(num_params=num_params, infix=False)

        if self.op_str not in ActionOp.op_list:
            ActionOp.op_list[self.op_str] = self

    def __call__(self, engine, params):
        raise NotImplementedError()



class ActionComponent(PO.ProductionComponent):
    """ The Core Action Class, holds an operator,
    and a list of values """


    def __init__(self, op_str, params):
        """ Create an action with an operator and values """
        assert all([isinstance(x, Sentence) for x in params]), params
        super(ActionComponent, self).__init__(op_str, params)

    def __call__(self, engine, data):
        # lookup op
        assert(self.op in ActionOp.op_list)
        op_func = ActionOp.op_list[self.op]
        # get values from data
        values = self.get_values(data)
        # perform action op with data
        op_func(engine, values)

    def __refine_op_func(self, op_str):
        """ Replace the current op func set with a specific
        op func, used for type refinement """
        assert(op_str in ActionOp.op_list)
        self._value = op_str

    def verify(self):
        """ Check the Action is using a valid operator (ACT enum) """
        if self.op not in ActionOp.op_list.keys():
            raise AttributeError("Unrecognised Action: {}".format(self.op))

    def get_values(self, data):
        """ Output a list of bindings from this action """
        output = []
        for x in self._vars:
            if isinstance(x, Sentence):
                output.append(x.expand_bindings(data))
            elif isinstance(x, list):  # and all([isinstance(y, Node) for y in x]):
                output.append([y.bind(data) for y in x])
            elif hasattr(x, '_data') and x._data[util.BIND_S]:
                if util.AT_BIND_S in x._data:
                    output.append(data[util.AT_BIND_S + x._value])
                else:
                    output.append(data[x._value])
            else:
                output.append(x)
        return output

    def expand_bindings(self, bindings):
        """ Expand stored bindings at interpret time
        ie: +(.a.b.$x) + { x : .a.b.c } -> +(.a.b.a.b.c)
        """
        new_values = []
        for x in self._vars:
            if isinstance(x, Sentence):
                new_values.append(x.expand_bindings(bindings))
            else:
                new_values.append(x)
        return ActionComponent(self.op, new_values)

    def to_sentence(self):
        """ Return the action in canonical form """
        # eg : assert a.test  = assert -> a.test -> nil
        # TODO : params are sentences themselves
        head = PyRuleNode(self.op, {util.OPERATOR_S : self})
        sen = Sentence([head] + self._vars[:])
        return sen

    def var_set(self):
        obj = super(ActionComponent, self).var_set()
        return {'in' : obj['in'].union(obj['out']), 'out': set()}

    def pprint(self, **kwargs):
        return PrU.print_operator(self, wrap_vars=True, **kwargs)


class Action(PO.ProductionContainer):
    """ A Container for Action Specifications """

    def __init__(self, clauses, params=None, type_str=util.ACTION_S):
        super(Action, self).__init__(clauses,
                                     params=params,
                                     type_str=type_str)

    def __str__(self):
        raise DeprecationWarning()
        return ", ".join([str(x) for x in self.clauses])

    def expand_bindings(self, bindings):
        """ Expand stored bindings """
        exp_clauses = []
        for clause in self.clauses:
            exp_clauses.append(clause.expand_bindings(bindings))

        return Action(exp_clauses, params=self._vars)

    def copy(self):
        copied = super(Action, self).copy()
        copied._vars += self._vars[:]
        return copied

    def to_sentences(self, target=None):
        # needs to return both the action sentences,
        # AND the action operators in canonical form
        raise NotImplementedError()

