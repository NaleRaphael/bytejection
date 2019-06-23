import dis
import numpy as np
from types import CodeType, FunctionType
from funcs import entry
from bytejection.core import update_function, COManipulator


def foo():
    print('additional line 01')
    result = np.add(10, 5)
    print(result)
    print('additional line 02')


def main():
    entry()
    # dis.dis(entry)
    # co = entry.__code__
    # bc = co.co_code

    # new_entry = update_function(
    #     entry,
    #     # to replace specific function, rewrite this as an arg taking a dict for mapping
    #     # e.g. co_names={'ori_func': 'foo'}
    #     co_names=('print', 'foo'),
    #     __globals__={'foo': foo},
    # )

    com = COManipulator(entry)
    new_entry = com.update_function('ori_func', foo)
    import pdb; pdb.set_trace()
    pass


if __name__ == '__main__':
    main()
