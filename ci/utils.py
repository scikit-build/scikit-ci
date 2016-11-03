# -*- coding: utf-8 -*-

"""This module defines functions generally useful in scikit-ci."""

import os

from .constants import SERVICES, SERVICES_ENV_VAR


def current_service():
    for service, env_var in SERVICES_ENV_VAR.items():
        if os.environ.get(env_var, 'false').lower() == 'true':
            return service
    raise LookupError(
        "unknown service: None of the environment variables {} are set "
        "to 'true' or 'True'".format(", ".join(SERVICES_ENV_VAR.values()))
    )


def current_operating_system(service):
    return os.environ[SERVICES[service]] if SERVICES[service] else None


def indent(text, prefix, predicate=None):
    """Adds 'prefix' to the beginning of selected lines in 'text'.
    If 'predicate' is provided, 'prefix' will only be added to the lines
    where 'predicate(line)' is True. If 'predicate' is not provided,
    it will default to adding 'prefix' to all non-empty lines that do not
    consist solely of whitespace characters.

    Copied from textwrap.py available in python 3 (cpython/cpython@a2d2bef)
    """
    if predicate is None:
        def predicate(line):
            return line.strip()

    def prefixed_lines():
        for line in text.splitlines(True):
            yield (prefix + line if predicate(line) else line)
    return ''.join(prefixed_lines())
