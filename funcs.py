import numpy as np


def multiply(x, y):
    return x * y


def add(x, y):
    return x + y


def py_multiply():
    print(multiply(2, 3))


def py_add():
    print(add(2, 3))


def np_multiply():
    print(np.multiply(2, 3))


def np_add():
    print(np.add(2, 3))


def entry():
    print('Calling function: py_multiply()')
    py_multiply()
    print('Remaining operations...')
