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
