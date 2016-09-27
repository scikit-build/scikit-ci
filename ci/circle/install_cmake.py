
"""
Usage::

    import install_cmake
    install_cmake.install()

"""

from subprocess import check_call


def install():
    """Download and install CMake into ``/usr/local``."""

    check_call([
        "wget", "--no-check-certificate", "--progress=dot",
        "https://cmake.org/files/v3.5/cmake-3.5.0-Linux-x86_64.tar.gz"
    ])
    check_call(["tar", "xzf", "cmake-3.5.0-Linux-x86_64.tar.gz"])
    check_call([
        "sudo", "rsync", "-avz", "cmake-3.5.0-Linux-x86_64/", "/usr/local"
    ])


if __name__ == '__main__':
    install()
