=========
scikit-ci
=========

+---------------------------------------------------------------------------------------------------------------------------------+
| The ``scikit-ci`` project was archived in March 2023.                                                                           |
+=================================================================================================================================+
| To build Python wheels across platforms and CI servers, consider using `cibuildwheel <https://cibuildwheel.readthedocs.io/>`_.  |
+---------------------------------------------------------------------------------------------------------------------------------+

Overview
--------

scikit-ci enables a centralized and simpler CI configuration for Python
extensions.

By having ``appveyor.yml``, ``azure-pipelines.yml``, ``circle.yml`` and ``.travis.yml`` calling
the same scikit-ci command-line executable, all the CI steps for all
service can be fully described in one ``scikit-ci.yml`` configuration file.

Latest Release
--------------

.. table::

  +--------------------------------------------------------------------------+
  | Versions                                                                 |
  +==========================================================================+
  | .. image:: https://img.shields.io/pypi/v/scikit-ci.svg?maxAge=2592000    |
  |     :target: https://pypi.python.org/pypi/scikit-ci                      |
  +--------------------------------------------------------------------------+

Build Status
------------

*Continuous integration pipelines have been disabled in March 2023. They were historically triggered on AppVeyor, Azure Pipelines, CircleCI and TravisCI services.*

Overall Health
--------------

.. image:: https://readthedocs.org/projects/scikit-ci/badge/?version=latest
    :target: http://scikit-ci.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

*Code coverage was at 95% and was historically tracked using codecov.io service until March 2023.*

Miscellaneous
-------------

* Free software: Apache Software license
* Documentation: http://scikit-ci.readthedocs.org
* Source code: https://github.com/scikit-build/scikit-ci
