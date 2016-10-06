
"""
Usage::

    import install_pyenv
    install_pyenv.install("3.4.5")

"""

import os
import sys

from subprocess import check_call


def _log(*args):
    print(" ".join(args))
    sys.stdout.flush()


def install(py_version):
    """Download and install ``pyenv``."""

    check_call(
        "\n".join((
            "brew update",
            "brew outdated pyenv || brew upgrade pyenv",
            "eval \"$( pyenv init - )\"",
            "pyenv install " + py_version,
            "pyenv local " + py_version,
            "echo 'Python Version:'",
            (
                "python -c \""
                "import sys, struct ; "
                "print(sys.version) ; "
                "print('{}-bit'.format(struct.calcsize('P') * 8))"
                "\""
            )
        )),
        shell=True
    )


if __name__ == '__main__':
    install(os.environ['PYTHONVERSION'])
