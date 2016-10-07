
import os
import platform
import pytest
import subprocess
import sys
import textwrap

from capturer import CaptureOutput

from . import push_dir, push_env
from ci.constants import SERVICES_ENV_VAR
from ci.driver import Driver
from ci.driver import main as ci_driver


def scikit_steps(tmpdir, service):
    """Given ``tmpdir`` and ``service``, this generator yields
    ``(step, system, cmd, environment)`` for all supported steps.
    """
    # Set variable like CIRCLE="true" allowing to test for the service
    environment = dict(os.environ)
    environment[SERVICES_ENV_VAR[service]] = "true"

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

            yield step, system, environment


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
        """  # noqa: E501
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
def test_driver(service, tmpdir):

    tmpdir.join('scikit-ci.yml').write(
        _generate_scikit_yml_content()
    )

    for step, system, environment in scikit_steps(tmpdir, service):

        with push_dir(str(tmpdir)),\
             push_env(**environment), \
             CaptureOutput() as capturer:
            ci_driver(step)
            output = capturer.get_text()

        second_line = "%s / %s" % (step, service)
        if system:
            second_line = "%s-%s / %s" % (second_line, system, system)

        print(output)

        expected_output = "\n".join([
            "%s" % step,
            "expand: %s" % step,
            "expand-2:%s" % (step if service == 'appveyor' else "$<WHAT>"),
            "Python %s" % sys.version.split()[0],
            second_line
        ])

        assert output == expected_output


def test_shell_command(tmpdir):

    if platform.system().lower() == "windows":
        tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
            """
            schema_version: "0.5.0"
            install:
              commands:
                - for %G in (foo bar) do python -c "print('var %G')"
                - "for %G in oof rab; do python -c \\"print('var: %G')\\"; done"
            """
        ))
        service = 'appveyor'
    else:
        tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
            """
            schema_version: "0.5.0"
            install:
              commands:
                - for var in foo bar; do python -c "print('var $var')"; done
                - "for var in oof rab; do python -c \\"print('var: $var')\\"; done"
            """  # noqa: E501
        ))
        service = 'circle'

    for step, system, environment in scikit_steps(tmpdir, service):

        with push_dir(str(tmpdir)), \
             push_env(**environment), \
             CaptureOutput() as capturer:
            ci_driver(step)
            output = capturer.get_text()

        expected_output = "\n".join([
            "var foo",
            "var bar",
            "var: oof",
            "var: rab"
        ]) if step == 'install' else ""

        assert output == expected_output


def test_multi_line_shell_command(tmpdir):
    if platform.system().lower() == "windows":
        tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
            """
            schema_version: "0.5.0"
            install:
              commands:
                - |
                  for % G in (foo bar) do ^
                  python -c "print('var %G')"
            """
        ))
        service = 'appveyor'

    else:
        tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
            """
            schema_version: "0.5.0"
            install:
              commands:
                - |
                  for var in foo bar; do
                    python -c "print('var $var')"
                  done
            """
        ))
        service = 'circle'

    for step, system, environment in scikit_steps(tmpdir, service):

        with push_dir(str(tmpdir)), \
             push_env(**environment), \
             CaptureOutput() as capturer:
            ci_driver(step)
            output = capturer.get_text()

        print(output)

        expected_output = "\n".join([
            "var foo",
            "var bar"
        ]) if step == 'install' else ""

        assert output == expected_output


def _expand_environment_vars_test(command, posix_shell, expected):
    environments = {
        "OTHER": "unused",
        "FO": "foo"
    }
    assert (
        Driver.expand_environment_vars(command, environments, posix_shell)
        == expected)


@pytest.mark.parametrize("command, posix_shell, expected", [
    (r"""echo "$<FO>", "$<B>", $<FO>""", False, 'echo "foo" , "$<B>" , foo'),
    (r"""echo '$<FO>', '$<B>', $<FO>""", False, "echo 'foo' , '$<B>' , foo"),
    (r"""echo "$<FO>", "$<B>", $<FO>""", True, 'echo "foo" , "$<B>" , foo'),
    (r"""echo '$<FO>', '$<B>', $<FO>""", True, "echo '$<FO>' , '$<B>' , foo"),
])
def test_expand_environment_vars(command, posix_shell, expected):
    _expand_environment_vars_test(command, posix_shell, expected)


@pytest.mark.parametrize("command, posix_shell, expected", [
    (r"""echo "$<FO>", \
"$<B>", $<FO>""", True, 'echo "foo" , "$<B>" , foo'),
    (r"""echo '$<FO>', \
'$<B>', $<FO>""", True, "echo '$<FO>' , '$<B>' , foo"),
])
def test_expand_environment_vars_with_newline(command, posix_shell, expected):
    _expand_environment_vars_test(command, posix_shell, expected)


def test_cli(tmpdir):
    tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
        r"""
        schema_version: "0.5.0"
        install:
          commands:
            - "python -c \"with open('install-done', 'w') as file: file.write('')\""
        """  # noqa: E501
    ))
    service = 'circle'

    environment = dict(os.environ)
    environment[SERVICES_ENV_VAR[service]] = "true"

    driver_script = os.path.join(os.path.dirname(__file__), '../ci/driver.py')

    subprocess.check_call(
        "python %s %s" % (driver_script, "install"),
        shell=True,
        env=environment,
        stderr=subprocess.STDOUT,
        cwd=str(tmpdir)
    )

    assert tmpdir.join("install-done").exists()


def test_not_all_operating_system(tmpdir):
    tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
        r"""
        schema_version: "0.5.0"
        install:
          travis:
            osx:
              environment:
                FOO: BAR
        """  # noqa: E501
    ))
    service = 'travis'

    environment = dict(os.environ)
    environment[SERVICES_ENV_VAR[service]] = "true"

    environment["TRAVIS_OS_NAME"] = "linux"

    with push_dir(str(tmpdir)), push_env(**environment):
        ci_driver("install")


def test_environment_persist(tmpdir):
    tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
        r"""
        schema_version: "0.5.0"
        before_install:
          environment:
            FOO: hello
            BAR: world
            EMPTY: ""
          commands:
            - echo "1 [$<FOO>] [$<BAR>] [$<EMPTY>]"
          circle:
            environment:
              BAR: under world
        install:
          environment:
            BAR: beautiful world
          commands:
            - echo "2 [$<FOO>] [$<BAR>] [$<EMPTY>]"
        """
    ))
    service = 'circle'

    environment = dict(os.environ)
    environment[SERVICES_ENV_VAR[service]] = "true"

    with push_dir(str(tmpdir)), push_env(**environment), \
            CaptureOutput() as capturer:
        ci_driver("before_install")
        ci_driver("install")
        output = capturer.get_text()

    expected_output = "\n".join([
        "1 [hello] [under world] []",
        "2 [hello] [beautiful world] []"
    ])

    assert output == expected_output


def test_within_environment_expansion(tmpdir):
    tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
        r"""
        schema_version: "0.5.0"
        before_install:
          environment:
            FOO: hello
            BAR: $<WHAT>
          commands:
            - echo "[$<FOO> $<BAR> $<STRING>]"
            - echo "[\\the\\thing]"
            - echo "[$<FOO_DIR>\\the\\thing]"
        """
    ))
    service = 'circle'

    environment = dict(os.environ)
    environment[SERVICES_ENV_VAR[service]] = "true"

    environment["WHAT"] = "world"
    environment["STRING"] = "of \"wonders\""
    environment["FOO_DIR"] = "C:\\path\\to"

    with push_dir(str(tmpdir)), push_env(**environment), \
            CaptureOutput() as capturer:
        ci_driver("before_install")
        output = capturer.get_text()

    expected_output = "\n".join([
        "[hello world of \"wonders\"]",
        "[\\the\\thing]",
        "[C:\\path\\to\\the\\thing]",
    ])

    assert output == expected_output
