
"""
Usage::

    import patch_vs2008
    patch_vs2008.apply_patch()

"""

import os
import shutil
import sys
import zipfile

from subprocess import check_call

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

PATCH_URL = \
    "https://github.com/menpo/condaci/raw/master/vs2008_patch.zip"


def _log(*args):
    script_name = os.path.basename(__file__)
    print("[appveyor:%s] " % script_name + " ".join(args))
    sys.stdout.flush()


def apply_patch():
    """Implement workaround for 64-bit Visual Studio 2008"""

    if os.environ["PYTHON_ARCH"] == "64":
        _log("Downloading 64-bit Visual Studio Fix")
        remote_zip = urlopen(PATCH_URL)
        with open("C:\\vs2008_patch.zip", "wb") as local_zip:
            shutil.copyfileobj(remote_zip, local_zip)

        _log("Unpacking 64-bit Visual Studio Fix")
        with zipfile.ZipFile("C:\\vs2008_patch.zip") as local_zip:
            local_zip.extractall("C:\\vs2008_patch")

        _log("Applying 64-bit Visual Studio Fix")
        check_call(
            [
                "cmd.exe",
                "/E:ON",
                "/V:ON",
                "/C",
                "C:\\vs2008_patch\\setup_x64.bat"
            ],
            cwd="C:\\vs2008_patch")

if __name__ == '__main__':
    apply_patch()
