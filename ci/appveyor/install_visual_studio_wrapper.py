
"""
Usage::

    import install_visual_studio_wrapper
    install_visual_studio_wrapper.install()

"""

import os
import shutil
import sys

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

SCRIPT_URL = \
    "https://raw.githubusercontent.com/ogrisel/python-appveyor-demo/" \
    "f54ec3593bcea682098a59b560c1850c19746e10/appveyor/run_with_env.cmd"

LOCAL_PATH_DEFAULT = \
    os.path.join(os.path.dirname(__file__), "run-with-visual-studio.cmd")


def install(local_path=LOCAL_PATH_DEFAULT):
    """Download ``run_with_env.cmd`` and copy it to ``local_path``"""

    print("Downloading into %s" % local_path)

    remote_script = urlopen(SCRIPT_URL)
    with open(local_path, "wb") as local_script:
        shutil.copyfileobj(remote_script, local_script)

if __name__ == '__main__':
    install(sys.argv[1])
