# -*- coding: utf-8 -*-

"""
Ci command line tool (enable python -m ci syntax)
"""

import ci


def main():
    """The main entry point to ``ci.py``.

    This is installed as the script entry point.
    """

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "step", type=str, choices=ci.STEPS,
        help="name of the step to execute")
    args = parser.parse_args()

    ci.execute_step(args.step)


if __name__ == '__main__':
    main()
