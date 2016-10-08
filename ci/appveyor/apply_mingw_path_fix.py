
"""
Usage::

    import apply_mingw_path_fix
    apply_mingw_path_fix.update_path()

"""

import os
import sys


def _log(*args):
    script_name = os.path.basename(__file__)
    print("[appveyor:%s] " % script_name + " ".join(args))
    sys.stdout.flush()


def update_path():
    """Implement workaround for MinGW on Appveyor"""
    if os.environ.get("CMAKE_GENERATOR", "").lower().startswith("mingw"):
        _log("Applying MinGW PATH fix")

        mingw_bin = os.path.normpath(
            os.path.join("C:\\", "MinGW", "bin")).lower()

        os.environ["PATH"] = os.pathsep.join(
            one_path for one_path in
            os.environ["PATH"].split(os.pathsep)

            if (
                os.path.normpath(one_path).lower() == mingw_bin or
                not (
                    os.path.exists(os.path.join(one_path, "sh.exe")) or
                    os.path.exists(os.path.join(one_path, "sh.bat")) or
                    os.path.exists(os.path.join(one_path, "sh"))
                )
            )
        )

if __name__ == '__main__':
    update_path(sys.argv[0])
