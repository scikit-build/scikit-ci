
from driver import Driver

from circle import install_cmake


class CircleDriver(Driver):
    def drive_install(self):
        self.check_call(["sudo", "apt-get", "update"])
        self.check_call(["sudo", "apt-get", "install", "gfortran"])

        install_cmake.install()

        Driver.drive_install(self)

    def drive_after_test(self):
        self.check_call([
            "codecov", "-X", "gcov", "--required",
            "--file", "./tests/coverage.xml"
        ])

        Driver.drive_after_test(self)
