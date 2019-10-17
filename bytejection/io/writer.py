from .utils import _code_to_pyc

__all__ = ['COWriter']


class COWriter(object):
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
        with open(fn, 'wb') as f:
            f.write(_code_to_pyc(co))
