# -*- coding: utf-8 -*-

"""
Ci command line tool (enable python -m ci syntax)
"""

import argparse
import ci
import os


class _OptionalStep(argparse.Action):
    """Custom action making the ``step`` positional argument with choices
    optional.

    Setting the ``choices`` attribute will fail with an *invalid choice* error.

    Adapted from http://stackoverflow.com/questions/8526675/python-argparse-optional-append-argument-with-choices/8527629#8527629
    """  # noqa: E501
    def __call__(self, parser, namespace, value, option_string=None):
        if value:
            if value not in ci.STEPS:
                message = ("invalid choice: {0!r} (choose from {1})"
                           .format(value,
                                   ', '.join([repr(action)
                                              for action in
                                              ci.STEPS])))

                raise argparse.ArgumentError(self, message)
            setattr(namespace, self.dest, value)


def main():
    """The main entry point to ``ci.py``.

    This is installed as the script entry point.
    """

    version_str = ("This is scikit-ci version %s, imported from %s\n" %
                   (ci.__version__, os.path.abspath(ci.__file__)))

    parser = argparse.ArgumentParser(description=ci.__doc__)
    parser.add_argument(
        "step", type=str, nargs='?', default=ci.STEPS[-1],
        action=_OptionalStep, metavar='STEP',
        help="name of the step to execute. "
             "Choose from: {}. "
             "If no step is specified, all are executed.".format(", ".join(
                [repr(action) for action in ci.STEPS]))
    )
    parser.add_argument(
        "--force", action="store_true",
        help="always execute the steps"
    )
    parser.add_argument(
        "--without-deps", action="store_false",
        help="do not execute dependent steps", dest='with_dependencies'
    )
    parser.add_argument(
        "--clear-cached-env", action="store_true",
        help="clear cached environment (removes 'env.json' file)"
    )
    parser.add_argument(
        "--version", action="version",
        version=version_str,
        help="display scikit-ci version and import information.")
    args = parser.parse_args()

    try:
        ci.execute_step(
            args.step,
            force=args.force,
            with_dependencies=args.with_dependencies,
            clear_cached_env=args.clear_cached_env
        )
    except ci.SKCIError as exc:
        exit(exc)


if __name__ == '__main__':  # pragma: no cover
    main()
