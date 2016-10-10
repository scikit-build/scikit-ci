# -*- coding: utf-8 -*-

"""
scikit-ci enables a centralized and simpler CI configuration for Python
extensions.
"""

from .constants import STEPS
from .driver import execute_step

__author__ = 'The scikit-build team'
__email__ = 'scikit-build@googlegroups.com'
__version__ = '0.5.0'

__all__ = ["execute_step", "STEPS"]
