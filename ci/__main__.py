# -*- coding: utf-8 -*-

"""
Ci command line tool (enable python -m ci syntax)
"""

from .constants import STEPS
from .driver import execute_step


def main():
    """The main entry point to ``ci.py``.

    This is installed as the script entry point.
    """

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("step", type=str, choices=STEPS,
                        help="name of the step to execute")
    args = parser.parse_args()

    execute_step(args.step)


if __name__ == '__main__':
    main()
