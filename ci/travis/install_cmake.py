
"""
Usage::

    import install_cmake
    install_cmake.install()

"""

import platform
import sys

from subprocess import check_call

DEFAULT_CMAKE_VERSION = "3.5.0"


def _log(*args):
    print(" ".join(args))
    sys.stdout.flush()


def install(cmake_version=DEFAULT_CMAKE_VERSION, is_darwin=False):
    """Download and install CMake into ``/usr/local``."""

    cmake_os = "Darwin" if is_darwin else "Linux"
    cmake_name = "cmake-{}-{}-x86_64".format(cmake_version, cmake_os)
    cmake_package = ".".join((cmake_name, "tar", "gz"))
    cmake_version_major = cmake_version.split(".")[0]
    cmake_version_minor = cmake_version.split(".")[1]

    _log("Downloading", cmake_package)
    check_call([
        "wget", "--no-check-certificate", "--progress=dot",
        "https://cmake.org/files/v{}.{}/{}".format(
            cmake_version_major, cmake_version_minor, cmake_package)
    ])

    _log("Extracting", cmake_package)
    check_call(["tar", "xzf", cmake_package])

    if is_darwin:
        prefix = "/usr/local/bin"
        _log("Removing any existing CMake in", prefix)
        check_call(
            ["sudo", "rm", "-f"] + [
                "/".join((prefix, subdir)) for subdir in
                ("cmake", "cpack", "cmake-gui", "ccmake", "ctest")
                ]
        )

        _log("Installing CMake in", prefix)
        check_call([
            "sudo",
            cmake_name + "/CMake.app/Contents/bin/cmake-gui",
            "--install"
        ])

    else:
        _log("Copying", cmake_name, "to /usr/local")
        check_call([
            "sudo", "rsync", "-avz", cmake_name + "/", "/usr/local"])


if __name__ == '__main__':
    install(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CMAKE_VERSION,
            is_darwin=platform.system().lower() == "darwin")
