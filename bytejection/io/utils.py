from sys import version_info
import os.path as osp
import marshal
import time

if version_info.major < 3 or version_info.minor <= 4:
    import imp
    PY_MAGIC_NUMBER = imp.get_magic()
    del imp
else:
    from importlib import util as im_util
    PY_MAGIC_NUMBER = im_util.MAGIC_NUMBER
    del im_util


def _code_to_pyc(co, source_size=0):
    import importlib as im
    from importlib import util as im_util

    # Prepare to load some internal functions
    path = osp.join(osp.dirname(im.__file__), '_bootstrap_external.py')
    spec= im_util.spec_from_file_location('imb', path)
    mod = im_util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Inject dependencies to dynamically imported module
    mod.marshal = marshal

    if version_info.major == 3 and version_info.minor == 7:
        func = mod._code_to_timestamp_pyc
    else:
        func = mod._code_to_bytecode

    return func(co)
