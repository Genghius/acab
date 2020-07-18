"""
An Entry point for type checking

Type checking is a triple of tries: (type_definitions,
 type_assignments, type_variables)

Definitions are structured polytypes.
Assignments start untyped, and are gradually refined.
Variables connect variables in the assignments to definitions.

The Tries use nodes of TypeDefTrieNode,
TypeAssignmentTrieNode, and VarTypeTrieNode.

The values of the trie nodes are acab.abstract.values, subclassed as Types.
They are TypeDefinitions, and TypeInstantiations.


When a TypeChecker is called with (Definitions, Rules, Assertions),
it adds the definitions, add the assertions,
then adds each rule, treating each rule as a separate context.

Definitions are located by their path (eg: type.test )
which holds the TypeDefintion (which contains its structure and vars)
(eg: { type.test.name!$x :: string, type.test.age!$y :: int })

type_assignments is the main 'work' trie, holding all sentences.
When an assertion/declaration is added, it adds the node then updates
the node to connect any variables in the sentence with variables
in the type_variable trie.
(eg: a.thing.$x,  a.different.thing :: type.test)

Variables connect different locations of the assignment trie together
(eg: a.thing.$x, another.thing.$x will share the same var node: $x)


When validate is called:
equivalent pathed nodes are merged,
then known types are applied everywhere they can be
the linked type definition then DFS's
ensure it matches the definition.
and any newly typed nodes are then ready to be used in the next iteration



If validate succeeds, it returns True. If it Fails, it raises an Exception

"""

import logging as root_logger
from functools import partial
from uuid import uuid1

from acab.abstract.value import AcabStatement
from acab.abstract.sentence import Sentence
from acab.abstract.trie.trie import Trie
from acab.abstract.action import ActionOp

from . import type_exceptions as te
from . import util as TU

from .nodes.operator_def_node import OperatorDefTrieNode
from .nodes.type_assignment_node import TypeAssignmentTrieNode
from .nodes.typedef_node import TypeDefTrieNode
from .nodes.var_type_node import VarTypeTrieNode
from .nodes.sum_def_node import SumTypeDefTrieNode

from .values.operator_definition import OperatorDefinition
from .values.type_definition import TypeDefinition, SumTypeDefinition


logging = root_logger.getLogger(__name__)


class TypeChecker(ActionOp):
    """ Abstract Class for Type Checking """
    # parse their locations, and add them as definitions

    def __init__(self):
        super(TypeChecker, self).__init__()

        self._definitions = Trie(TypeDefTrieNode)
        self._declarations = Trie(TypeAssignmentTrieNode)
        self._variables = Trie(VarTypeTrieNode)

    def __str__(self):
        output = []
        output.append("Defs   : {}".format(str(self._definitions).replace('\n', ' ')))
        output.append("Decs   : {}".format(str(self._declarations).replace('\n', ' ')))
        output.append("Vars   : {}".format(str(self._variables).replace('\n', ' ')))

        return "\n".join(output)

    def __repr__(self):
        return "TypeChecker: \n{}".format(str(self))


    def __call__(self, data=None, engine=None):
        """ Pass in data to type check """
        # Gets all leaf sentences and statements
        logging.info("Running Type Checker")
        sentences = engine.to_sentences()
        logging.info("Checking {} sentences".format(len(sentences)))

        local_contexts_to_check = []
        for sen in sentences:
            if isinstance(sen[-1], TypeDefinition):
                self.add_definition(sen)
            elif isinstance(sen[-1], AcabStatement):
                local_contexts_to_check.append(sen[-1])
            else:
                self.add_assertion(sen)

        logging.info("Definitions and Assertions added")
        logging.info("Checking {} local contexts".format(len(local_contexts_to_check)))
        for statement in local_contexts_to_check:
            self.add_statement(statement)

        logging.info("Checking Totality")
        self.validate()


    def _get_known_typed_nodes(self):
        # propagate known variable types
        dummy = [x.propagate() for x in self._variables.get_nodes(lambda x: x.type_instance is not None)]
        # get all known declared types
        val_queue = {y for y in self._declarations.get_nodes(lambda x: x.type_instance is not None)}
        return val_queue

    def _merge_equivalent_nodes(self):
        """ merge equivalent variables.
        ie: a.b.$c and a.b.$d share the same ._variables node """
        parents_of_equiv_vars = self._declarations.get_nodes(TU.has_equivalent_vars_pred)
        for p in parents_of_equiv_vars:
            var_nodes = {x._var_node for x in p._children.values() if x.is_var}
            head = var_nodes.pop()
            head.merge(var_nodes)
            dummy = [self._variables.remove([x]) for x in var_nodes]


    def clear_context(self):
        """ Clear variables """
        # Clear self._variables and unregister its nodes from
        # vars in declarations
        var_nodes = self._variables.get_nodes()
        dummy = [x.clear_assignments() for x in var_nodes]

        # remove all sentences in declarations that start with a variable
        # TODO or an operator
        dummy = [self._declarations.remove([x]) for x in var_nodes]

        # remove the variables
        dummy = [self._variables.remove([x]) for x in var_nodes]

    def query(self, queries):
        """ Get the type of a sentence leaf """
        if isinstance(queries, Sentence):
            queries = [queries]

        results = []
        for line in queries:
            queried = self._declarations.query(line)
            if queried is None:
                continue
            line_is_typed = TU.TYPE_DEC_S in line[-1]._data
            result_is_typed = TU.TYPE_DEC_S in queried._data
            types_match = (line_is_typed
                           and result_is_typed
                           and line[-1]._data[TU.TYPE_DEC_S] == queried._data[TU.TYPE_DEC_S])
            if line_is_typed and result_is_typed and not types_match:
                raise te.TypeConflictException(line[-1]._data[TU.TYPE_DEC_S],
                                               queried._data[TU.TYPE_DEC_S],
                                               "".join([str(x) for x in line]))
            results.append(queried)
        return results

    def validate(self):
        """ Infer and check types """
        self._merge_equivalent_nodes()
        typed_queue = self._get_known_typed_nodes()

        # TODO: get known operations

        # Use known types to infer unknown types
        create_var = partial(util_create_type_var, self)
        dealt_with = set()
        while bool(typed_queue):
            head = typed_queue.pop()
            assert(isinstance(head, TypeAssignmentTrieNode)), breakpoint()
            if head in dealt_with:
                continue
            dealt_with.add(head)

            # TODO branch on structural /functional

            # check the head
            # TODO: handle sum type paths
            head_type = self._definitions.query(head.type_instance.path)
            if head_type is None:
                raise te.TypeUndefinedException(head.type_instance, head)

            # Propagate the type to all connected variables
            # TODO: if var nodes also link *into* polytype def nodes
            # that would solve generalisation?
            if head.is_var:
                head._var_node.unify_types(head.type_instance)
                head._var_node.propagate()
                assert(all([isinstance(x, TypeAssignmentTrieNode) for x in head._var_node._nodes])), breakpoint()
                typed_queue.update([x for x in head._var_node._nodes if isinstance(x, TypeAssignmentTrieNode)])

            # Apply a known type to a node, get back newly inferred types
            results = head_type.validate(head, create_var)
            assert(all([isinstance(x, TypeAssignmentTrieNode) for x in results])), breakpoint()
            typed_queue.update(results)

            # if head validation returns only operators, and
            # the queue is only operators, then error

        return True

    def add_definition(self, *definitions):
        for a_def in definitions:
            assert(isinstance(a_def[-1], TypeDefinition))
            assert(isinstance(a_def, Sentence))
            if isinstance(a_def[-1], OperatorDefinition):
                self._definitions.add(a_def, a_def[-1],
                                                 leaf_override=OperatorDefTrieNode)
            elif isinstance(a_def[-1], SumTypeDefinition):
                self._definitions.add(a_def, a_def[-1],
                                                 leaf_override=SumTypeDefTrieNode)
            else:
                self._definitions.add(a_def, a_def[-1])

    def add_assertion(self, sen):
        assert(isinstance(sen, Sentence))
        self._declarations.add(sen, None,
                               update=lambda c, v, p, d: c.update(v, d),
                               u_data=self._variables)

    def add_statement(self, statement):
        """
        Statements are treated as having their own local context.
        So add it, type check it, and then clear any variable associations
        """
        sentences = statement.to_local_sentences()

        for sen in sentences:
            self.add_assertion(sen)

        self.validate()
        self.clear_context()



def util_create_type_var(tc, base_name):
    # Create a new var name
    assert(isinstance(base_name, str))
    var_name = str(uuid1())
    return tc._variables.add([base_name, var_name], [])