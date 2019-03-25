# -*- coding: utf-8 -*-

"""This module provides an interface to parse and exectute commands found in
``scikit-ci.yml``."""

import errno
import json
import os
import os.path
import re
import ruamel.yaml
import shlex
import subprocess
import sys
import tempfile

from collections import MutableMapping
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from pyfiglet import Figlet

from . import exceptions, utils
from .constants import SCIKIT_CI_CONFIG, SERVICES, STEPS


class DriverContext(object):
    def __init__(self, driver, env_file="env.json"):
        self.driver = driver
        self.env_file = env_file

    def __enter__(self):
        self.driver.load_env(self.env_file)
        return self.driver

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None and exc_value is None and traceback is None:
            self.driver.save_env(self.driver.env, self.env_file)

        self.driver.unload_env()


class Driver(object):
    def __init__(self):
        self.env = None
        self._env_file = None

    @staticmethod
    def log(*s):
        print(" ".join(s))
        sys.stdout.flush()

    @staticmethod
    def read_env(env_file="env.json"):
        if not os.path.exists(env_file):
            return {}
        with open(env_file) as _file:
            return json.load(_file)

    def load_env(self, env_file="env.json"):
        if self.env is not None:
            self.unload_env()

        self.env = {}
        self.env.update(os.environ)
        self._env_file = env_file

        if os.path.exists(self._env_file):
            self.env.update(self.read_env(self._env_file))

        self.env = {str(k): str(v) for k, v in self.env.items()}

    @staticmethod
    def save_env(env, env_file="env.json"):
        env = {str(k): str(v) for k, v in env.items()}
        with open(env_file, "w") as _file:
            json.dump(env, _file, indent=4)

    def unload_env(self):
        self.env = None

    if "COMSPEC" in os.environ:

        class GenericCommandConfig(object):
            shell = "cmd.exe"
            subprocess_shell_mode = True
            shell_options = ["/E:ON", "/V:ON", "/c"]
            use_script = True
            script_suffix = ".cmd"
            script_pre_code = "@echo off"
            script_post_code = ""

            @staticmethod
            def escape_cmd(cmd):
                return cmd.replace("%", "%%").replace("\\\\", "\\")

            @staticmethod
            def unescape_cmd(cmd):
                return cmd.replace("%", "%%").replace("\\", "\\\\")

    else:

        class GenericCommandConfig(object):
            shell = "bash"
            subprocess_shell_mode = False
            shell_options = []
            use_script = True
            script_suffix = ".sh"
            script_pre_code = "set -e"
            script_post_code = ""

            @staticmethod
            def escape_cmd(cmd):
                return cmd

            @staticmethod
            def unescape_cmd(cmd):
                return cmd

    class PythonCommandConfig(object):
        shell = "python"
        subprocess_shell_mode = True
        shell_options = ["-B"]
        use_script = True
        script_suffix = ".py"
        script_pre_code = ""
        script_post_code = ""

        @staticmethod
        def escape_cmd(cmd):
            return cmd

        @staticmethod
        def unescape_cmd(cmd):
            return cmd

    @staticmethod
    def get_command_config(language):
        if language == "python":
            return Driver.PythonCommandConfig()
        else:
            return Driver.GenericCommandConfig()

    def check_call(self, *args, **kwds):
        kwds["env"] = kwds.get("env", self.env)
        cmd_config = kwds.pop("cmd_config")
        kwds["shell"] = cmd_config.subprocess_shell_mode
        cmd = cmd_config.escape_cmd(args[0])
        if cmd_config.use_script:
            script = cmd
            script_lines = script.splitlines()
            if len(script_lines) == 1:
                self.log("[scikit-ci] Executing: %s" % cmd_config.unescape_cmd(
                    script))
            else:
                self.log("[scikit-ci] Executing:")
                prefix = " " * len("[scikit-ci] ") + "  "
                for line in utils.indent(cmd_config.unescape_cmd(script),
                                         prefix).splitlines():
                    self.log(line)

            def _write(output_stream, txt):
                output_stream.write(bytearray("%s\n" % txt, "utf-8"))

            # Because of python issue #14243, we set "delete=False" and delete
            # manually after process execution.
            try:
                script_file = tempfile.NamedTemporaryFile(
                    delete=False, suffix=cmd_config.script_suffix)
                # Pre-code
                _write(script_file, cmd_config.script_pre_code)
                # Content provided in the yml configuration files
                _write(script_file, script)
                # Post-code
                _write(script_file, cmd_config.script_post_code)
                script_file.file.flush()

                # Then, compose the command to execute
                shell_cmd = [cmd_config.shell]
                shell_cmd.extend(cmd_config.shell_options)
                shell_cmd.append(script_file.name)
                if cmd_config.subprocess_shell_mode:
                    shell_cmd = " ".join(['"%s"' % arg for arg in shell_cmd])
                args = [shell_cmd]
                # And finally execute
                subprocess.check_call(*args, **kwds)
            finally:
                script_file.close()
                os.remove(script_file.name)
        else:
            shell_cmd = [cmd_config.shell] if cmd_config.shell else []
            shell_cmd.extend(cmd_config.shell_options)
            shell_cmd.append(cmd)
            args = [" ".join(shell_cmd)]
            self.log("[scikit-ci] Executing: %s" % args[0])
            subprocess.check_call(*args, **kwds)

    def env_context(self, env_file="env.json"):
        return DriverContext(self, env_file)

    @staticmethod
    def expand_environment_vars(text, environment, to_empty_string=False):
        """Return an updated ``text`` string where all occurrences of
        ``$<EnvironmentVarName>`` found in ``environment`` are replaced.

        By default, occurrences of ``$<EnvironmentVarName>`` that are NOT
        associated with any environment variable are not replaced. Setting
        ``to_empty_string`` to True will change them to empty string.

        """
        for name, value in environment.items():
            text = text.replace(
                "$<%s>" % name,
                value.replace("\\", "\\\\").replace("\"", "\\\""))
        if to_empty_string:
            text = re.sub(Driver.ENV_VAR_REGEX, "", text)
        return text

    ENV_VAR_REGEX = re.compile(r"\$<[\w\d][\w\d_]*>", re.IGNORECASE)
    """Regular expression matching legal environment variable of the
    form ``$<EnvironmentVarName>``"""

    @staticmethod
    def recursively_expand_environment_vars(step_env, global_env=None):
        """This function will recursively expand all occurrences of
        ``$<EnvironmentVarName>`` found in ``step_env`` and ``global_env``
        values.
        """

        if global_env is None:
            global_env = step_env

        # Keep track of variables that still need to be expanded
        to_be_expanded = set()

        def _expand(names, _work_env, _global_env=None):
            if _global_env is None:
                _global_env = _work_env
            for env_var_name in names:
                # Get the value
                env_var_value = _work_env[env_var_name]

                # Attempt to expand the value
                _work_env[env_var_name] = Driver.expand_environment_vars(
                    env_var_value, _global_env)

                # Keep track of variable names to expand
                if re.match(Driver.ENV_VAR_REGEX, _work_env[env_var_name]):
                    to_be_expanded.add(env_var_name)
                elif env_var_name in to_be_expanded:
                    to_be_expanded.remove(env_var_name)

        # Expand step env values referencing global env variables
        _expand(step_env.keys(), step_env, global_env)
        global_env.update(step_env)

        # Expand variables
        _expand(step_env.keys(), global_env)

        # Expand remaining variables if any
        to_be_expanded_count = len(to_be_expanded)
        while to_be_expanded:
            _expand(to_be_expanded, global_env)
            if to_be_expanded_count == len(to_be_expanded):
                break
            to_be_expanded_count = len(to_be_expanded)

        # Update step environment
        for name in step_env:
            step_env[name] = global_env[name]

    @staticmethod
    def expand_command(command, environments, posix_shell=True):
        """Return an updated ``command`` string where all occurrences of
        ``$<EnvironmentVarName>`` (with a corresponding env variable set) have
        been replaced.

        If ``posix_shell`` is True, only occurrences of
        ``$<EnvironmentVarName>`` in string starting with double quotes will
        be replaced.

        See
        https://www.gnu.org/software/bash/manual/html_node/Double-Quotes.html
        and
        https://www.gnu.org/software/bash/manual/html_node/Single-Quotes.html
        """
        if not posix_shell:
            return Driver.expand_environment_vars(
                    command, environments, to_empty_string=True)

        # Strip line continuation characters. There are not required to
        # successfully evaluate the expression and are confusing shlex.
        command = command.replace("\\\n", "")

        def _indent_size(txt):
            count = 0
            for char in txt:
                if char != ' ':
                    break
                count += 1
            return count

        expanded_lines = []

        # Proceed to the expansion line by line
        for line in command.splitlines():
            if line.startswith("#") or line == "":
                expanded_lines.append(line)
                continue
            indent = _indent_size(line)
            tokenizer = shlex.shlex(line, posix=False)
            tokenizer.whitespace_split = True
            expanded_tokens = []
            for token in tokenizer:
                expand = not (token[0] == "'" and token[-1] == "'")
                if expand:
                    token = Driver.expand_environment_vars(
                        token, environments, to_empty_string=True)
                expanded_tokens.append(token)

            expanded_lines.append(indent * " " + " ".join(expanded_tokens))

        return "\n".join(expanded_lines)

    @staticmethod
    def _raise_if_setting_ci_name(environment):
        # Check if reserved variable are used
        if "CI_NAME" in environment:
            raise ValueError("CI_NAME environment variable can not be set. "
                             "It is reserved to store the name of the current "
                             "CI service (e.g appveyor, azure, circle or travis.")

    @staticmethod
    def parse_config(config_file, stage_name, service_name, global_env):
        with open(config_file) as input_stream:
            data = ruamel.yaml.load(input_stream, ruamel.yaml.RoundTripLoader)

        commands = []
        environment = {}

        if stage_name in data:
            stage = data[stage_name]

            # common to all services
            environment = stage.get("environment", {})
            commands = stage.get("commands", [])

            # Sanity checks
            Driver._raise_if_setting_ci_name(environment)

            # Expand all occurrences of ``$<EnvironmentVarName>``.
            Driver.recursively_expand_environment_vars(environment, global_env)

            if service_name in stage:
                system = stage[service_name]

                # consider service offering multiple operating system support
                if SERVICES[service_name]:
                    operating_system = global_env[SERVICES[service_name]]
                    system = system.get(operating_system, {})

                # if any, get service specific environment
                system_environment = system.get("environment", {})

                # Sanity checks
                Driver._raise_if_setting_ci_name(environment)

                # Expand system environment values
                Driver.recursively_expand_environment_vars(
                    system_environment, global_env)

                # Merge system environment variable back into environment
                environment.update(system_environment)

                # ... and append commands
                commands += system.get("commands", [])

        return environment, commands

    def execute_commands(self, stage_name):

        print(Figlet().renderText(stage_name.upper()))

        service_name = utils.current_service()

        self.env["CI_NAME"] = service_name

        environment, commands = self.parse_config(
            SCIKIT_CI_CONFIG, stage_name, service_name, self.env)

        # Unescape environment variables
        for name in environment:
            value = self.env[name]
            for old, new in [("\\\\", "\\")]:
                value = value.replace(old, new)
            self.env[name] = value

        for cmd in commands:
            language = "default"
            if isinstance(cmd, MutableMapping):
                # Prevent output of debug message.
                # Workaround https://bitbucket.org/ruamel/yaml/pull-requests/13
                try:
                    oldout = sys.stdout
                    sys.stdout = StringIO()
                    language = list(cmd.keys())[0]
                    cmd = list(cmd.values())[0]
                finally:
                    sys.stdout = oldout

            else:
                # Expand environment variables used within commands
                posix_shell = "COMSPEC" not in os.environ
                cmd = self.expand_command(
                    cmd, self.env, posix_shell=posix_shell).strip()
            try:
                self.check_call(
                    cmd, cmd_config=self.get_command_config(language),
                    env=self.env
                )
            except subprocess.CalledProcessError as exc:
                raise exceptions.SKCIStepExecutionError(
                    stage_name, exc.returncode, cmd, exc.output
                )


def dependent_steps(step):
    if step not in STEPS:  # pragma: no cover
        raise KeyError("invalid step: {}".format(step))
    step_index = STEPS.index(step)
    if step_index == 0:
        return []
    return STEPS[0:step_index]


def execute_step(
        step, force=False, with_dependencies=True, clear_cached_env=False):

    if not os.path.exists(SCIKIT_CI_CONFIG):  # pragma: no cover
        raise OSError(errno.ENOENT, "Couldn't find %s" % SCIKIT_CI_CONFIG)

    if step not in STEPS:  # pragma: no cover
        raise KeyError("invalid step: {}".format(step))

    if clear_cached_env and os.path.exists('env.json'):
        os.remove('env.json')

    depends = dependent_steps(step)

    # If forcing execution, remove SCIKIT_CI_<step> env. variables
    if force:
        env = Driver.read_env()
        steps = [step]
        if with_dependencies:
            steps += depends
        for _step in steps:
            if 'SCIKIT_CI_%s' % _step.upper() in env:
                del env['SCIKIT_CI_%s' % _step.upper()]
        Driver.save_env(env)

    # Skip step if it has already been executed
    if 'SCIKIT_CI_%s' % step.upper() in Driver.read_env():
        return

    # Recursively execute dependent steps
    if with_dependencies and depends:
        execute_step(depends[-1], with_dependencies=with_dependencies)

    d = Driver()
    with d.env_context():
        d.execute_commands(step)
        d.env['SCIKIT_CI_%s' % step.upper()] = '1'
