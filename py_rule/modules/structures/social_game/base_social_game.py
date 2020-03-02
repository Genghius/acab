"""
** Koster Games
*** Base Game
    Position
    Demarcation
    Decision making
    Choice
    Information
    payoff
    Scope

*** Parallel (A)Symmetric
    mediating status,
    ordering, leaderboards

*** Direct Opposition
    Resource consumption
    Tug of War
    handicaps

*** Multifront opposition
    last man standing
    Bidding

*** Information games
    deception, bluffing
    3rd party/meta betting

*** Games masters

*** Roles and Teams
    Ritual, gifts,
    reciprocity, mentoring
    identity, ostracism

*** Networks
    trust, guilds
    exclusivity, contract
    election, reputation,
    influence
    public goods, commons
    services


"""
from py_rule.abstract.value import PyRuleValue

class SocialGameBase(PyRuleValue):
    """ Base Description of social games """

    def __init__(self):
        return

    def __str__(self):
        """ Data needs to implement a str method that produces
        output that can be re-parsed """
        raise NotImplementedError()

    def copy(self):
        """ Data needs to be able to be copied """
        raise NotImplementedError()

    def bind(self, bindings):
        """ Data needs to be able to bind a dictionary
        of values to internal variables """
        raise NotImplementedError()

    def var_set(self):
        """ Data needs to be able to report internal variables """
        raise NotImplementedError()



