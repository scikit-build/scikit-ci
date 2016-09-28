
import json
import os
import os.path
import ruamel.yaml
import shlex
import subprocess
import sys

SCIKIT_CI_CONFIG = "scikit-ci.yml"

SERVICES = {
    "appveyor": None,
    "circle": None,
    "travis": "TRAVIS_OS_NAME"
}


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
        return subprocess.check_call(*args, **kwds)

    def env_context(self, env_file="env.json"):
        return DriverContext(self, env_file)

    @staticmethod
    def parse_config(config_file, stage_name, service_name):
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
                    operating_system = os.environ[SERVICES[service_name]]
                    system = system[operating_system]

                # if any, append service specific environment and commands
                environment.update(system.get("environment", {}))
                commands += system.get("commands", [])

        return environment, commands

    def execute_commands(self, stage_name, service_name):


        environment, commands = self.parse_config(
            SCIKIT_CI_CONFIG, stage_name, service_name)

        self.env.update(environment)

        for cmd in commands:
            self.check_call(shlex.split(cmd), env=self.env)


if __name__ == "__main__":


    stages = [
        "before_install",
        "install",
        "before_build",
        "build",
        "test",
        "after_test"
    ]

    if not os.path.exists(SCIKIT_CI_CONFIG):
        raise Exception("Couldn't find %s" % SCIKIT_CI_CONFIG)

    service_name, stage_key = sys.argv[1:3]
    if service_name not in SERVICES.keys():
        raise KeyError("invalid service: {}".format(service_name))

    if stage_key not in stages:
        raise KeyError("invalid stage: {}".format(stage_key))

    d = Driver()
    with d.env_context():
        d.execute_commands(stage_key, service_name)
