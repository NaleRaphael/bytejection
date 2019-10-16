import sys
if sys.version_info.major < 3 or sys.version_info.minor <= 4:
    import imp
    PY_MAGIC_NUMBER = imp.get_magic()
    del imp
else:
    import importlib.util
    PY_MAGIC_NUMBER = importlib.util.MAGIC_NUMBER
    del importlib.util
del sys


__all__ = ['COWritter']


class COWritter(object):
    @classmethod
    def to_pyc(cls, fn, co):
        """
        Dump code object to a .pyc file.

        Parameters
        ----------
        fn : string
            File name of .pyc file.
        co : code object
            Code object to be dumped.

        Note
        ----
        See also: `importlib._bootstrap_external._code_to_bytecode()`
        """
        import marshal
        import struct, time

        marshalled_co = marshal.dumps(co)
        magic_number = PY_MAGIC_NUMBER
        timestamp = struct.pack('i', int(time.time()))
        padding = b'A\x00\x00\x00'

        with open(fn, 'wb') as f:
            f.write(magic_number)
            f.write(timestamp)
            f.write(padding)
            f.write(marshalled_co)
