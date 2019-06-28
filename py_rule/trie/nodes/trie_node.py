import py_rule.utils as utils

class TrieNode:

    @staticmethod
    def Root():
        raise Exception("Unimplemented")

    def __init__(self, value, data=None):
        self._value = value
        self._children = {}
        self._data = {}
        if data:
            self._data.update(data)

    def __str__(self):
        """ Usable output """
        val = str(self._value)
        if self._data['value_type'] == "string":
            val = '"{}"'.format(val)
        elif self._data['value_type'] == 'float':
            val.replace(".", "d")

        if 'bind' in self._data and self._data['bind']:
            val = "$" + val

        if 'constraints' in self._data:
            constraints = ", ".join(str(x) for x in self._data['constraints'])
            val += "({})".format(constraints)

        if 'op' in self._data:
            val += utils.EXOP_lookup[self._data['op']]

        return val

    def __repr__(self):
        """ Unambiguous printing """
        return "TN: {}".format(repr(self._value))

    def __hash__(self):
        return hash(str(self))

    def __len__(self):
        return len(self._children)

    def __bool__(self):
        return bool(self._children)

    def __contains(self, v):
        return self.has_child(v)

    def add_child(self, node):
        self._children[str(node)] = node
        return node

    def get_child(self, node):
        return self._children[str(node)]

    def has_child(self, node):
        return str(node) in self._children

    def remove_child(self, node):
        if node in self:
            del self._children[str(node)]
            return True

        return False

    def clear_children(self):
        self._children = {}

    def opless_print(self):
        val = str(self._value)
        if self._data['value_type'] == "string":
            val = '"{}"'.format(val)
        elif self._data['value_type'] == 'float':
            val = val.replace(".", "d")

        if 'bind' in self._data and self._data['bind']:
            val = "$" + val
        if 'constraints' in self._data:
            constraints = ", ".join(str(x) for x in self._data['constraints'])
            val += "({})".format(constraints)
        return val

    def copy(self):
        newnode = TrieNode(self._value, self._data)
        newnode._children.update(self._children)
        return newnode
