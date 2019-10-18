import dis
import re
import sys
from types import CodeType, FunctionType, ModuleType

__all__ = [
    'update_function', 'COManipulator',
    'inject_function'
]


i2b = lambda x: x.to_bytes(1, byteorder=sys.byteorder)
b2i = lambda x: int.from_bytes(x, byteorder=sys.byteorder)
OPMAP = dis.opmap
IOPMAP = {v: k for k, v in OPMAP.items()}
INS_END = i2b(0)    # INSTRUCTION_END

CO_ATTRS = [
    'co_argcount', 'co_kwonlyargcount', 'co_nlocals',
    'co_stacksize', 'co_flags', 'co_code', 'co_consts',
    'co_names', 'co_varnames', 'co_filename', 'co_name',
    'co_firstlineno', 'co_lnotab', 'co_freevars', 'co_cellvars'
]

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

META = {
    'function': [
        '__globals__', '__name__', '__defaults__', '__closure__'
    ],
    'module': [
        '__name__'
    ],
}

def _get_code(obj):
    if hasattr(obj, '__code__'):
        return getattr(obj, '__code__')
    elif hasattr(obj, '__loader__'):
        return getattr(obj, '__loader__').get_code(None)
    else:
        raise ValueError('Cannot get code object from this object.')


def update_object(obj, _type, **kwargs):
    old = _get_code(obj)
    new = CodeType(*(kwargs.get(attr, getattr(old, attr)) for attr in CO_ATTRS))
    meta_names = META[type(obj).__name__]
    new_meta = []
    for name in meta_names:
        val = kwargs.get(name)
        new_meta.append(getattr(obj, name) if val is None else UPDATE_META[name](obj, val))
    return _type(*tuple([new] + new_meta))


def update_function(f, **kwargs):
    return update_object(f, FunctionType, **kwargs)


def update_module(mod, **kwargs):
    return update_object(mod, ModuleType, **kwargs)


def iscompatible(tgt, src):
    return (tgt == src or IOPMAP[tgt] in COMP_INST[IOPMAP[src]])


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


def inject_bytecode(co, target_name, bc_payload):
    list_target_name = target_name.split('.')
    inst_load = inst_load = '([{}|{}])'.format(
        i2b(OPMAP['LOAD_GLOBAL']).decode(), i2b(OPMAP['LOAD_NAME']).decode()
    )
    pattern = ''.join([inst_load + i2b(co.co_names.index(part)).decode() for part in list_target_name])
    regex = re.compile(pattern.encode())
    code = co.co_code

    inst_load_global = i2b(OPMAP['LOAD_GLOBAL']).decode()
    inst_load_attr = i2b(OPMAP['LOAD_ATTR']).decode()

    for matched in regex.finditer(code):
        start, end = matched.span()
        code = code[:start] + bc_payload + code[end:]
    return code


def inject_function(f, target_name, payload_tuple):
    co = f.__code__
    payload_name, payload = payload_tuple

    # Manipulate `co_consts`
    new_co_consts = co.co_consts + tuple([
        payload.__code__, '{}.<locals>.{}'.format(co.co_name, payload_name)
    ])
    idx_payload_co = len(new_co_consts) - 2
    idx_payload_local_name = len(new_co_consts) - 1

    # Manipulate `co_varnames`
    new_co_varnames = co.co_varnames + tuple([payload_name])
    idx_payload_varnames = len(new_co_varnames) - 1

    template_make_function = [
        (OPMAP['LOAD_CONST'], idx_payload_co),
        (OPMAP['LOAD_CONST'], idx_payload_local_name),
        (OPMAP['MAKE_FUNCTION'], 0),
        (OPMAP['STORE_FAST'], idx_payload_varnames),
    ]

    # NOTE: There should be a `0` as an ending instruction in Python 3.5
    if sys.version_info.major == 3 and sys.version_info.minor == 5:
        template_make_function = [v + (0,) for v in template_make_function]

    template_load_function = [
        (OPMAP['LOAD_FAST'], idx_payload_varnames),
    ]
    bc_make_function = b''.join([b''.join(list(map(i2b, v))) for v in template_make_function])
    bc_load_function = b''.join([b''.join(list(map(i2b, v))) for v in template_load_function])

    new_code = inject_bytecode(co, target_name, bc_load_function)
    new_code = b''.join([bc_make_function, new_code])

    return update_function(
        f,
        co_consts=new_co_consts,
        co_varnames=new_co_varnames,
        co_code=new_code,
    )


class COManipulator(object):
    def update_function(self, f, old_name, func_tuple, rename=False, **kwargs):
        co = f.__code__
        new_name, new_func = func_tuple
        splitted_old_name = old_name.split('.')
        splitted_new_name = new_name.split('.')

        if not all([part in co.co_names for part in splitted_old_name]):
            raise ValueError('Given `old_name` does not exist in {}.'.format(f))

        idx = co.co_names.index(splitted_old_name[-1])
        new_co_names = (co.co_names[:idx] + (splitted_new_name[-1],) + co.co_names[idx+1:])

        # inject new namespaces (e.g. module, class...) and loading instruction (e.g. `LOAD_GLOBAL`...)
        new_co_code = co.co_code
        if len(splitted_new_name) > len(splitted_old_name):
            new_co_names = tuple(list(new_co_names) + splitted_new_name[:-1])
            new_co_code = inject_load_inst(co, old_name, new_name, new_co_names)

        # inject new modules / variables from into global scope
        new_globals = kwargs.get('__globals__', {})
        if new_name not in f.__globals__:
            new_globals.update({new_name: new_func})

        new_name = new_name if rename else f.__name__

        return update_function(
            f,
            co_names=new_co_names,
            co_name=new_name,
            co_code=new_co_code,
            __globals__=new_globals,
            __name__=new_name,
        )

    def patch_module(self, module, f, old_name, func_tuple, rename=False, **kwargs):
        payload_name, payload = func_tuple
        new_func = inject_function(f, old_name, func_tuple)
        co = _get_code(module)

        # find index of target code object
        target_name = new_func.__code__.co_name
        index = None
        for i, v in enumerate(co.co_consts):
            co_name = getattr(v, 'co_name', None)
            if co_name is None or co_name != target_name:
                continue
            else:
                index = i
                break
        if index is None:
            raise RuntimeError('Desired function does not exist in given module.')

        new_co_consts = tuple(
            co.co_consts[:index] + tuple([new_func.__code__]) + co.co_consts[index+1:]
        )

        payloads = {
            'co_consts': new_co_consts,
            'co_names': co.co_names + tuple([payload_name])
        }

        new_co_module = CodeType(
            *(kwargs.get(attr, getattr(co, attr) if attr not in payloads else payloads.get(attr))
            for attr in CO_ATTRS)
        )
        return new_co_module
