
import os
import platform
import pyfiglet
import pytest
import subprocess
import sys
import textwrap

from ruamel.yaml.compat import ordereddict

from . import captured_lines, display_captured_text, push_dir, push_env
from ci.constants import SERVICES, SERVICES_ENV_VAR, STEPS
from ci.driver import Driver, dependent_steps, execute_step
from ci.exceptions import SKCIStepExecutionError
from ci.utils import current_service, current_operating_system

"""Indicate if the system has a Windows command line interpreter"""
HAS_COMSPEC = "COMSPEC" in os.environ

"""Version of the tested scikit-ci schema."""
SCHEMA_VERSION = "0.5.0"


def disable_services(environment=os.environ):
    """Clear environment variables associated will all know services
    """
    for any_service in SERVICES:
        # Clear service variable (e.g APPVEYOR)
        if SERVICES_ENV_VAR[any_service] in environment:
            del environment[SERVICES_ENV_VAR[any_service]]
        # Clear variable associated operating system (e.g TRAVIS_OS_NAME)
        if SERVICES[any_service]:
            if SERVICES[any_service] in environment:
                del environment[SERVICES[any_service]]


def enable_service(service, environment=os.environ, operating_system=None):
    """Ensure ``service`` is enabled.

    For multi-os services, you are expected to set ``operating_system``.

    Note that before enabling ``service``, the environment variables (including
    the one specifying which OS is enabled) for all services are first removed
    from the ``environment``.
    """
    disable_services(environment)
    environment[SERVICES_ENV_VAR[service]] = "true"
    if SERVICES[service]:
        assert operating_system is not None
        environment[SERVICES[service]] = operating_system


@pytest.mark.parametrize("service, exception", [
    ('appveyor', None),
    ('azure', None),
    ('circle', None),
    ('travis', None),
    ('invalid', LookupError)
])
def test_current_service(service, exception):
    with push_env():
        if exception is None:
            operating_system = "linux" if SERVICES[service] else None
            enable_service(service, operating_system=operating_system)
            assert current_service() == service
            assert current_operating_system(service) == operating_system
        else:
            disable_services()
            with pytest.raises(exception):
                current_service()


def scikit_steps(tmpdir, service):
    """Given ``tmpdir`` and ``service``, this generator yields
    ``(step, system, environment)`` for all supported steps.
    """

    # Remove environment variables of the form 'SCIKIT_CI_<STEP>`
    for step in STEPS:
        if 'SCIKIT_CI_%s' % step.upper() in os.environ:
            del os.environ['SCIKIT_CI_%s' % step.upper()]

    # By default, a service is associated with only one "implicit" operating
    # system.
    # Service supporting multiple operating system (e.g travis) should be
    # specified below.
    osenv_per_service = {
        "azure": {"Darwin": "AGENT_OS", "Linux": "AGENT_OS", "Windows_NT": "AGENT_OS"},
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

        for step in STEPS:

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

          azure:
            Darwin:
              environment:
                SERVICE: azure-Darwin
              commands:
                - $<PYTHON> -c "import os; print('%s / %s / %s' % (os.environ['WHAT'], os.environ['SERVICE'], os.environ['AGENT_OS']))"
            Linux:
              environment:
                SERVICE: azure-Linux
              commands:
                - $<PYTHON> -c "import os; print('%s / %s / %s' % (os.environ['WHAT'], os.environ['SERVICE'], os.environ['AGENT_OS']))"
            Windows_NT:
              environment:
                SERVICE: azure-Windows_NT
              commands:
                - $<PYTHON> -c "import os; print('%s / %s / %s' % (os.environ['WHAT'], os.environ['SERVICE'], os.environ['AGENT_OS']))"

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
                    command_1=commands[1]) for step in STEPS
                 ]
            )
    )


def strip_ascii_art(tuple_of_lines):
    """Return lines without the ascii-art representing the step name.
    """
    if not isinstance(tuple_of_lines, tuple):
        tuple_of_lines = (tuple_of_lines,)

    offset = pyfiglet.FigletFont().height
    return tuple([lines[offset + 1:] for lines in tuple_of_lines])


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
                output_lines, error_lines = strip_ascii_art(
                    captured_lines(capfd))

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


def test_dependent_steps():
    step = "before_install"
    expected = []
    assert dependent_steps(step) == expected

    step = "build"
    expected = ['before_install', 'install', 'before_build']
    assert dependent_steps(step) == expected


def test_shell_for_loop(tmpdir, capfd):

    if platform.system().lower() == "windows":
        # Since executing windows terminal command is not supported
        # on appveyor, we do not test for it.
        # That said, here is an example of should be expected to work:
        #   FOR %G IN (foo bar) DO python -c "print('var %G')"
        tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
            r"""
            schema_version: "{version}"
            install:
              commands:
                - |
                  echo var foo
                  echo var bar
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
            output_lines, _ = strip_ascii_art(captured_lines(capfd))

        if step == 'install':
            if platform.system().lower() == "windows":
                assert output_lines[3] == "var foo"
                assert output_lines[4] == "var bar"
            else:
                assert output_lines[1] == "var foo"
                assert output_lines[2] == "var bar"
                assert output_lines[4] == "var: oof"
                assert output_lines[5] == "var: rab"
        else:
            assert len(output_lines) == 0


def test_shell_command_with_quoted_args(tmpdir, capfd):

    program = tmpdir.join("program.py")
    program.write(textwrap.dedent(
        """
        import sys
        for index, arg in enumerate(sys.argv):
            if index == 0:
                continue
            print("arg_%s [%s]" % (index, sys.argv[index]))
        """
    ))

    tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
        r"""
        schema_version: "{version}"
        install:
          commands:
            - echo Hello1
            - echo "Hello2"
            - echo 'Hello3'
            - python -c "print('Hello4')"
            - python -c 'print("Hello5")'
            - python -c "print('Hello6\'World')"
            - python program.py --things "foo" "bar" --more-things "doo" 'dar'
            - python program.py --the-foo="foo" -the-bar='bar'

        """  # noqa: E501
    ).format(version=SCHEMA_VERSION))
    service = 'appveyor' if platform.system().lower() == "windows" else "circle"

    for step, system, environment in scikit_steps(tmpdir, service):

        with push_dir(str(tmpdir)), push_env(**environment):
            execute_step(step)
            output_lines, _ = strip_ascii_art(captured_lines(capfd))

        if step == 'install':

            # Command 1
            offset = 0
            output_line_count = 1
            assert output_lines[1 + offset] == "Hello1"

            # Command 2
            offset = offset + 1 + output_line_count
            output_line_count = 1
            if HAS_COMSPEC:
                assert output_lines[1 + offset] == "\"Hello2\""
            else:
                assert output_lines[1 + offset] == "Hello2"

            # Command 3
            offset = offset + 1 + output_line_count
            output_line_count = 1
            if HAS_COMSPEC:
                assert output_lines[1 + offset] == "'Hello3'"
            else:
                assert output_lines[1 + offset] == "Hello3"

            # Command 4
            offset = offset + 1 + output_line_count
            output_line_count = 1
            assert output_lines[1 + offset] == "Hello4"

            # Command 5
            offset = offset + 1 + output_line_count
            if HAS_COMSPEC:
                output_line_count = 0
            else:
                output_line_count = 1
                assert output_lines[1 + offset] == "Hello5"

            # Command 6
            offset = offset + 1 + output_line_count
            output_line_count = 1
            assert output_lines[1 + offset] == "Hello6'World"

            # Command 7
            offset = offset + 1 + output_line_count
            output_line_count = 6
            assert output_lines[1 + offset] == "arg_1 [--things]"
            assert output_lines[2 + offset] == "arg_2 [foo]"
            assert output_lines[3 + offset] == "arg_3 [bar]"
            assert output_lines[4 + offset] == "arg_4 [--more-things]"
            assert output_lines[5 + offset] == "arg_5 [doo]"
            if HAS_COMSPEC:
                assert output_lines[6 + offset] == "arg_6 ['dar']"
            else:
                assert output_lines[6 + offset] == "arg_6 [dar]"

            # Command 8
            offset = offset + 1 + output_line_count
            # output_line_count = 2
            assert output_lines[1 + offset] == "arg_1 [--the-foo=foo]"
            if HAS_COMSPEC:
                assert output_lines[2 + offset] == "arg_2 [-the-bar='bar']"
            else:
                assert output_lines[2 + offset] == "arg_2 [-the-bar=bar]"
        else:
            assert len(output_lines) == 0


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
                  for %%G in (foo bar) do ^
                  python -c "print('var %%G')"

                  if "bar" == "bar" echo "bar is bar"
            """
        ).format(version=SCHEMA_VERSION))
        service = 'appveyor'
        offset = 4

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

                  if [[ "bar" == "bar" ]]; then
                    echo "bar is bar"
                  fi

                  # This is a comment
                  # .. and an other one
                  for letter in $(echo a) \
                        $(echo b); do
                      echo the letter $letter -in "/text/"
                  done
            """
        ).format(version=SCHEMA_VERSION))
        service = 'circle'
        # Number of lines in the command  (without line continuation)
        offset = 13

    for step, system, environment in scikit_steps(tmpdir, service):

        with push_dir(str(tmpdir)), push_env(**environment):
            execute_step(step)
            output_lines, _ = strip_ascii_art(captured_lines(capfd))

        if step == 'install':
            assert output_lines[offset + 1] == "var foo"
            assert output_lines[offset + 2] == "var bar"
            assert output_lines[offset + 3] == "bar is bar"
            assert output_lines[offset + 4] == "the letter a -in /text/"
            assert output_lines[offset + 5] == "the letter b -in /text/"
        else:
            assert len(output_lines) == 0


def _expand_command_test(command, posix_shell, expected):
    environments = {
        "OTHER": "unused",
        "FO": "foo"
    }
    assert (
        Driver.expand_command(command, environments, posix_shell)
        == expected)


@pytest.mark.parametrize("command, posix_shell, expected", [
    (r"""echo "$<FO>", "$<B>", $<FO>""", False, 'echo "foo", "", foo'),
    (r"""echo '$<FO>', '$<B>', $<FO>""", False, "echo 'foo', '', foo"),
    (r"""echo "$<FO>", "$<B>", $<FO>""", True, 'echo "foo" , "" , foo'),
    (r"""echo '$<FO>', '$<B>', $<FO>""", True, "echo '$<FO>' , '$<B>' , foo"),
])
def test_expand_command(command, posix_shell, expected):
    _expand_command_test(command, posix_shell, expected)


@pytest.mark.parametrize("command, posix_shell, expected", [
    (r"""echo "$<FO>", \
"$<B>", $<FO>""", True, 'echo "foo" , "" , foo'),
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


def test_cli_force_and_without_deps(tmpdir):
    tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
        r"""
        schema_version: "{version}"
        before_install:
          commands:
            - "python -c \"with open('before_install-done', 'w') as file: file.write('')\""
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

    #
    # Execute without --force
    #
    subprocess.check_call(
        "python -m ci install",
        shell=True,
        env=environment,
        stderr=subprocess.STDOUT,
        cwd=str(tmpdir)
    )

    # Check that steps were executed
    assert tmpdir.join("before_install-done").exists()
    assert tmpdir.join("install-done").exists()

    tmpdir.join("before_install-done").remove()
    tmpdir.join("install-done").remove()

    #
    # Execute without --force
    #
    subprocess.check_call(
        "python -m ci install",
        shell=True,
        env=environment,
        stderr=subprocess.STDOUT,
        cwd=str(tmpdir)
    )

    # Check that steps were NOT re-executed
    assert not tmpdir.join("before_install-done").exists()
    assert not tmpdir.join("install-done").exists()

    #
    # Execute with --force
    #
    subprocess.check_call(
        "python -m ci install --force",
        shell=True,
        env=environment,
        stderr=subprocess.STDOUT,
        cwd=str(tmpdir)
    )

    # Check that steps were re-executed
    assert tmpdir.join("before_install-done").exists()
    assert tmpdir.join("install-done").exists()

    tmpdir.join("before_install-done").remove()
    tmpdir.join("install-done").remove()

    #
    # Execute with --force and --without-deps
    #
    subprocess.check_call(
        "python -m ci install --force --without-deps",
        shell=True,
        env=environment,
        stderr=subprocess.STDOUT,
        cwd=str(tmpdir)
    )

    # Check that only specified step was re-executed
    assert not tmpdir.join("before_install-done").exists()
    assert tmpdir.join("install-done").exists()

    tmpdir.join("install-done").remove()
    tmpdir.join("env.json").remove()

    #
    # Execute with --without-deps
    #
    subprocess.check_call(
        "python -m ci install --without-deps",
        shell=True,
        env=environment,
        stderr=subprocess.STDOUT,
        cwd=str(tmpdir)
    )

    # Check that only specified step was executed
    assert not tmpdir.join("before_install-done").exists()
    assert tmpdir.join("install-done").exists()


def test_cli_execute_all_steps(tmpdir):
    tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
        r"""
        schema_version: "{version}"
        before_install:
          commands:
            - "python -c \"with open('before_install-done', 'w') as file: file.write('')\""
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
        "python -m ci",
        shell=True,
        env=environment,
        stderr=subprocess.STDOUT,
        cwd=str(tmpdir)
    )

    assert tmpdir.join("before_install-done").exists()
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

    output_lines = []

    with push_dir(str(tmpdir)), push_env():
        enable_service(service)

        execute_step("before_install")
        output_lines.extend(strip_ascii_art(captured_lines(capfd))[0])

        execute_step("install")
        output_lines.extend(strip_ascii_art(captured_lines(capfd))[0])

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

    # quote_type = "'" if HAS_COMSPEC else "\""
    # backslashes = "\\\\\\\\" if HAS_COMSPEC else "\\"

    quote_type = "'"  # if HAS_COMSPEC else "\""
    backslashes = "\\"

    environment["WHAT"] = "world"
    environment["STRING"] = "of " + quote_type + "wonders" + quote_type
    environment["FOO_DIR"] = "C:\\path\\to"
    environment["VERY_DIR"] = "\\very"

    with push_dir(str(tmpdir)), push_env(**environment):
        execute_step("before_install")
        output_lines, _ = strip_ascii_art(captured_lines(capfd))

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

    output_lines = []

    with push_dir(str(tmpdir)), push_env(SYMBOLS="c;d;e"):
        enable_service(service)

        execute_step("before_install")
        output_lines.extend(strip_ascii_art(captured_lines(capfd))[0])

        execute_step("install")
        output_lines.extend(strip_ascii_art(captured_lines(capfd))[0])

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
        output_lines, _ = strip_ascii_art(captured_lines(capfd))

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


def test_step_ordering_and_dependency(tmpdir):
    tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
        r"""
        schema_version: "{version}"
        before_install:
          commands:
            - "python -c \"with open('before_install', 'w') as file: file.write('')\""
        install:
          commands:
            - "python -c \"with open('install', 'w') as file: file.write('')\""
        before_build:
          commands:
            - "python -c \"with open('before_build', 'w') as file: file.write('')\""
        build:
          commands:
            - "python -c \"with open('build', 'w') as file: file.write('')\""
        test:
          commands:
            - "python -c \"exit(1)\""
        after_test:
          commands:
            - "python -c \"with open('after_test', 'w') as file: file.write('')\""
        """  # noqa: E501
    ).format(version=SCHEMA_VERSION))
    service = 'circle'

    environment = dict(os.environ)
    enable_service(service, environment)

    with push_dir(str(tmpdir)), push_env(**environment):

        execute_step("install")

        #
        # Check that steps `before_install` and `install` were executed
        #
        env = Driver.read_env()
        assert env['SCIKIT_CI_BEFORE_INSTALL'] == '1'
        assert env['SCIKIT_CI_INSTALL'] == '1'
        assert tmpdir.join('before_install').exists()
        assert tmpdir.join('install').exists()

        # Remove files - This is to make sure the steps are not re-executed
        tmpdir.join('before_install').remove()
        tmpdir.join('install').remove()

        # Check files have been removed
        assert not tmpdir.join('before_install').exists()
        assert not tmpdir.join('install').exists()

        execute_step("build")

        #
        # Check that only `before_build` and `build` steps were executed
        #
        env = Driver.read_env()
        assert env['SCIKIT_CI_BEFORE_INSTALL'] == '1'
        assert env['SCIKIT_CI_INSTALL'] == '1'
        assert env['SCIKIT_CI_BEFORE_BUILD'] == '1'
        assert env['SCIKIT_CI_BUILD'] == '1'

        assert not tmpdir.join('before_install').exists()
        assert not tmpdir.join('install').exists()
        assert tmpdir.join('before_build').exists()
        assert tmpdir.join('build').exists()

        # Remove files - This will to make sure the steps are not re-executed
        tmpdir.join('before_build').remove()
        tmpdir.join('build').remove()

        failed = False
        try:
            execute_step("after_test")
        except SKCIStepExecutionError as exc:
            failed = "exit(1)" in exc.cmd

        #
        # Check that `after_test` step was NOT executed. It should not be
        # execute because `test` step is failing.
        #
        assert failed
        env = Driver.read_env()
        assert env['SCIKIT_CI_BEFORE_INSTALL'] == '1'
        assert env['SCIKIT_CI_INSTALL'] == '1'
        assert env['SCIKIT_CI_BEFORE_BUILD'] == '1'
        assert env['SCIKIT_CI_BUILD'] == '1'
        assert 'SCIKIT_CI_TEST' not in env
        assert 'SCIKIT_CI_AFTER_TEST' not in env

        assert not tmpdir.join('before_install').exists()
        assert not tmpdir.join('install').exists()
        assert not tmpdir.join('before_install').exists()
        assert not tmpdir.join('install').exists()
        assert not tmpdir.join('test').exists()
        assert not tmpdir.join('after_test').exists()

        #
        # Check `force=True` works as expected
        #
        execute_step("install", force=True)

        # Check that steps `before_install` and `install` were re-executed
        env = Driver.read_env()
        assert env['SCIKIT_CI_BEFORE_INSTALL'] == '1'
        assert env['SCIKIT_CI_INSTALL'] == '1'
        assert tmpdir.join('before_install').exists()
        assert tmpdir.join('install').exists()

        tmpdir.join('before_install').remove()
        tmpdir.join('install').remove()

        #
        # Check `force=True` and `with_dependencies=True` work as expected
        #
        execute_step("install", force=True, with_dependencies=False)

        # Check that only step `install` was re-executed
        env = Driver.read_env()
        assert env['SCIKIT_CI_BEFORE_INSTALL'] == '1'
        assert env['SCIKIT_CI_INSTALL'] == '1'
        assert not tmpdir.join('before_install').exists()
        assert tmpdir.join('install').exists()

        tmpdir.join('install').remove()

        #
        # Check `force=False` and `with_dependencies=True` work as expected
        #
        tmpdir.join('env.json').remove()
        execute_step("install", with_dependencies=False)

        # Check that only step `install` was executed
        env = Driver.read_env()
        assert 'SCIKIT_CI_BEFORE_INSTALL' not in env
        assert env['SCIKIT_CI_INSTALL'] == '1'
        assert not tmpdir.join('before_install').exists()
        assert tmpdir.join('install').exists()


def test_clear_env(tmpdir):
    """This test checks that the 'env.json' file is removed when the force
    option is specified.
    """

    tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
        r"""
        schema_version: "{version}"
        """
    ).format(version=SCHEMA_VERSION))

    service = 'circle'

    environment = dict(os.environ)
    enable_service(service, environment)

    with push_dir(str(tmpdir)), push_env(**environment):

        execute_step("test")

        env = Driver.read_env()
        assert env['SCIKIT_CI_TEST'] == '1'

        # Add variable to check env file is effectively removed
        assert 'CLEAR_ENV_TEST' not in env
        env['CLEAR_ENV_TEST'] = '1'
        Driver.save_env(env)
        assert 'CLEAR_ENV_TEST' in Driver.read_env()

        #
        # Re-execute 'test' step clearing environment
        #
        execute_step("test", clear_cached_env=True)

        env = Driver.read_env()
        assert env['SCIKIT_CI_TEST'] == '1'
        assert 'CLEAR_ENV_TEST' not in env


def test_python_cmd(tmpdir, capfd):
    tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
        r"""
        schema_version: "{version}"
        test:
          commands:
            - python: print("single_line")
            - python: "for letter in ['a', 'b', 'c']: print(letter)"
            # This is a comment
            - python: |
                      for index in range(3):
                          with open("file_%s" % index, "w") as output:
                              output.write("")
        """
    ).format(version=SCHEMA_VERSION))

    service = 'circle'

    environment = dict(os.environ)
    enable_service(service, environment)

    with push_dir(str(tmpdir)), push_env(**environment):
        execute_step("test", with_dependencies=False)
        output_lines, _ = strip_ascii_art(captured_lines(capfd))

    assert output_lines[1] == "single_line"
    assert output_lines[3] == "a"
    assert output_lines[4] == "b"
    assert output_lines[5] == "c"
    assert tmpdir.join("file_0").exists()
    assert tmpdir.join("file_1").exists()
    assert tmpdir.join("file_2").exists()


def test_issue39_propagate_command_script_error(tmpdir):
    tmpdir.join('scikit-ci.yml').write(textwrap.dedent(
        r"""
        schema_version: "{version}"
        test:
          commands:
            # The following command is expected to fail
            - |
              $(import foo; print(foo()))
              $(import bar; print(bar()))
        """
    ).format(version=SCHEMA_VERSION))

    service = 'circle'

    environment = dict(os.environ)
    enable_service(service, environment)

    with push_dir(str(tmpdir)), push_env(**environment):
        with pytest.raises(
                SKCIStepExecutionError,
                message=".*Return code: 2.+Command:.+$(import foo; print(foo())).*"):
            execute_step("test", with_dependencies=False)
