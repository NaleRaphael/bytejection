from sys import version_info
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


def _w_long(x):
    return (int(x) & 0xFFFFFFFF).to_bytes(4, 'little')


def _code_to_pyc(co, source_size=0):
    data = bytearray(PY_MAGIC_NUMBER)

    # A padding character is added in Python 3.7.
    # https://github.com/python/cpython/blob/3.7/Lib/importlib/_bootstrap_external.py#L539
    if version_info.major < 3 or version_info.minor == 7:
        data.extend(_w_long(0))

    data.extend(_w_long(int(time.time())))
    data.extend(_w_long(source_size))
    data.extend(marshal.dumps(co))
    return data
