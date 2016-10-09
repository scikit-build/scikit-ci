
import os

try:
    from .constants import SERVICES, SERVICES_ENV_VAR
except (SystemError, ValueError):
    from constants import SERVICES, SERVICES_ENV_VAR


def current_service():
    for service in SERVICES.keys():
        if os.environ.get(
                SERVICES_ENV_VAR[service], 'false').lower() == 'true':
            return service
    raise LookupError(
        "unknown service: None of the environment variables {} are set "
        "to 'true' or 'True'".format(", ".join(SERVICES_ENV_VAR.values()))
    )


def current_operating_system(service):
    return os.environ[SERVICES[service]] if SERVICES[service] else None
