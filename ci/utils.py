
import os

from constants import SERVICES, SERVICES_ENV_VAR


def current_service():
    for service in SERVICES.keys():
        if os.environ.get(
                SERVICES_ENV_VAR[service], 'false').lower() == 'true':
            return service
    raise Exception(
        "unknown service: None of the environment variables {} "
        "is set to 'true'".format(", ".join(SERVICES_ENV_VAR.values()))
    )


def current_operating_system(service):
    return os.environ[SERVICES[service]] if SERVICES[service] else None
