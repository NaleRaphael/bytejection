from subprocess import Popen
import shlex
import shutil
from os import makedirs
from os import path as osp
from pathlib import Path as pl_path
import re


def main():
    package_name = 'foobarbuzz'
    dir_target = './{}'.format(package_name)
    cmds = [
        'python -m compileall {}'.format(dir_target),
    ]

    for cmd in cmds:
        proc = Popen(shlex.split(cmd))
        proc.wait()

    dir_dist = './foobarbuzz/dist'
    if not osp.exists(dir_dist):
        makedirs(dir_dist)

    regex = re.compile('.cpython-\d{2}')

    pyc_files = list(pl_path(osp.abspath(dir_target)).glob('**/__pycache__/*.pyc'))
    for f in pyc_files:
        parts = f.parts
        idx = parts.index('__pycache__')
        parts = parts[:idx] + parts[idx+1:]
        idx = parts.index(package_name)
        parts = parts[:idx+1] + ('dist',) + parts[idx+1:]

        f_target = regex.sub('', osp.join(*parts))
        print('Moving file from {} to {}'.format(f, f_target))
        if not osp.exists(osp.dirname(f_target)):
            makedirs(osp.dirname(f_target))
        shutil.move(f, f_target)


if __name__ == '__main__':
    main()
