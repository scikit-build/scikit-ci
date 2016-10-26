# -*- coding: utf-8 -*-

"""
Ci command line tool (enable python -m ci syntax)
"""

import argparse
import ci
import os


class _OptionalChoices(argparse.Action):
    """Custom action making a positional argument with choices optional.

    Possible choices should be set with:
    - ``default`` attribute set as a list
    - ``nargs`` attribute set to ``'*'``

    Setting the ``choices`` attribute will fail with an *invalid choice* error.

    Adapted from http://stackoverflow.com/questions/8526675/python-argparse-optional-append-argument-with-choices/8527629#8527629
    """  # noqa: E501
    def __call__(self, parser, namespace, values, option_string=None):
        if values:
            for value in values:
                if value not in self.default:
                    message = ("invalid choice: {0!r} (choose from {1})"
                               .format(value,
                                       ', '.join([repr(action)
                                                  for action in
                                                  self.default])))

                    raise argparse.ArgumentError(self, message)
            setattr(namespace, self.dest, values)


def main():
    """The main entry point to ``ci.py``.

    This is installed as the script entry point.
    """

    version_str = ("This is scikit-ci version %s, imported from %s\n" %
                   (ci.__version__, os.path.abspath(ci.__file__)))

    parser = argparse.ArgumentParser(description=ci.__doc__)
    parser.add_argument(
        "steps", type=str, nargs='*', default=ci.STEPS,
        action=_OptionalChoices, metavar='STEP',
        help="name of the steps to execute. "
             "Choose from: {}. "
             "If not steps are specified, all are executed.".format(", ".join(
                [repr(action) for action in ci.STEPS]))
    )
    parser.add_argument(
        "--version", action="version",
        version=version_str,
        help="display scikit-ci version and import information.")
    args = parser.parse_args()

    for step in args.steps:
        ci.execute_step(step)


if __name__ == '__main__':
    main()
