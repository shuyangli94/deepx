import numpy as np
from abc import ABCMeta, abstractmethod
from six import add_metaclass
from functools import wraps

from .. import T
from ..util import flatten
from .exceptions import ShapeOutError
from .shape import Shape

# __all__ = ['Node', 'NodeList']

class DeviceDecorator(ABCMeta):
    def __init__(cls, name, bases, clsdict):
        if 'get_outputs' in clsdict:
            old = clsdict['get_outputs']
            @wraps(old)
            def new_get_outputs(self, *args, **kwargs):
                with T.device(self.device):
                    return old(self, *args, **kwargs)
            setattr(cls, 'get_outputs', new_get_outputs)

@add_metaclass(DeviceDecorator)
class Node(object):
    """
    The :class:`Node` is the highest level abstraction in DeepX.
    It represents anything that takes in a set of inputs
    and returns a set of outputs.
    """

    @abstractmethod
    def get_shapes_in(self):
        pass

    @abstractmethod
    def get_shapes_out(self):
        pass

    def get_num_inputs(self):
        return len(self.get_shapes_in())

    def get_num_outputs(self):
        return len(self.get_shapes_out())

    def get_outputs(self, inputs):
        if len(inputs) != self.get_num_inputs():
            raise Exception("shape mismatch")
        return self.forward(*inputs)

    @abstractmethod
    def forward(self, *inputs):
        pass

    def outputs(self, *inputs):
        return self.forward(*inputs)

    def __repr__(self):
        return "Node(%u, %u)" % (self.get_num_inputs(), self.get_num_outputs())

    def __rshift__(self, other):
        if (isinstance(other, list) or isinstance(other, tuple)):
            return [self.chain(c) for c in other]
        return self.chain(other)

    def __rrshift__(self, other):
        other = coerce_node(other)
        return other >> self

    def __add__(self, other):
        return self.add(other)

    def chain(self, node):
        return Chain(self, node)

    def add(self, node):
        from ..ops import Add
        node = coerce_node(node)
        return (self, node) >> Add()

    @abstractmethod
    def infer_shape(self):
        pass

    def __str__(self):
        return repr(self)

def coerce_node(val):
    if isinstance(val, float) or isinstance(val, int):
        from .data import Constant
        return Constant(val)
    elif isinstance(val, list) or isinstance(val, tuple):
        return NodeList(val)
    raise Exception("bad node")

class NodeList(Node):

    def __init__(self, nodes):
        self.nodes = list(nodes)
        assert len(self.nodes) > 0

    def get_shapes_in(self):
        return self.nodes[0].get_shapes_in()

    def infer_shape(self):
        for node in self.nodes:
            node.infer_shape()

    def get_shapes_out(self):
        return [shape for node in self.nodes for shape in node.get_shapes_out()]

    def __repr__(self):
        return "[%s]" % ", ".join(map(repr, self.nodes))

    def forward(self, *inputs):
        return [out for node in self.nodes for out in node.forward(*inputs)]

class ShapedNode(Node):

    def __init__(self, shapes_in, shapes_out):
        self.shapes_in = shapes_in
        self.shapes_out = shapes_out

    def get_shapes_in(self):
        return self.shapes_in

    def get_shapes_out(self):
        return self.shapes_out

    def set_shapes_in(self, shape):
        self.shapes_in = shape

    def set_shapes_out(self, shape):
        self.shapes_out = shape

class Chain(Node):

    def __init__(self, left, right):
        self.left = left
        self.right = right
        self.infer_shape()

    def get_shapes_in(self):
        return self.left.get_shapes_in()

    def get_shapes_out(self):
        return self.right.get_shapes_out()

    def set_shapes_in(self, shapes_in):
        self.left.set_shapes_in(shapes_in)

    def set_shapes_out(self, shapes_out):
        self.right.set_shapes_out(shapes_out)

    def forward(self, *inputs):
        left_out = self.left.forward(*inputs)
        right_out = self.right.forward(*left_out)
        return right_out

    def infer_shape(self):
        self.left.infer_shape()
        self.right.infer_shape()
        left_shape, right_shape = self.left.get_shapes_out(), self.right.get_shapes_in()
        if left_shape == right_shape == None:
            return
        elif left_shape == None:
            self.left.set_shapes_out(right_shape)
        elif right_shape == None:
            self.right.set_shapes_in(left_shape)
        else:
            if len(left_shape) != len(right_shape):
                raise Exception("shape mismatch")
            new_shape = []
            for l, r in zip(left_shape, right_shape):
                new_shape.append(l.unify(r))
            self.left.set_shapes_out(new_shape)
            self.right.set_shapes_in(new_shape)
        self.left.infer_shape()
        self.right.infer_shape()

    def __repr__(self):
        return "%s >> %s" % (self.left, self.right)
