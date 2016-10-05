
"""
Usage::

    import install_cmake
    install_cmake.install()

"""

import os
import shutil
import sys
import zipfile

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

DEFAULT_CMAKE_VERSION = "3.5.2"


def _log(*args):
    print(" ".join(args))
    sys.stdout.flush()


def _env_prepend(key, *values):
    os.environ[key] = os.pathsep.join(
        list(values) + os.environ.get(key, "").split(os.pathsep))


def install(cmake_version=DEFAULT_CMAKE_VERSION):
    """Download and install CMake into ``C:\\cmake``.

    The function also make sure to prepend ``C:\\cmake\\bin``
    to the ``PATH``."""

    cmake_version_major = cmake_version.split(".")[0]
    cmake_version_minor = cmake_version.split(".")[1]

    _log("Downloading CMake", cmake_version)
    remote_file = urlopen(
        "https://cmake.org/files/v{}.{}/cmake-{}-win32-x86.zip".format(
            cmake_version_major, cmake_version_minor, cmake_version))

    with open("C:\\cmake.zip", "wb") as local_file:
        shutil.copyfileobj(remote_file, local_file)

    _log("Unpacking CMake")

    try:
        os.mkdir("C:\\cmake")
    except OSError:
        pass

    with zipfile.ZipFile("C:\\cmake.zip") as local_zip:
        local_zip.extractall("C:\\cmake")

    _env_prepend("PATH", "C:\\cmake\bin")


if __name__ == '__main__':
    install(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CMAKE_VERSION)
