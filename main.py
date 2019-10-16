from subprocess import Popen
import shlex


def main():
    cmd = 'python demo/run_patch_module.py'
    proc = Popen(shlex.split(cmd))
    proc.wait()


if __name__ == '__main__':
    main()
