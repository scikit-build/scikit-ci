
"""
Usage::

    import install_cmake
    install_cmake.install()

"""

import sys

from subprocess import check_call


def _log(*args):
    print(" ".join(args))
    sys.stdout.flush()


def install(is_darwin=False, cmake_version="3.5"):
    """Download and install CMake into ``/usr/local``."""

    cmake_os = "Darwin" if is_darwin else "Linux"
    cmake_name = "cmake-{}.0-{}-x86_64".format(cmake_version, cmake_os)
    cmake_package = ".".join((cmake_name, "tar", "gz"))

    _log("Downloading", cmake_package)
    check_call([
        "wget", "--no-check-certificate", "--progress=dot",
        "https://cmake.org/files/v{}/{}".format(
            cmake_version, cmake_package)
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
    install()
