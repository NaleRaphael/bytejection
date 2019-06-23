import pytest
import numpy as np
from bytejection import modify


def test_convert_np_multiply_to_divide():
    def foo(x, y):
        # print('Nothing special...')
        # ones = np.ones(10)
        # zeros = np.zeros(10)
        result = np.multiply(x, y)
        return result

    # bar = modify(foo, 'np.multiply', 'np.divide')
    bar = modify(foo, 'np.multiply(x, y)', 'np.divide(x, y)')

