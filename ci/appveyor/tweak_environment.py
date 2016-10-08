
"""
Usage::

    import tweak_environment
    tweak_environment.install()

"""

import os
import sys

from xml.dom.minidom import parse


def _log(*args):
    script_name = os.path.basename(__file__)
    print("[appveyor:%s] " % script_name + " ".join(args))
    sys.stdout.flush()


def tweak():
    update_notepad_settings()


def update_notepad_settings():
    """Update notepad++ settings to facilitate its use.

    Settings updated:

     - ``TabSetting.replaceBySpace`` set to ``yes``

    """

    settings = "%s/Notepad++/config.xml" % os.environ["appdata"]

    if not os.path.exists(settings):
        _log("[notepad++] Skipping. Setting file not found:", settings)

    _log("notepad++: Parsing", settings)
    dom = parse(settings)

    _log("[notepad++] Updating")
    configs = dom.documentElement.getElementsByTagName('GUIConfigs').item(0)
    for elem in configs.getElementsByTagName('GUIConfig'):
        if elem.getAttribute('name') == "TabSetting":
            elem.setAttribute("replaceBySpace", "yes")

    _log("[notepad++] Writing", settings)
    with open(settings, "w") as output:
        dom.writexml(output)


if __name__ == '__main__':
    tweak()
