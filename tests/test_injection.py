import pytest
from bytejection import COManipulator
from .funcs import (
    py_mul_2_3, py_add_2_3, np_mul_2_3, np_add_2_3,
    entry_py_mul_2_3, entry_py_add_2_3,
)


def test_convert_mul_to_add():
    com = COManipulator(entry_py_mul_2_3)
    updated = com.update_function('py_mul_2_3', ('py_add_2_3', py_add_2_3))
    assert entry_py_mul_2_3() == 6
    assert updated() == 5


def test_injection_with_module_name():
    com = COManipulator(entry_py_mul_2_3)
    updated = com.update_function('py_mul_2_3', ('np_add_2_3', np_add_2_3))
    assert entry_py_mul_2_3() == 6
    assert updated() == 5
