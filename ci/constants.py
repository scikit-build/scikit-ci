
"""Name of the configuration."""
SCIKIT_CI_CONFIG = "scikit-ci.yml"

"""Describes the supported services.

Service associated with only one "implicit" operating system
are associated with the value ``None``.

Service supporting multiple operating systems (e.g. travis) are
associated with the name of environment variable describing the
operating system in use. (e.g ``TRAVIS_OS_NAME``).
"""
SERVICES = {
    "appveyor": None,
    "circle": None,
    "travis": "TRAVIS_OS_NAME"
}

SERVICES_ENV_VAR = {
    "appveyor": "APPVEYOR",
    "circle": "CIRCLECI",
    "travis": "TRAVIS",
}

"""Name of the CI steps.

These are the scikit-ci steps to execute. They are expected to
be mapped to the step recognized by continuous integration
services like Appveyor, CircleCI or TravisCI.
"""
STEPS = [
    "before_install",
    "install",
    "before_build",
    "build",
    "test",
    "after_test"
]
