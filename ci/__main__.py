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
        "step", type=str, choices=ci.STEPS,
        help="name of the step to execute")
    parser.add_argument(
        "--version", action="version",
        version=version_str,
        help="display scikit-ci version and import information.")
    args = parser.parse_args()

    ci.execute_step(args.step)


if __name__ == '__main__':
    main()
