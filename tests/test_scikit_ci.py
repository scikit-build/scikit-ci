
import os
import pytest
import shlex
import subprocess
import sys


@pytest.mark.parametrize("service",
                         ['appveyor', 'circle', 'travis'])
def test_scikit_ci(service):

    # Set variable like CIRCLE="true" allowing to test for the service
    environment = dict(os.environ)
    environment[service.upper()] = "true"

    # By default, a service is associated with only one "implicit" operating
    # system.
    # Service supporting multiple operating system (e.g travis) should be
    # specified below.
    osenv_per_service = {
        "travis": {"linux": "TRAVIS_OS_NAME", "osx": "TRAVIS_OS_NAME"}
    }

    systems = [None]

    osenv = osenv_per_service.get(service, {})
    if osenv:
        systems = osenv.keys()

    for system in systems:

        # Remove leftover 'env.json'
        if os.path.exists("env.json"):
            os.remove("env.json")

        if system:
            environment[osenv[system]] = system

        for step in [
                'before_install',
                'install',
                'before_build',
                'build',
                'test',
                'after_test']:

            cmd = "python ci/driver.py %s" % step
            output = subprocess.check_output(
                shlex.split(cmd),
                env=environment,
                stderr=subprocess.STDOUT).strip()

            second_line = "%s / %s" % (step, service)
            if system:
                second_line = "%s-%s / %s" % (second_line, system, system)

            print(output)

            expected_output = "\n".join([
                "%s" % step,
                "Python %d.%d.%d" % (sys.version_info[:3]),
                second_line
            ])

            assert output == expected_output
