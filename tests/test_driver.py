
import os
import pytest
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../ci'))

from driver import Driver  # noqa: E402


def _expand_environment_vars_test(command, posix_shell, expected):
    environments = {
        "OTHER": "unused",
        "FO": "foo"
    }
    assert (
        Driver.expand_environment_vars(command, environments, posix_shell)
        == expected)


@pytest.mark.parametrize("command, posix_shell, expected", [
    (r"""echo "$<FO>", "$<B>", $<FO>""", False, 'echo "foo" , "$<B>" , foo'),
    (r"""echo '$<FO>', '$<B>', $<FO>""", False, "echo 'foo' , '$<B>' , foo"),
    (r"""echo "$<FO>", "$<B>", $<FO>""", True, 'echo "foo" , "$<B>" , foo'),
    (r"""echo '$<FO>', '$<B>', $<FO>""", True, "echo '$<FO>' , '$<B>' , foo"),
])
def test_expand_environment_vars(command, posix_shell, expected):
    _expand_environment_vars_test(command, posix_shell, expected)


@pytest.mark.parametrize("command, posix_shell, expected", [
    (r"""echo "$<FO>", \
"$<B>", $<FO>""", True, 'echo "foo" , "$<B>" , foo'),
    (r"""echo '$<FO>', \
'$<B>', $<FO>""", True, "echo '$<FO>' , '$<B>' , foo"),
])
def test_expand_environment_vars_with_newline(command, posix_shell, expected):
    _expand_environment_vars_test(command, posix_shell, expected)
