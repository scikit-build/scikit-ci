# -*- coding: utf-8 -*-

"""This module provides an interface to parse and exectute commands found in
``scikit-ci.yml``."""

import errno
import json
import os
import os.path
import ruamel.yaml
import shlex
import subprocess
import sys

from . import utils
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
            self.driver.save_env()

        self.driver.unload_env()


class Driver(object):
    def __init__(self):
        self.env = None
        self._env_file = None

    @staticmethod
    def log(*s):
        print(" ".join(s))
        sys.stdout.flush()

    def load_env(self, env_file="env.json"):
        if self.env is not None:
            self.unload_env()

        self.env = {}
        self.env.update(os.environ)
        self._env_file = env_file

        if os.path.exists(self._env_file):
            self.env.update(json.load(open(self._env_file)))

        self.env = {str(k): str(v) for k, v in self.env.items()}

    def save_env(self, env_file=None):
        if env_file is None:
            env_file = self._env_file

        with open(env_file, "w") as env:
            json.dump(self.env, env, indent=4)

    def unload_env(self):
        self.env = None

    def check_call(self, *args, **kwds):
        kwds["env"] = kwds.get("env", self.env)
        kwds["shell"] = True

        if "COMSPEC" in os.environ:
            cmd = "cmd.exe /E:ON /V:ON /C \"%s\"" % args[0]
            args = [cmd]

        self.log("[scikit-ci] Executing: %s" % args[0])
        return subprocess.check_call(*args, **kwds)

    def env_context(self, env_file="env.json"):
        return DriverContext(self, env_file)

    @staticmethod
    def expand_environment_vars(text, environments):
        """Return an updated ``command`` string where all occurrences of
        ``$<EnvironmentVarName>`` (with a corresponding env variable set) have
        been replaced.
        """

        for name, value in environments.items():
            text = text.replace(
                "$<%s>" % name,
                value.replace("\\", "\\\\").replace("\"", "\\\""))

        return text

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
        # Strip line continuation characters. There are not required
        # successfully evaluate the expression and were confusion shlex.
        if posix_shell:
            command = command.replace("\\\n", "")

        tokenizer = shlex.shlex(command, posix=False)
        tokenizer.whitespace_split = True
        expanded_lines = []
        expanded_tokens = []
        lineno = 1
        for token in tokenizer:
            expand = not (posix_shell and token[0] == "'" and token[-1] == "'")
            if expand:
                token = Driver.expand_environment_vars(token, environments)

            if tokenizer.lineno > lineno:
                expanded_lines.append(" ".join(expanded_tokens))
                expanded_tokens = []

            expanded_tokens.append(token)
            lineno = tokenizer.lineno

        if expanded_tokens:
            expanded_lines.append(" ".join(expanded_tokens))

        return "\n".join(expanded_lines)

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

            if service_name in stage:
                system = stage[service_name]

                # consider service offering multiple operating system support
                if SERVICES[service_name]:
                    operating_system = global_env[SERVICES[service_name]]
                    system = system.get(operating_system, {})

                # if any, set service specific environment
                system_environment = system.get("environment", {})
                for name, value in system_environment.items():
                    environment[name] = Driver.expand_environment_vars(
                        value, environment)
                # ... and append commands
                commands += system.get("commands", [])

        return environment, commands

    def execute_commands(self, stage_name):

        service_name = utils.current_service()

        environment, commands = self.parse_config(
            SCIKIT_CI_CONFIG, stage_name, service_name, self.env)

        # Check if reserved variable are used
        if "CI_NAME" in environment:
            raise ValueError("CI_NAME environment variable can not be set. "
                             "It is reserved to store the name of the current "
                             "CI service (e.g appveyor, circle or travis.")

        environment["CI_NAME"] = service_name

        # Expand stage environment variables
        for name, value in environment.items():
            environment[name] = self.expand_environment_vars(value, self.env)

        # Merge stage environment variables with global environment
        self.env.update(environment)

        # Unescape environment variables
        for name in environment:
            value = self.env[name]
            for old, new in [("\\\\", "\\")]:
                value = value.replace(old, new)
            self.env[name] = value

        posix_shell = "COMSPEC" not in os.environ

        for cmd in commands:
            # Expand environment variables used within commands
            cmd = self.expand_command(
                cmd, self.env, posix_shell=posix_shell)
            self.check_call(cmd.replace("\\\\", "\\\\\\\\"), env=self.env)


def execute_step(step):

    if not os.path.exists(SCIKIT_CI_CONFIG):  # pragma: no cover
        raise OSError(errno.ENOENT, "Couldn't find %s" % SCIKIT_CI_CONFIG)

    if step not in STEPS:  # pragma: no cover
        raise KeyError("invalid stage: {}".format(step))

    d = Driver()
    with d.env_context():
        d.execute_commands(step)
