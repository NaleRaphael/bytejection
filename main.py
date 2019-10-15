import dis
import numpy as np
from funcs import entry, py_multiply, py_add, np_add
from bytejection import update_function, COManipulator


def main():
    entry()
    com = COManipulator()
    updated = com.update_function(entry, 'py_multiply', ('py_add', py_add))
    updated()

    py_multiply()
    com = COManipulator()
    updated = com.update_function(py_multiply, 'multiply', ('np.add', np.add))
    updated()


if __name__ == '__main__':
    main()
