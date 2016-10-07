
import os
import subprocess
import sys

from utils import current_service


DEFAULT_CMAKE_VERSION = "3.6.2"


def install(cmake_version=DEFAULT_CMAKE_VERSION):

    script_dir = os.path.dirname(__file__)

    script = "%s/install_cmake.py" % current_service()

    print("[%s] Executing %s %s" %
          (os.path.basename(__file__), script, cmake_version))

    subprocess.check_call([
        sys.executable, "%s/%s" % (script_dir, script), cmake_version])

if __name__ == '__main__':
    install(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CMAKE_VERSION)
