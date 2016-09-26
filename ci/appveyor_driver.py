
from driver import Driver

import os
import os.path

from appveyor import (apply_mingw_path_fix,
                      install_cmake,
                      install_visual_studio_wrapper,
                      patch_vs2008)


class AppveyorDriver(Driver):
    def drive_install(self):
        self.log("Filesystem root:")
        self.check_call(["dir", "C:\\"])

        self.log("Installed SDKs:")
        self.check_call([
            "dir", "C:\\Program Files\\Microsoft SDKs\\Windows\\"])

        install_visual_studio_wrapper.install(
            os.path.join("ci", "appveyor", "run-with-visual-studio.cmd"))

        patch_vs2008.apply_patch()

        apply_mingw_path_fix.update_path()

        install_cmake.install()

        python_root = self.env["PYTHON"]
        py_scripts = os.path.join(python_root, "Scripts")

        self.env["PYTHONSCRIPTS"] = py_scripts
        self.env_prepend("PATH", py_scripts, python_root)

        Driver.drive_install(self)

    def drive_after_test(self):
        Driver.drive_after_test(self)

        self.check_call(["python", "setup.py", "bdist_wininst"])
        self.check_call(["python", "setup.py", "bdist_msi"])

        codecov = os.path.join(self.env["PYTHONSCRIPTS"], "codecov.exe")
        self.check_call([
            codecov, "-X", "gcov", "--required",
            "--file", ".\\tests\\coverage.xml"
        ])

        if os.path.exists("dist"):
            self.check_call(["dir", "dist"], shell=True)
