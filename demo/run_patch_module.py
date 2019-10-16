import os.path as osp

try:
    import bytejection
    _MODULE_INSTALLED = True
except (ModuleNotFoundError, ImportError) as ex:
    # Fallback to import from source directory
    _MODULE_INSTALLED = False
    import sys
    sys.path.insert(0, osp.abspath(osp.join(osp.dirname(__file__), '..')))

from bytejection import COManipulator
from bytejection.io import COWritter

if not _MODULE_INSTALLED:
    sys.path.pop(0)
    del sys


def load_module_from_path(name, path):
    import imp
    fo, fn, info = imp.find_module(name, [path])
    return imp.load_module(name, fo, fn, info)


def main():
    try:
        import foobarbuzz.core as mod
    except ModuleNotFoundError:
        mod = load_module_from_path('foobarbuzz', osp.join(osp.dirname(__file__), 'pkg'))
        mod = mod.core

    # Check the output of original function
    print('--- original version ---')
    mod.foo()

    # Payload to be injected
    def new_verification():
        print('... Content has been modified ...')

    com = COManipulator()

    co_module = com.patch_module(
        mod, mod.foo, 'verification', ('new_verification', new_verification)
    )
    COWritter.to_pyc('./modified.pyc', co_module)

    # Check the output of modified function
    print('--- modified version ---')
    modified_mod = load_module_from_path('modified', osp.dirname(__file__))
    modified_mod.foo()


if __name__ == '__main__':
    main()
