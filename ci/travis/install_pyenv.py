
"""
Usage::

    import install_pyenv
    install_pyenv.install("3.4.5")

"""

import os
import sys

from subprocess import check_call


def _log(*args):
    script_name = os.path.basename(__file__)
    print("[travis:%s] " % script_name + " ".join(args))
    sys.stdout.flush()


def install(py_version):
    """Download and install ``pyenv``."""

    _log("Updating pyenv using brew")
    check_call(
        "\n".join((
            "brew update",
            "brew outdated pyenv || brew upgrade pyenv"
        )),
        shell=True
    )

    _log("Checking that requested python version", py_version, "works")
    check_call(
        "\n".join((
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
