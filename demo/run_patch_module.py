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
from bytejection.io import COWriter

if not _MODULE_INSTALLED:
    sys.path.pop(0)
    del sys


def _load_module_deprecated(name, path):
    import imp
    fo, fn, info = imp.find_module(name, [path])
    return imp.load_module(name, fo, fn, info)


def _load_module(name, path):
    from importlib import util as im_util
    spec = im_util.spec_from_file_location(name, path, submodule_search_locations=[])
    if spec is not None:
        mod = im_util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    else:
        mod = None
    return mod


def load_module_from_path(name, path):
    from sys import version_info
    if version_info.major < 3 or version_info.minor < 4:
        mod = _load_module_deprecated(name, path)
    else:
        mod = _load_module(name, path)
    return mod


def main():
    try:
        import foobarbuzz.core as mod
    except ModuleNotFoundError:
        mod_path = osp.join(osp.dirname(__file__), 'pkg', 'foobarbuzz', 'core.py')
        mod = load_module_from_path('foobarbuzz.core', mod_path)

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
    COWriter.to_pyc('./modified.pyc', co_module)

    # Check the output of modified function
    print('--- modified version ---')
    modified_mod = load_module_from_path('modified', osp.join(osp.dirname(__file__), 'modified.pyc'))
    modified_mod.foo()


if __name__ == '__main__':
    main()
