"""
The Core Value Classes: AcabValue, AcabStatement, Sentence
"""
import logging as root_logger
from copy import deepcopy
from dataclasses import InitVar, dataclass, field, replace
from fractions import Fraction
from re import Pattern
from typing import (Any, Callable, ClassVar, Dict, Generic, Iterable, Iterator,
                    List, Mapping, Match, MutableMapping, Optional, Sequence,
                    Set, Tuple, TypeVar, Union, cast)
from uuid import UUID, uuid1
from weakref import ref

from acab import types as AT
import acab.interfaces.value as VI
from acab.core.config.config import AcabConfig
import acab.core.data.default_structure as DS

logging          = root_logger.getLogger(__name__)

config           = AcabConfig.Get()
ANON_VALUE       = config.prepare("Symbols", "ANON_VALUE")()
BIND_SYMBOL      = config.prepare("Symbols", "BIND")()
AT_BIND_SYMBOL   = config.prepare("Symbols", "AT_BIND")()
FALLBACK_MODAL   = config.prepare("Symbols", "FALLBACK_MODAL", actions=[config.actions_e.STRIPQUOTE])()

UUID_CHOP        = bool(int(config.prepare("Print.Data", "UUID_CHOP")()))

T     = TypeVar('T', str, Pattern, list)

Value     = AT.Value
Sen       = AT.Sentence
Statement = AT.Statement

@dataclass(frozen=True)
class AcabValue(VI.Value_i, Generic[T]):
    _value_types : ClassVar[Set[Any]] = set([VI.Value_i, str, Pattern, list])
    value        : T                  = field(default=None)

    @staticmethod
    def safe_make(value: T,
                  name: str=None,
                  data: Optional[Dict[Any, Any]]=None,
                  _type: Optional[Sen]=None,
                  **kwargs) -> Value:
        """ Wrap the provided value in an AcabValue,
        but only if it isn't an AcabValue already """
        _data = {}
        if data is not None:
            _data.update(data)
        if _type is not None:
            _data.update({DS.TYPE_INSTANCE: _type})

        if isinstance(value, VI.Value_i):
            new_data = {}
            new_data.update(value.data)
            new_data.update(_data)
            return value.copy(data=new_data)


        return AcabValue(value=value, data=_data, **kwargs)

    def __post_init__(self):
        # Applicable values: Self + any registered
        value_type_tuple = tuple(list(AcabValue._value_types))

        assert(self.value is None or isinstance(self.value, value_type_tuple)), self.value

        # NOTE: use of setattr to override frozen temporarily to update name
        #
        # TODO: this could be a sieve?
        # TODO or move into safe_make
        # name update #########################################################
        name_update = None
        if self.name is None and self.value is None:
            name_update = self.__class__.__name__
        if self.name is not None:
            assert(isinstance(self.name, str)), self.name
        elif isinstance(self.value, Pattern):
            name_update = self.value.pattern
        elif isinstance(self.value, (list, VI.Statement_i)):
            name_update = ANON_VALUE
        else:
            name_update = str(self.value)

        if name_update is not None:
            object.__setattr__(self, "name", name_update)
            # self.name = name_update
        # end of name update ##################################################

        if self.value is None:
            object.__setattr__(self, "value", self.name)
            # self.value = self.name

        if DS.TYPE_INSTANCE not in self.data:
            self.data[DS.TYPE_INSTANCE] = DS.TYPE_BOTTOM_NAME

        if DS.BIND not in self.data:
            self.data[DS.BIND] = False

        if any([not isinstance(x, VI.Value_i) for x in self.params]):
            original_params = self.params[:]
            self.params.clear()
            self.params.extend([AcabValue.safe_make(x) for x in original_params])


    def __str__(self):
        """ the simplest representation of the value,
        for internal use.
        For reparseable output, use a PrintSemantics
        """
        return self.name


    def __repr__(self):
        val_str = ""
        name_str = str(self)
        if self.value is not self.name:
            val_str = ":..."

        if self.is_at_var:
            name_str = BIND_SYMBOL + name_str
        elif self.is_var:
            name_str = BIND_SYMBOL + name_str

        return "({}:{}:{})".format(self.__class__.__name__,
                                     name_str,
                                     val_str)

    def __hash__(self):
        return hash(repr(self))

    def __eq__(self, other):
        """ Base eq: compare hashes  """
        if id(self) == id(other):
            return True
        elif isinstance(other, str):
            return str(self) == other
        elif not isinstance(other, VI.Value_i):
            return False
        elif self.uuid == other.uuid:
            return True
        else:
            return str(self) == str(other)



    def __lt__(self, other):
        if isinstance(other, AcabValue):
            return self.name < other.name
        elif isinstance(other, str):
            return self.name < str

        return TypeError("AcabValues can only be __lt__'d with AcabValues and Strings")


    @property
    def type(self) -> Sen:
        """ Lazily coerces description to Sentence """
        # TODO ensure this type sentence is of type... "sentence.type"?
        # to enable printing
        type_matches_t = isinstance(self.data[DS.TYPE_INSTANCE], Sentence)
        if type_matches_t:
            return self.data[DS.TYPE_INSTANCE]

        if DS.SEMANTIC_HINT in self.data and isinstance(self.data[DS.SEMANTIC_HINT], Sentence):
            self.data[DS.TYPE_INSTANCE] = self.data[DS.SEMANTIC_HINT]
        else:
            self.data[DS.TYPE_INSTANCE] = Sentence.build([self.data[DS.TYPE_INSTANCE]])
        return self.data[DS.TYPE_INSTANCE]


    @property
    def is_var(self) -> bool:
        return self.data[DS.BIND] is not False

    @property
    def is_at_var(self) -> bool:
        return self.data[DS.BIND] == DS.AT_BIND

    def copy(self, **kwargs) -> Value:
        """ copy the object, but give it a new uuid """
        if 'params' not in kwargs:
            kwargs['params'] = self.params[:]
        if 'tags' not in kwargs:
            kwargs['tags'] = self.tags.copy()
        if 'data' not in kwargs:
            kwargs['data'] = self.data.copy()

        return replace(self, uuid=uuid1(), **kwargs)


    def bind(self, bindings) -> Value:
        """ Data needs to be able to bind a dictionary
        of values to internal variables
        return modified copy
        """
        if self.is_var and self.value in bindings:
            assert(not self.params)
            return AcabValue.safe_make(bindings[self.value])

        if not any([x.is_var for x in self.params]):
            return self

        bound_params = [x.bind(bindings) for x in self.params]
        return self.copy(params=bound_params)


    def apply_params(self, params, data=None) -> Value:
        """
        return modified copy
        """
        if not bool(params):
            return self

        safe_params = [x if isinstance(x, VI.Value_i) else AcabValue(x) for x in params]
        return self.copy(params=safe_params)

    def apply_tags(self, tags:List[Value]) -> Value:
        """
        return modified copy
        """
        assert(all([isinstance(x, VI.Value_i) for x in tags]))
        if not bool(tags):
            return self

        tag_extension  = {x for x in self.tags}
        tag_extension.update(tags)
        return self.copy(tags=tag_extension)

    def has_tag(self, *tags:List[Value]) -> bool:
        return all([t in self.tags for t in tags])


    def attach_statement(self, value) -> Statement:
        """
        Attach an unnamed statement to this value.
        Name the statement to the name of the former leaf
        return modified copy
        """
        assert(isinstance(value, VI.Value_i))
        combined_data = self.data.copy()
        combined_data.update(value.data)
        value_copy = value.copy(name=self.name, data=combined_data)
        return value_copy



    @property
    def has_var(self) -> bool:
        if self.is_var:
            return True
        if any([x.has_var for x in self.params]):
            return True
        if any([x.has_var for x in self.tags]):
            return True
        return False

    def to_word(self) -> Value:
        return self


class AcabStatement(AcabValue, VI.Statement_i):
    """ AcabStatement functions the same as AcabValue,
    but provides specific functionality for converting to a string
    """

    def to_word(self) -> Value:
        """ Convert a Statement to just an AcabValue, of it's name """
        new_data = {}
        new_data.update(self.data)
        new_data.update({DS.TYPE_INSTANCE: Sentence.build([DS.TYPE_BOTTOM_NAME])})
        simple_value = AcabValue.safe_make(self.name, data=new_data)
        return simple_value

@dataclass(frozen=True)
class Sentence(AcabStatement, VI.Sentence_i):

    @staticmethod
    def build(words, **kwargs):
        safe_words = [AcabValue.safe_make(x) for x in words]
        sen = Sentence(value=safe_words, **kwargs)
        return sen


    def __post_init__(self):
        AcabValue.__post_init__(self)
        self.data[DS.TYPE_INSTANCE] = DS.SENTENCE_PRIM

    def __eq__(self, other):
        if isinstance(other, str) and other[:2] == "_:":
            return str(self) == other
        elif isinstance(other, str):
            return str(self) == f"_:{other}"
        elif not isinstance(other, VI.Sentence_i):
            return False
        elif len(self) != len(other):
            return False
        else:
            return all([x == y for x,y in zip(self.words, other.words)])


    def __hash__(self):
        return hash(str(self))
    def __str__(self):
        words = FALLBACK_MODAL.join([str(x) for x in self.words])
        return "{}:{}".format(self.name, words)

    def __repr__(self):
        return super().__repr__()
    def __len__(self):
        return len(self.words)
    def __iter__(self):
        return iter(self.words)

    def __getitem__(self, i):
        if isinstance(i, slice):
            return Sentence.build(self.words.__getitem__(i), data=self.data)
        return self.words.__getitem__(i)

    def __contains__(self, value:Union[str, Value]):
        return value in self.words

    def copy(self, **kwargs) -> Sen:
        if 'value' not in kwargs:
            kwargs['value'] = [x.copy() for x in self.value]

        return super(Sentence, self).copy(**kwargs)

    def clear(self) -> Sen:
        """
        return modified copy
        """
        return self.copy(value=[])

    def bind(self, bindings) -> Sen:
        """ Given a dictionary of bindings, reify the sentence,
        using those bindings.
        ie: a.b.$x with {x: blah} => a.b.blah
        return modified copy
        """
        assert(isinstance(bindings, dict))
        output = []

        for word in self:
            # early expand if a plain node
            if not word.is_var:
                output.append(word)
                continue

            if not word.value in bindings:
                output.append(word)
                continue

            # Sentence invariant: only word[0] can have an at_bind
            if word.is_at_var:
                retrieved = bindings[DS.AT_BIND + word.value]
            else:
                retrieved = bindings[word.value]


            if isinstance(retrieved, VI.Sentence_i) and len(retrieved) == 1:
                # Flatten len1 sentences:
                copied = retrieved[0].copy()
                copied.data.update(word.data)
                copied.data[DS.BIND] = False
                output.append(copied)
            elif isinstance(retrieved, VI.Value_i):
                # Apply the variables data to the retrieval
                copied = retrieved.copy()
                copied.data.update(word.data)
                # Except retrieved isn't a binding
                copied.data[DS.BIND] = False
                output.append(retrieved)
            else:
                # TODO how often should this actually happen?
                # won't most things be values already?
                # TODO get a type for basic values
                new_word = AcabValue(retrieved, data=word.data)
                new_word.data[DS.BIND] = False
                output.append(new_word)

        return Sentence.build(output,
                              data=self.data,
                              params=self.params,
                              tags=self.tags)

    def add(self, *other) -> Sen:
        """ Return a copy of the sentence, with words added to the end.
        This can flatten entire sentences onto the end
        return modified copy
        """
        words = self.words
        for sen in other:
            assert(isinstance(sen, (list, VI.Sentence_i)))
            words += [x for x in sen]

        new_sen = replace(self, value=words)
        return new_sen

    def prefix(self, prefix:Union[Value, Sen]) -> Sen:
        if isinstance(prefix, list):
            prefix = Sentence.build(prefix)
        elif not isinstance(self, Sentence):
            prefix = Sentence.build([prefix])

        return prefix.add(self)


    def attach_statement(self, value) -> Sen:
        """
        Copy the sentence,
        Replace the leaf with the provided statement,
        Name the statement to the name of the former leaf
        return modified copy
        """
        assert(isinstance(value, VI.Value_i))
        last = self.words[-1]
        combined_data = last.data.copy()
        combined_data.update(value.data)
        value_copy = value.copy(name=last.name, data=combined_data)

        new_words = self.words[:-1] + [value_copy]
        sen_copy = self.copy(value=new_words)

        return sen_copy

    def detach_statement(self) -> Tuple[Sen, List[Statement]]:
        """
        The inverse of attach_statement.
        Copy the sentence,
        Reduce all words down to basic values
        Return modified copy, and the statement
        """
        statements = []
        out_words  = []

        # collect leaf statements
        for word in self.words:
            if isinstance(word, VI.Statement_i):
                out_words.append(word.to_word())
                statements.append(word)
            else:
                out_words.append(word)

        sen_copy = self.copy(value=out_words)
        return (sen_copy, statements)


    @property
    def is_var(self) -> bool:
        if len(self) > 1:
            return False

        return self[0].is_var

    @property
    def is_at_var(self) -> bool:
        if len(self) > 1:
            return False

        return self[0].is_var

    @property
    def has_var(self) -> bool:
        if self.is_var:
            return True
        return any([x.is_var for x in self.words])


    def match(self, sen:Sen) -> List[Tuple[Value, Value]]:
        """ Match a sentence's variables to a target

        eg: _:$x.b.$y match _:a.b.c -> [(x, a), (y, c)]
        """
        results = []
        for x,y in zip(self.words, sen.words):
            if x.is_var:
                results.append((x,y))

        return results
