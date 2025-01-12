import logging as root_logger

import acab.interfaces.semantic as SI
import acab.error.semantic_exception as ASErr
from acab.core.config.config import AcabConfig
from acab.core.data.acab_struct import BasicNodeStruct
from acab.core.data.values import AcabStatement, Sentence

logging = root_logger.getLogger(__name__)
config = AcabConfig.Get()

CONSTRAINT_S     = config.prepare("Value.Structure", "CONSTRAINT")()
NEGATION_S       = config.prepare("Value.Structure", "NEGATION")()
QUERY_FALLBACK_S = config.prepare("Value.Structure", "QUERY_FALLBACK")()
DEFAULT_SETUP_S  = config.prepare("Data", "DEFAULT_SETUP_METHOD")()
DEFAULT_UPDATE_S = config.prepare("Data", "DEFAULT_UPDATE_METHOD")()

Node          = 'AcabNode'
Printable     = 'Printable'
Value         = 'AcabValue'
Structure     = 'AcabStruct'
Engine        = 'Engine'
Contexts      = 'Contexts'


# TODO RDFSemantics, ReteSemantics
# Dependent Semantics
class FSMSemantics(SI.DependentSemantics_i):

    def insert(self, struct, sen, data=None, ctxs=None):
        """
        In the FSM, everything is access from the root,
        there is a defined start node,
        sentences define sequences of connections

        eg:
        a.b.c.a : defines a circular path

        a.b.d   : defines a split
        a.c.d

        -a.b.c  : disconnects a from b, and b from c
        """
        if data is None:
            data = {}

        if NEGATION_S in sen.data and sen.data[NEGATION_S]:
            return self._delete(struct, sen, data, engine)

        # Get the root
        root = self.default[0].up(struct.root)
        current = root
        root_semantics, _ = self.lookup(root.value)
        for word in sen:
            new_node = None
            root_accessible = root_semantics.access(root, word, data)
            if not bool(root_accessible):
                next_semantics, _ = self.lookup(word)
                new_node = next_semantics.make(word, data)
                root_semantics.insert(root, word, data)
            else:
                new_node = root_accessible[0]

            current_semantics, _ = self.lookup(current)
            current_accessible = current_semantics.access(current, new_node, data)
            if not bool(current_accessible):
                current = current_semantics.insert(current, new_node, data)
            else:
                current = new_node

        return current

    def query(self, struct, query, data=None, ctxs=None):
        """
        Test that all states exist, and connections line up:
        a.b.c.d?

        Or that connections are *not* there:
        ~a.b.c?

        Use a node test to check state?:
        a(λactive).b.c.d?
        a.b(λactive).c.d? etc

        Or Get the active state:
        $x(λactive)?

        Test for loops:
        a.b.a?

        Test for available movements:
        $x(λactive).$y?
        """
        # Query from start to finish
        if ctxs is None:
            raise ASErr.AcabSemanticException("Ctxs is None to fsm query", query)

        negated_query = False
        if NEGATION_S in sen.data and sen.data[NEGATION_S]:
            negated_query = True

        # TODO get collapse vars from the sentence
        collapse_vars = []
        with ctxs(struct.root, sen[0], data, collapse_vars, negated_query):
            for word in sen:
                for ctxInst in ctxs.active_list():
                    indep, _ = self.lookup(ctxInst.current)
                    results = indep.access(ctxInst.current, word, data)
                    if not bool(results):
                        ctxs.fail(ctxInst, word, None)
                    else:
                        ctxs.test(word, ctxInst, results)

        return ctxs


    def _delete(self, struct, sen, data=None, ctxs=None):
        """
        remove each word in the sentence from its prior
        """
        root = struct.root
        root_sem, _ = self.lookup(root.value)
        current = None
        for head,succ in zip(sen[:-1], sen[1:]):
            if root_sem.access(root, head, data):
                head_node = root_sem.get(root, head, data)
                head_sem, _ = self.lookup(head_node.value)
                head_sem.delete(head_node, succ, data)
                current = head_node

        return current

    def trigger(self, struct, sen, data=None, ctxs=None):
        """
        Trigger the FSM.
        ie:
        [empty sentence] : Use any available transition
        a.b              : Use the defined transition
        """
        raise NotImplementedError()


class ASPSemantics(SI.DependentSemantics_i):
    """
    Stub for passing assertions and queries into an ASP program
    """

    def insert(self, struct, sen, data=None, ctxs=None):
        """
        construct the ASP program
        """
        pass


    def query(self, struct, query, data=None, ctxs=None):
        """
        pass the cached asp program to a solver,
        retrieve results, extract what is needed,
        and return as sentences
        """
        pass

    def trigger(self, struct, sen, data=None, ctxs=None):
        pass



class DepthTrieSemantics(SI.DependentSemantics_i):
    """
    Trie Semantics which map values -> Nodes
    Searches *Depth First*
    """

    def insert(self, struct, sen, data=None, ctxs=None):
        if data is None:
            data = {}

        if NEGATION_S in sen.data and sen.data[NEGATION_S]:
            return self._delete(struct, sen, data)

        # Get the root
        # TODO: Ensure the struct is appropriate
        current = self.default[0].up(struct.root)
        for word in sen:
            semantics, _ = self.lookup(current)
            accessible = semantics.access(current, word, data)
            if bool(accessible):
                current = accessible[0]
            else:
                next_semantics, _ = self.lookup(word)
                new_node = next_semantics.make(word, data)
                current = semantics.insert(current, new_node, data)

        return current


    def _delete(self, struct, sen, data=None, ctxs=None):
        parent = struct.root
        current = struct.root

        for word in sen:
            # Get independent semantics for current
            semantics, _ = self.lookup(current)
            accessed = semantics.access(current, word, data)
            if bool(accessed):
                parent = current
                current = accessed[0]
            else:
                return None

        # At leaf:
        # remove current from parent
        semantics, _ = self.lookup(parent)
        semantics.remove(parent, current.value, data)

        return current


    def query(self, struct, sen, data=None, ctxs=None):
        """ Depth First Search Query """
        if ctxs is None:
            raise ASErr.AcabSemanticException("Ctxs is none to TrieSemantics.query", sen)

        negated_query = False
        if NEGATION_S in sen.data and sen.data[NEGATION_S]:
            negated_query = True

        # TODO get collapse vars from the sentence
        collapse_vars = []
        with ctxs(struct.root, sen, data, collapse_vars, negated_query):
            while ctxs.active:
                currentInst = ctxs.pop(top=True)
                try:
                    remaining_sen = sen.words[:]
                    if currentInst._remaining_query is not None:
                        remaining_sen = currentInst._remaining_query

                    while bool(remaining_sen):
                        word = remaining_sen.pop(0)
                        indep, _ = self.lookup(currentInst._current)
                        search_word = word
                        # Handle variable:
                        if word.is_var and word not in ctxInst:
                            search_word = None
                        elif word.is_var and word in ctxInst:
                            # Word is var, but bound, so look for that instead
                            search_word = currentInst[word]


                        results = indep.access(currentInst._current,
                                               search_word,
                                               datac)

                        # TODO to make this depth first,
                        # the current ctxInst needs to be updated
                        # as the search progresses
                        if not bool(results):
                            ctxs.fail(currentInst, word, None)
                            raise ASErr.AcabSemanticQueryContextDepletionFailure("Ctx has failed, going to next", None)
                        else:
                            new_active_ctxs = ctxs.test(currentInst, results, word)
                            if not bool(new_active_ctxs):
                                raise ASErr.AcabSemanticQueryContextDepletionFailure("No Successes, switch to next context", None)
                            for ctxInst in new_active_ctxs:
                                ctx_inst._remaining_query = remaining_sen[:]

                            currentInst = new_active_ctxs.pop(0)

                except ASErr.AcabSemanticQueryContextDepletionFailure as err:
                    continue

        return ctxs


    def trigger(self, struct, sen, data=None, ctxs=None):
        pass
