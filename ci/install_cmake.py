
import sys

from .driver import Driver


DEFAULT_CMAKE_VERSION = "3.6.2"


def install(cmake_version=DEFAULT_CMAKE_VERSION):

    sys.path.insert(0, "./%s" % Driver.current_service())

    import install_cmake as ci_install_cmake
    ci_install_cmake.install(cmake_version)

if __name__ == '__main__':
    install(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CMAKE_VERSION)