# -*- coding: utf-8 -*-

"""
Ci command line tool (enable python -m ci syntax)
"""

import ci
import os


def main():
    """The main entry point to ``ci.py``.

    This is installed as the script entry point.
    """

    import argparse

    version_str = ("This is scikit-ci version %s, imported from %s\n" %
                   (ci.__version__, os.path.abspath(ci.__file__)))

    parser = argparse.ArgumentParser(description=ci.__doc__)
    parser.add_argument(
        "steps", type=str, choices=ci.STEPS, nargs='+',
        help="name of the steps to execute")
    parser.add_argument(
        "--version", action="version",
        version=version_str,
        help="display scikit-ci version and import information.")
    args = parser.parse_args()

    for step in args.steps:
        ci.execute_step(step)


if __name__ == '__main__':
    main()
