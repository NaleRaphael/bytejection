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
        import imp
        import struct, time

        marshalled_co = marshal.dumps(co)
        magic_number = imp.get_magic()
        timestamp = struct.pack('i', int(time.time()))
        padding = b'A\x00\x00\x00'

        with open(fn, 'wb') as f:
            f.write(magic_number)
            f.write(timestamp)
            f.write(padding)
            f.write(marshalled_co)
