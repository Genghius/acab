from acab.interfaces.dsl import DSL_Fragment_i

from .query_operators import EQ, NEQ, RegMatch, ELEM, HasTag, TypeMatch
from . import query_op_parsers as QOP

class QueryDSL(DSL_Fragment_i):
    """ The Module Spec for base operators """

    def assert_parsers(self, pt):
        pt.add("word.annotation.hastag", QOP.tagList)
        #        "operator.query.eq", QO.EQ,
        #        "operator.query.neq", QO.NEQ,
        #        "operator.query.regmatch", QO.RegMatch,
        #        "operator.query.elem", QO.ELEM,
        #        "operator.query.hastag", QO.HasTag,
        pass


    def query_parsers(self, pt):
        pass
