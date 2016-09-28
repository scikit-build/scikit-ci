
from driver import PythonWheelDriver

from travis import (install_cmake, install_pyenv)


class TravisDriver(PythonWheelDriver):

    def load_env(self, *args, **kwargs):
        PythonWheelDriver.load_env(self, *args, **kwargs)
        self.is_darwin = (self.env.get("TRAVIS_OS_NAME") == "osx")
        self.py_version = self.env.get("PYTHONVERSION")
        self.extra_test_args = self.env.get("EXTRA_TEST_ARGS", "")

    def drive_install(self):

        install_cmake.install(self.is_darwin, "3.5")
        if self.is_darwin:
            install_pyenv.install(self.py_version)

            self.check_call(
                "\n".join((
                    "eval \"$( pyenv init - )\"",
                    (
                        "pip install "
                        "--user --disable-pip-version-check --user --upgrade "
                        "pip"
                    ),
                    "pip install --user -r requirements.txt",
                    "pip install --user -r requirements-dev.txt"
                )),
                shell=True
            )

        if not self.is_darwin:
            PythonWheelDriver.drive_install(self)

    def drive_pre_build(self):
        if self.is_darwin:
            self.check_call(
                "\n".join((
                    "eval \"$( pyenv init - )\"",
                    "python -m flake8 -v"
                )),
                shell=True
            )
        else:
            PythonWheelDriver.drive_pre_build(self)

    def drive_build(self):
        if self.is_darwin:
            self.check_call(
                "\n".join((
                    "eval \"$( pyenv init - )\"",
                    "python setup.py build"
                )),
                shell=True
            )
        else:
            PythonWheelDriver.drive_build(self)

    def drive_test(self):
        if self.is_darwin:
            extra_test_args = self.env.get("EXTRA_TEST_ARGS", "")
            addopts = ""
            if extra_test_args:
                addopts = " --addopts " + extra_test_args

            self.check_call(
                "\n".join((
                    "eval \"$( pyenv init - )\"",
                    "python setup.py test" + addopts
                )),
                shell=True
            )
        else:
            PythonWheelDriver.drive_test(self)

    def drive_after_test(self):
        if self.is_darwin:
            self.check_call(
                "\n".join((
                    "eval \"$( pyenv init - )\"",
                    "codecov -X gcov --required --file ./tests/coverage.xml",
                    "python setup.py bdist_wheel"
                )),
                shell=True
            )
        else:
            self.check_call([
                "codecov", "-X", "gcov", "--required",
                "--file", "./tests/coverage.xml"
            ])
            PythonWheelDriver.drive_after_test(self)
