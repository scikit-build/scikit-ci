
import os
import subprocess
import sys

from driver import Driver


DEFAULT_CMAKE_VERSION = "3.6.2"


def install(cmake_version=DEFAULT_CMAKE_VERSION):

    script_dir = os.path.dirname(__file__)

    subprocess.check_call([
        sys.executable,
        "%s/%s/install_cmake.py" % (script_dir, Driver.current_service()),
        cmake_version])

if __name__ == '__main__':
    install(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CMAKE_VERSION)
