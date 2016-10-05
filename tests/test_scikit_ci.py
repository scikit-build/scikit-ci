
import os
import pytest
import shlex
import subprocess
import sys
import textwrap


def _generate_scikit_yml_content():
    template_step = (
        """
        {what}:

          environment:
            WHAT: {what}
          commands:
            - python -c 'import os; print("%s" % os.environ["WHAT"])'
            - python -c "import os; print('expand:%s' % \\"$<WHAT>\\")"
            - python -c 'import os; print("expand-2:%s" % "$<WHAT>")'
            - python --version

          appveyor:
            environment:
              SERVICE: appveyor
            commands:
              - python -c 'import os; print("%s / %s" % (os.environ["WHAT"], os.environ["SERVICE"]))'

          circle:
            environment:
              SERVICE: circle
            commands:
              - python -c 'import os; print("%s / %s" % (os.environ["WHAT"], os.environ["SERVICE"]))'

          travis:
            linux:
              environment:
                SERVICE: travis-linux
              commands:
                - python -c 'import os; print("%s / %s / %s" % (os.environ["WHAT"], os.environ["SERVICE"], os.environ["TRAVIS_OS_NAME"]))'
            osx:
              environment:
                SERVICE: travis-osx
              commands:
                - python -c 'import os; print("%s / %s / %s" % (os.environ["WHAT"], os.environ["SERVICE"], os.environ["TRAVIS_OS_NAME"]))'
        """
    )

    template = (
        """
        schema_version: "0.5.0"
        {}
        """
    )

    return textwrap.dedent(template).format(
            "".join(
                [textwrap.dedent(template_step).format(what=step) for step in
                       ['before_install',
                        'install',
                        'before_build',
                        'build',
                        'test',
                        'after_test']
                 ]
            )
    )


@pytest.mark.parametrize("service",
                         ['appveyor', 'circle', 'travis'])
def test_scikit_ci(service, tmpdir):

    driver_script = os.path.join(os.path.dirname(__file__), '../ci/driver.py')

    tmpdir.join('scikit-ci.yml').write(
        _generate_scikit_yml_content()
    )

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
        env_json = tmpdir.join("env.json")
        if env_json.exists():
            env_json.remove()

        if system:
            environment[osenv[system]] = system

        for step in [
                'before_install',
                'install',
                'before_build',
                'build',
                'test',
                'after_test']:

            cmd = "python %s %s" % (driver_script, step)
            output = subprocess.check_output(
                shlex.split(cmd),
                env=environment,
                stderr=subprocess.STDOUT,
                cwd=str(tmpdir)
            ).strip()

            second_line = "%s / %s" % (step, service)
            if system:
                second_line = "%s-%s / %s" % (second_line, system, system)

            print(output)

            expected_output = "\n".join([
                "%s" % step,
                "expand: %s" % step,
                "expand-2:%s" % (step if service == 'appveyor' else "$<WHAT>"),
                "Python %d.%d.%d" % (sys.version_info[:3]),
                second_line
            ])

            assert output == expected_output
