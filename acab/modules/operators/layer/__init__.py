from acab.interfaces.dsl import DSL_Fragment_i

from .layer_actions import LayerRunAgenda, LayerRunRules, LayerPerform

class MODULE(DSL_Fragment_i):
    """ The Module Spec for base operators """

    def assert_parsers(self, pt):
        # pt.add("operator.transform.run_agenda", LA.LayerRunAgenda,
        #        "operator.transform.run_rules", LA.LayerRunRules,
        #        "operator.action.layer_perform", LA.LayerPerform)
        pass

    def query_parsers(self, pt):
        pass

