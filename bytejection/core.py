import dis
import re
import sys
from types import CodeType, FunctionType

__all__ = ['update_function', 'COManipulator']


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


def inject_load_inst(co, old_name, new_name, new_co_names):
    list_old_name = old_name.split('.')
    list_new_name = new_name.split('.')

    inst_load = '([{}|{}])'.format(
        i2b(OPMAP['LOAD_GLOBAL']).decode(), i2b(OPMAP['LOAD_NAME']).decode()
    )
    pattern = ''.join([inst_load + i2b(co.co_names.index(part)).decode() for part in list_old_name])
    regex = re.compile(pattern.encode())
    code = co.co_code

    inst_load_global = i2b(OPMAP['LOAD_GLOBAL']).decode()
    inst_load_attr = i2b(OPMAP['LOAD_ATTR']).decode()

    for matched in regex.finditer(code):
        start, end = matched.span()
        payload = ''.join([inst_load_global + i2b(new_co_names.index(name)).decode() for name in list_new_name[:-1]])
        payload += inst_load_attr + i2b(new_co_names.index(list_new_name[-1])).decode()
        code = code[:start] + payload.encode() + code[end:]
    return code


class COManipulator(object):
    def __init__(self, func):
        self._f = func

    @property
    def ori_func(self):
        return self._f

    def update_function(self, old_name, func_tuple, rename=False, **kwargs):
        co = self._f.__code__
        new_name, new_func = func_tuple
        splitted_old_name = old_name.split('.')
        splitted_new_name = new_name.split('.')

        if not all([part in co.co_names for part in splitted_old_name]):
            raise ValueError('Given `old_name` does not exist in {}.'.format(self._f))

        idx = co.co_names.index(splitted_old_name[-1])
        new_co_names = (co.co_names[:idx] + (splitted_new_name[-1],) + co.co_names[idx+1:])

        # inject new namespaces (e.g. module, class...) and loading instruction (e.g. `LOAD_GLOBAL`...)
        new_co_code = co.co_code
        if len(splitted_new_name) > len(splitted_old_name):
            new_co_names = tuple(list(new_co_names) + splitted_new_name[:-1])
            new_co_code = inject_load_inst(co, old_name, new_name, new_co_names)

        # inject new modules / variables from into global scope
        new_globals = kwargs.get('__globals__', {})
        if new_name not in self._f.__globals__:
            new_globals.update({new_name: new_func})

        new_name = new_name if rename else self._f.__name__

        return update_function(
            self._f,
            co_names=new_co_names,
            co_name=new_name,
            co_code=new_co_code,
            __globals__=new_globals,
            __name__=new_name,
        )
