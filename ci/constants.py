# -*- coding: utf-8 -*-

SCIKIT_CI_CONFIG = "scikit-ci.yml"
"""Name of the configuration."""

SERVICES = {
    "appveyor": None,
    "azure": "AGENT_OS",
    "circle": None,
    "travis": "TRAVIS_OS_NAME"
}
"""Describes the supported services.

Service associated with only one "implicit" operating system
are associated with the value ``None``.

Service supporting multiple operating systems (e.g. travis) are
associated with the name of environment variable describing the
operating system in use. (e.g ``TRAVIS_OS_NAME``).
"""

SERVICES_ENV_VAR = {
    "appveyor": "APPVEYOR",
    "azure": "TF_BUILD",
    "circle": "CIRCLECI",
    "travis": "TRAVIS",
}

STEPS = [
    "before_install",
    "install",
    "before_build",
    "build",
    "test",
    "after_test"
]
"""Name of the CI steps.

These are the scikit-ci steps to execute. They are expected to
be mapped to the step recognized by continuous integration
services like Appveyor, Azure Pipelines, CircleCI or TravisCI.
"""
