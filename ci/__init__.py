# -*- coding: utf-8 -*-

"""
scikit-ci enables a centralized and simpler CI configuration for Python
extensions.
"""

from .constants import STEPS
from .driver import execute_step
from .exceptions import SKCIError
from ._version import get_versions

__author__ = 'The scikit-build team'
__email__ = 'scikit-build@googlegroups.com'
__version__ = get_versions()['version']
del get_versions

__all__ = ["execute_step", "SKCIError", "STEPS"]
