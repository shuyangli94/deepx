# DeepX [![Build Status](https://travis-ci.org/sharadmv/deepx.svg?branch=master)](https://travis-ci.org/sharadmv/deepx) [![Coverage Status](https://coveralls.io/repos/sharadmv/deepx/badge.svg?branch=master&service=github)](https://coveralls.io/github/sharadmv/deepx?branch=master) [![PyPI](https://img.shields.io/pypi/v/deepx.svg)](https://pypi.python.org/pypi/deepx)
DeepX is a deep learning library designed with flexibility and succinctness in mind.
The key aspect is an expressive shorthand to describe your neural network architecture.

DeepX supports both [Theano](http://deeplearning.net/software/theano/) and [Tensorflow](http://www.tensorflow.org).

Installation
====================================

```
$ pip install deepx
```

Quickstart
=================================

The first step in building your first network is to define your *model*.
The model is the input-output structure of your network.
Let's consider the task of classifying MNIST with a multilayer perceptron (MLP).

```python
>>> from deepx.nn import *
>>> net = Relu(200) >> Relu(200) >> Softmax(10)
```

Our model acts like a normal Tensorflow/Theano function.
```python
>>> import tensorflow as tf
>>> net(tf.ones((10, 784)))
```

That's it, we're done!
