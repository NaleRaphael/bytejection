import importlib.util as imp_util
from bytejection import COManipulator


def load_module_from_pyc(fn, module_name):
    spec = imp_util.spec_from_file_location(module_name, fn)
    mod = imp_util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    fn = './foobarbuzz/dist/src/core.pyc'
    mod = load_module_from_pyc(fn, 'foobarbuzz.core')

    print('--- original version ---')
    mod.foo()
    print('------------------------\n')

    def new_verification():
        raise RuntimeError('This function should not be executed.')

    print('--- modified version ---')
    com = COManipulator(mod.foo)
    updated = com.update_function('verification', ('new_verification', new_verification))
    updated()


if __name__ == '__main__':
    main()
