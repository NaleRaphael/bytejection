import dis
import sys
from types import CodeType, FunctionType

__all__ = ['update_function']


i2b = lambda x: x.to_bytes(1, byteorder=sys.byteorder)
b2i = lambda x: int.from_bytes(x, byteorder=sys.byteorder)
OPMAP = dis.opmap
IOPMAP = {v: k for k, v in OPMAP.items()}
INS_END = i2b(0)    # INSTRUCTION_END


COMP_INST = {
    'LOAD_GLOBAL': ['LOAD_GLOBAL', 'LOAD_NAME'],
    'LOAD_FAST': ['LOAD_FAST', 'LOAD_NAME'],
}


def _update_meta_globals(f, val):
    attr = getattr(f, '__globals__')
    if not isinstance(val, dict):
        raise TypeError('Given `val` should be a `dict`.')
    attr.update(val)
    return attr


def _update_meta_name(f, val):
    if not isinstance(val, str):
        raise TypeError('Given `val` should be a `str`.')
    return val


def _update_meta_defaults(f, val):
    attr = getattr(f, '__defaults__')
    if not isinstance(val, tuple):
        raise TypeError('Given `val` should be a `tuple`.')
    if len(val) != len(attr):
        raise ValueError('Length of given `val` does not meet with the orignal one.')
    attr.update(val)
    return attr


def _update_meta_closure(f, val):
    if not isinstance(val, tuple):
        raise TypeError('Given `val` should be a `tuple`')
    return val


UPDATE_META = {
    '__globals__': _update_meta_globals,
    '__name__': _update_meta_name,
    '__defaults__': _update_meta_defaults,
    '__closure__': _update_meta_closure,
}

def update_function(f, **kwargs):
    old = f.__code__
    attrs = [
        'co_argcount', 'co_kwonlyargcount', 'co_nlocals',
        'co_stacksize', 'co_flags', 'co_code', 'co_consts',
        'co_names', 'co_varnames', 'co_filename', 'co_name',
        'co_firstlineno', 'co_lnotab', 'co_freevars', 'co_cellvars'
    ]
    new = CodeType(*(kwargs.get(attr, getattr(old, attr)) for attr in attrs))

    meta_names = ['__globals__', '__name__', '__defaults__', '__closure__']
    new_meta = []
    for name in meta_names:
        val = kwargs.get(name)
        new_meta.append(getattr(f, name) if val is None else UPDATE_META[name](f, val))
    import pdb; pdb.set_trace()
    return FunctionType(*tuple([new] + new_meta))


def iscompatible(tgt, src):
    return True if (tgt == src or IOPMAP[tgt] in COMP_INST[IOPMAP[src]]) else False


def search_name(co, inst, idx):
    if inst == OPMAP['LOAD_GLOBAL']:
        return ('LOAD_GLOBAL', 'co_names', idx)
    elif inst == OPMAP['LOAD_FAST']:
        return ('LOAD_FAST', 'co_varnames', idx)
    else:
        return None


class COMap(object):
    def __init__(self):
        pass

    @classmethod
    def positioning(cls, co_src, co_tgt):
        # src: LOAD_GLOBAL -> tgt: LOAD_GLOBAL, LOAD_NAME
        # src: LOAD_FAST -> tgt: LOAD_FAST, LOAD_NAME
        code_src = co_src.co_code
        code_tgt = co_tgt.co_code

        pairs = []
        pos = 0
        import pdb; pdb.set_trace()

        # 1. based on `co_tgt`, find the begining location of the first line of `co_tgt` in `co_src`
        while pos < len(code_tgt):
            tgt_inst, tgt_idx = code_tgt[pos], code_tgt[pos+1]
            if src_inst == OPMAP['CALL_FUNCTION']:
                break

            while p < len(code_src):
                src_inst, src_idx = code_src[pos], code_src[pos+1]
                if not iscompatible(tgt_inst, src_inst):
                    p += 2
                    continue
                pass

        # rewrite the following code
        while pos < len(code_src):
            src_inst, src_idx = code_src[pos], code_src[pos+1]
            tgt_inst, tgt_idx = code_tgt[pos], code_tgt[pos+1]
            # 1. check whether `tgt_inst` is a compatible instruction of `src_inst`
            if not iscompatible(tgt_inst, src_inst):
                pos += 2
                continue

            # 2. find the variable set of which `src_idx` and `tgt_idx` locate
            src_idx_info = search_name(co_src, src_inst, src_idx)

            if src_inst == OPMAP['CALL_FUNCTION']:
                break
            pos += 2


class COManipulator(object):
    def __init__(self, func):
        self._f = func

    @property
    def ori_func(self):
        return self._f

    # def replace_method(self, src, tgt):
    #     _src = compile(src, '<string>', 'exec')
    #     _tgt = compile(tgt, '<string>', 'exec')

    #     comap = COMap.positioning(self.fc, _src)

    def update_function(self, target_name, new_func, rename=False):
        # TODO: make this workable with `mod.func` or `mod.submod.func`
        co = self._f.__code__
        new_name = new_func.__name__
        if target_name not in co.co_names:
            raise ValueError('Given `target_name` does not exist in {}.'.format(self._f))

        idx = co.co_names.index(target_name)
        new_co_names = (co.co_names[:idx] + (new_name,) + co.co_names[idx+1:])
        new_globals = {} if new_name in self._f.__globals__ else {new_name: new_func}
        new_name = new_name if rename else self._f.__name__

        return update_function(
            self._f,
            co_names=new_co_names,
            co_name=new_name,
            __globals__=new_globals,
            __name__=new_name,
        )

    def reset(self):
        pass


def modify(f, src, target):
    """
    Parameters
    ----------
    f : function
    src : string
    target: string

    Reference
    ---------
    https://stackoverflow.com/questions/2904274/globals-and-locals-in-python-exec
    """
    fc = f.__code__

    consts = fc.co_consts
    stacksize = fc.co_stacksize
    payload = fc.co_code

    _src = compile(src, '<string>', 'exec')
    _target = compile(target, '<string>', 'exec')

    # e: 101, x65 -> 'LOAD_NAME'
    # j: 106, x6A -> 'LOAD_ATTR'
    # t: 116, x74 -> 'LOAD_GLOBAL'
    # x83 -> 'CALL_FUNCTION'

    import pdb; pdb.set_trace()
    result = COMap.positioning(fc, _src)
    # idx = payload.index(_src.co_code)
