
import os
import platform
import pytest
import subprocess
import sys
import textwrap

from ruamel.yaml.compat import ordereddict

from . import captured_lines, display_captured_text, push_dir, push_env
from ci.constants import SERVICES, SERVICES_ENV_VAR
from ci.driver import Driver, execute_step
from ci.utils import current_service, current_operating_system

"""Indicate if the system has a Windows command line interpreter"""
HAS_COMSPEC = "COMSPEC" in os.environ

"""Version of the tested scikit-ci schema."""
SCHEMA_VERSION = "0.5.0"


def enable_service(service, environment=os.environ, operating_system=None):
    """Ensure ``service`` is enabled.

    For multi-os services, you are expected to set ``operating_system``.

    Note that before enabling ``service``, the environment variables (including
    the one specifying which OS is enabled) for all services are first removed
    from the ``environment``.
    """
    for any_service in SERVICES:
        if SERVICES_ENV_VAR[any_service] in environment:
            del environment[SERVICES_ENV_VAR[any_service]]
        if SERVICES[any_service]:
            if SERVICES[any_service] in environment:
                del environment[SERVICES[any_service]]
    environment[SERVICES_ENV_VAR[service]] = "true"
    if SERVICES[service]:
        assert operating_system is not None
        environment[SERVICES[service]] = operating_system


@pytest.mark.parametrize("service", SERVICES.keys())
def test_current_service(service):
    with push_env():
        operating_system = "linux" if SERVICES[service] else None
        enable_service(service, operating_system=operating_system)
        assert current_service() == service
        assert current_operating_system(service) == operating_system


def scikit_steps(tmpdir, service):
    """Given ``tmpdir`` and ``service``, this generator yields
    ``(step, system, environment)`` for all supported steps.
    """

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

        # Set variable like CIRCLE="true" allowing to test for the service
        environment = os.environ
        enable_service(service, environment, system)

        for step in [
                'before_install',
                'install',
                'before_build',
                'build',
                'test',
                'after_test']:

            yield step, system, environment


def _generate_scikit_yml_content(service):
    template_step = (
        r"""
        {what}:

          environment:
            WHAT: {what}
          commands:
            - $<PYTHON> -c "import os; print('%s' % os.environ['WHAT'])"
            {command_0}
            {command_1}
            - $<PYTHON> -c "import sys; print('%s.%s.%s' % sys.version_info[:3])"

          appveyor:
            environment:
              SERVICE: appveyor
            commands:
              - $<PYTHON> -c "import os; print('%s / %s' % (os.environ['WHAT'], os.environ['SERVICE']))"

          circle:
            environment:
              SERVICE: circle
            commands:
              - $<PYTHON> -c "import os; print('%s / %s' % (os.environ['WHAT'], os.environ['SERVICE']))"

          travis:
            linux:
              environment:
                SERVICE: travis-linux
              commands:
                - $<PYTHON> -c "import os; print('%s / %s / %s' % (os.environ['WHAT'], os.environ['SERVICE'], os.environ['TRAVIS_OS_NAME']))"
            osx:
              environment:
                SERVICE: travis-osx
              commands:
                - $<PYTHON> -c "import os; print('%s / %s / %s' % (os.environ['WHAT'], os.environ['SERVICE'], os.environ['TRAVIS_OS_NAME']))"
        """  # noqa: E501
    )

    template = (
        """
        schema_version: "{version}"
        {{}}
        """.format(version=SCHEMA_VERSION)
    )

    if HAS_COMSPEC:
        commands = [
            r"""- $<PYTHON> -c "import os; print('expand:%s' % '$<WHAT>')" """,
            r"""- $<PYTHON> -c "import os; print('expand-2:%s' % '$<WHAT>')" """
            ]
    else:
        commands = [
            r"""- $<PYTHON> -c "import os; print('expand:%s' % \"$<WHAT>\")" """,  # noqa: E501
            r"""- $<PYTHON> -c 'import os; print("expand-2:%s" % "$<WHAT>")' """
            ]

    return textwrap.dedent(template).format(
            "".join(
                [textwrap.dedent(template_step).format(
                    what=step,
                    command_0=commands[0],
                    command_1=commands[1]) for step in
                 ['before_install',
                  'install',
                  'before_build',
                  'build',
                  'test',
                  'after_test']
                 ]
            )
    )


@pytest.mark.parametrize("service", SERVICES)
def test_driver(service, tmpdir, capfd):

    tmpdir.join('scikit-ci.yml').write(
        _generate_scikit_yml_content(service)
    )

    outputs = []

    with push_env():

        for step, system, environment in scikit_steps(tmpdir, service):

            if "PYTHON" not in environment:
                environment["PYTHON"] = "python"

            with push_dir(str(tmpdir)), push_env(**environment):
                execute_step(step)
                output_lines, error_lines = captured_lines(capfd)

            outputs.append((step, system, output_lines, error_lines))

    with capfd.disabled():
        for step, system, output_lines, error_lines in outputs:

            second_line = "%s / %s" % (step, service)
            if system:
                second_line = "%s-%s / %s" % (second_line, system, system)

            try:
                extra_space = "" if HAS_COMSPEC else " "
                assert output_lines[1] == "%s" % step
                assert output_lines[3] == "expand:%s%s" % (extra_space, step)
                assert output_lines[5] == "expand-2:%s" % (
                    step if HAS_COMSPEC else "$<WHAT>")
                assert output_lines[7] == "%s.%s.%s" % sys.version_info[:3]
                assert output_lines[9] == second_line
            except AssertionError as error:
                context = service + (("-" + system) if system else "")
                print("\n[%s: %s]" % (context, step))
                display_captured_text(output_lines, error_lines)
                if sys.version_info[0] > 2:
                    raise error.with_traceback(sys.exc_info()[2])
                else:
                    raise


def test_shell_command(tmpdir, capfd):

    if platform.system().lower() == "windows":
        tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
            r"""
            schema_version: "{version}"
            install:
              commands:
                - FOR %G IN (foo bar) DO python -c "print('var %G')"
            """
        ).format(version=SCHEMA_VERSION))
        service = 'appveyor'
    else:
        tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
            r"""
            schema_version: "{version}"
            install:
              commands:
                - for var in foo bar; do python -c "print('var $var')"; done
                - "for var in oof rab; do python -c \"print('var: $var')\"; done"
            """  # noqa: E501
        ).format(version=SCHEMA_VERSION))
        service = 'circle'

    for step, system, environment in scikit_steps(tmpdir, service):

        with push_dir(str(tmpdir)), push_env(**environment):
            execute_step(step)
            output_lines, _ = captured_lines(capfd)

        if step == 'install':
            if platform.system().lower() == "windows":
                assert output_lines[3] == "var foo"
                assert output_lines[6] == "var bar"
            else:
                assert output_lines[1] == "var foo"
                assert output_lines[2] == "var bar"
                assert output_lines[4] == "var: oof"
                assert output_lines[5] == "var: rab"
        else:
            assert output_lines[0] == ''


@pytest.mark.skipif(platform.system().lower() == "windows",
                    reason="not supported")
def test_multi_line_shell_command(tmpdir, capfd):
    if platform.system().lower() == "windows":
        tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
            r"""
            schema_version: "{version}"
            install:
              commands:
                - |
                  for %G in (foo bar) do ^
                  python -c "print('var %G')"
            """
        ).format(version=SCHEMA_VERSION))
        service = 'appveyor'

    else:
        tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
            r"""
            schema_version: "{version}"
            install:
              commands:
                - |
                  for var in foo bar; do
                    python -c "print('var $var')"
                  done
            """
        ).format(version=SCHEMA_VERSION))
        service = 'circle'

    for step, system, environment in scikit_steps(tmpdir, service):

        with push_dir(str(tmpdir)), push_env(**environment):
            execute_step(step)
            output_lines, _ = captured_lines(capfd)

        if step == 'install':
            assert output_lines[3] == "var foo"
            assert output_lines[4] == "var bar"
        else:
            assert output_lines[0] == ''


def _expand_command_test(command, posix_shell, expected):
    environments = {
        "OTHER": "unused",
        "FO": "foo"
    }
    assert (
        Driver.expand_command(command, environments, posix_shell)
        == expected)


@pytest.mark.parametrize("command, posix_shell, expected", [
    (r"""echo "$<FO>", "$<B>", $<FO>""", False, 'echo "foo" , "$<B>" , foo'),
    (r"""echo '$<FO>', '$<B>', $<FO>""", False, "echo 'foo' , '$<B>' , foo"),
    (r"""echo "$<FO>", "$<B>", $<FO>""", True, 'echo "foo" , "$<B>" , foo'),
    (r"""echo '$<FO>', '$<B>', $<FO>""", True, "echo '$<FO>' , '$<B>' , foo"),
])
def test_expand_command(command, posix_shell, expected):
    _expand_command_test(command, posix_shell, expected)


@pytest.mark.parametrize("command, posix_shell, expected", [
    (r"""echo "$<FO>", \
"$<B>", $<FO>""", True, 'echo "foo" , "$<B>" , foo'),
    (r"""echo '$<FO>', \
'$<B>', $<FO>""", True, "echo '$<FO>' , '$<B>' , foo"),
])
def test_expand_command_with_newline(command, posix_shell, expected):
    _expand_command_test(command, posix_shell, expected)


def test_cli(tmpdir):
    tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
        r"""
        schema_version: "{version}"
        install:
          commands:
            - "python -c \"with open('install-done', 'w') as file: file.write('')\""
        """  # noqa: E501
    ).format(version=SCHEMA_VERSION))
    service = 'circle'

    environment = dict(os.environ)
    enable_service(service, environment)

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    environment['PYTHONPATH'] = root

    subprocess.check_call(
        "python -m ci install",
        shell=True,
        env=environment,
        stderr=subprocess.STDOUT,
        cwd=str(tmpdir)
    )

    assert tmpdir.join("install-done").exists()


def test_not_all_operating_system(tmpdir):
    tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
        r"""
        schema_version: "{version}"
        install:
          travis:
            osx:
              environment:
                FOO: BAR
        """  # noqa: E501
    ).format(version=SCHEMA_VERSION))
    service = 'travis'

    environment = dict(os.environ)
    enable_service(service, environment, "linux")

    with push_dir(str(tmpdir)), push_env(**environment):
        execute_step("install")


def test_environment_persist(tmpdir, capfd):
    quote = "" if HAS_COMSPEC else "\""
    tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
        r"""
        schema_version: "{version}"
        before_install:
          environment:
            FOO: hello
            BAR: world
            EMPTY: ""
          commands:
            - echo {quote}1 [$<FOO>] [$<BAR>] [$<EMPTY>]{quote}
          circle:
            environment:
              BAR: under world
        install:
          environment:
            BAR: beautiful world
          commands:
            - echo {quote}2 [$<FOO>] [$<BAR>] [$<EMPTY>]{quote}
        """
    ).format(quote=quote, version=SCHEMA_VERSION))
    service = 'circle'

    with push_dir(str(tmpdir)), push_env():
        enable_service(service)
        execute_step("before_install")
        execute_step("install")
        output_lines, _ = captured_lines(capfd)

    assert output_lines[1] == "1 [hello] [under world] []"
    assert output_lines[3] == "2 [hello] [beautiful world] []"


def test_within_environment_expansion(tmpdir, capfd):
    quote = "" if HAS_COMSPEC else "\""
    tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
        r"""
        schema_version: "{version}"
        before_install:
          environment:
            FOO: hello
            BAR: $<WHAT>
            REAL_DIR: $<VERY_DIR>\\real
          commands:
            - echo {quote}[$<FOO> $<BAR> $<STRING>]{quote}
            - echo {quote}[\\the\\thing]{quote}
            - echo {quote}[$<FOO_DIR>\\the\\thing]{quote}
            - echo {quote}[$<FOO_DIR>\\the$<REAL_DIR>\\thing]{quote}
        """
    ).format(quote=quote, version=SCHEMA_VERSION))
    service = 'circle'

    environment = dict(os.environ)
    enable_service(service, environment)

    quote_type = "'" if HAS_COMSPEC else "\""
    backslashes = "\\\\\\\\" if HAS_COMSPEC else "\\"

    environment["WHAT"] = "world"
    environment["STRING"] = "of " + quote_type + "wonders" + quote_type
    environment["FOO_DIR"] = "C:\\path\\to"
    environment["VERY_DIR"] = "\\very"

    with push_dir(str(tmpdir)), push_env(**environment):
        execute_step("before_install")
        output_lines, _ = captured_lines(capfd)

    assert output_lines[1] == "[hello world of " + quote_type + "wonders" + quote_type + "]"  # noqa: E501
    assert output_lines[3] == "[\\the\\thing]".replace("\\", backslashes)
    assert output_lines[5] == "[C:\\path\\to\\the\\thing]".replace("\\", backslashes)  # noqa: E501
    assert output_lines[7] == "[C:\\path\\to\\the\\very\\real\\thing]".replace("\\", backslashes)  # noqa: E501


def test_expand_environment(tmpdir, capfd):
    quote = "" if HAS_COMSPEC else "\""
    tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
        r"""
        schema_version: "{version}"
        before_install:
          environment:
            SYMBOLS: b;$<SYMBOLS>
          circle:
            environment:
              SYMBOLS: a;$<SYMBOLS>
          commands:
            - echo {quote}before_install [$<SYMBOLS>]{quote}
        install:
          environment:
            SYMBOLS: 9;$<SYMBOLS>
          circle:
            environment:
              SYMBOLS: 8;$<SYMBOLS>
          commands:
            - echo {quote}install [$<SYMBOLS>]{quote}
        """
    ).format(quote=quote, version=SCHEMA_VERSION))
    service = 'circle'

    with push_dir(str(tmpdir)), push_env(SYMBOLS="c;d;e"):
        enable_service(service)
        execute_step("before_install")
        execute_step("install")
        output_lines, _ = captured_lines(capfd)

    assert output_lines[1] == "before_install [a;b;c;d;e]"
    assert output_lines[3] == "install [8;9;a;b;c;d;e]"


def recursively_expand_environment_vars_data():

    def case_1():
        """All variables to expand are in ``step_env``
        """
        global_env = ordereddict()

        step_env = ordereddict()
        step_env['C'] = '$<B>'
        step_env['B'] = '$<A>'
        step_env['A'] = 'Hello'

        expected_step_env = ordereddict()
        expected_step_env['C'] = 'Hello'
        expected_step_env['B'] = 'Hello'
        expected_step_env['A'] = 'Hello'

        expected_global_env_size = 3

        return step_env, global_env, expected_step_env, expected_global_env_size

    def case_2():
        """Variable to expand are spread across ``step_env`` and ``global_env``.
        """
        global_env = ordereddict()
        global_env['B'] = '$<A>'

        step_env = ordereddict()
        step_env['C'] = '$<B>'
        step_env['A'] = 'Hello'

        expected_step_env = ordereddict()
        expected_step_env['C'] = 'Hello'
        expected_step_env['A'] = 'Hello'

        expected_global_env_size = 3

        return step_env, global_env, expected_step_env, expected_global_env_size

    def case_3():
        """Variable to expand are spread across ``step_env`` and ``global_env``
        with one of ``step_env`` variable that can not be expanded.
        """
        global_env = ordereddict()
        global_env['D'] = '$<C>'
        global_env['C'] = 'Ciao'
        global_env['G'] = '$<F>'

        step_env = ordereddict()
        step_env['H'] = '$<G>'
        step_env['E'] = '$<D>'
        step_env['B'] = '$<A>'
        step_env['A'] = 'Hello'

        expected_step_env = ordereddict()
        expected_step_env['H'] = '$<F>'
        expected_step_env['E'] = 'Ciao'
        expected_step_env['B'] = 'Hello'
        expected_step_env['A'] = 'Hello'

        expected_global_env_size = 7

        return step_env, global_env, expected_step_env, expected_global_env_size

    def case_4():
        """"""

        global_env = ordereddict()
        global_env["A"] = "0"

        step_env = ordereddict()
        step_env["A"] = "1$<A>"

        expected_step_env = ordereddict()
        expected_step_env['A'] = '10'

        expected_global_env_size = 1

        return step_env, global_env, expected_step_env, expected_global_env_size

    return [
        case_1(),
        case_2(),
        case_3(),
        case_4()
    ]


@pytest.mark.parametrize(
    "step_env, global_env, expected_step_env,expected_global_env_size",
    recursively_expand_environment_vars_data()
)
def test_recursively_expand_environment_vars(
        step_env, global_env, expected_step_env, expected_global_env_size):

    step_env_size = len(step_env)

    Driver.recursively_expand_environment_vars(step_env, global_env)

    assert len(global_env) == expected_global_env_size
    assert len(step_env) == step_env_size

    assert step_env == expected_step_env


def test_ci_name_environment_variable(tmpdir, capfd):
    quote = "" if HAS_COMSPEC else "\""
    tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
        r"""
        schema_version: "{version}"
        before_install:
          environment:
            FOO: $<CI_NAME>
          commands:
            - echo {quote}ci_name [$<CI_NAME>] foo [$<FOO>]{quote}
        """
    ).format(quote=quote, version=SCHEMA_VERSION))
    service = 'circle'

    with push_dir(str(tmpdir)), push_env():
        enable_service(service)
        execute_step("before_install")
        output_lines, _ = captured_lines(capfd)

    assert output_lines[1] == "ci_name [%s] foo [%s]" % (service, service)


def test_ci_name_reserved_environment_variable(tmpdir):
    quote = "" if HAS_COMSPEC else "\""
    tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
        r"""
        schema_version: "{version}"
        before_install:
          environment:
            CI_NAME: foo
        """
    ).format(quote=quote, version=SCHEMA_VERSION))
    service = 'circle'

    environment = dict(os.environ)
    enable_service(service, environment)

    failed = False
    try:
        with push_dir(str(tmpdir)), push_env(**environment):
            execute_step("before_install")
    except ValueError:
        failed = True

    assert failed
