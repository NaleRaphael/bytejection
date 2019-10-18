# bytejection - Bytecode injection

## Preface
To modify the implementation of a function persistently without changing the source code directly, we have to manipulate the bytecode generated from source.

Here is an extremely simplified workflow of Python:

```raw
----------            ------------
| source |  compiled  | bytecode |  executed by VM
|  (.py) |  ------->  |  (.pyc)  |  ------------->
----------            ------------
                        ↑ inject our payload here
```

## Demonstration
There is a sample module `foobarbuzz` created for demonstration, you play with it by running the script `demo/run_patch_module.py`. (or you can just check it on [repl.it](https://repl.it/@naleraphael/bytejection))

In the module `foobarbuzz`, there is a function `foo` which will call another function `verification` for some purposes (although it does nothing here).

In our scenario, we want to change the behavior of `verification` called by `foo`. So that we create a new implementation:

```python
# in 'demo/run_patch_module.py'
def new_verification():
    print('... Content has been modified ...')
```

Then, we use `COManipulator.patch_module()` to inject our new implementation to replace the original `verification` called by `foo`, and dump the modified module to a `.pyc` file by `COWriter.to_pyc()`.

---

And here is the output after the script is executed:

```raw
--- original version ---
foo
--- modified version ---
... Content has been modified ...
foo
```