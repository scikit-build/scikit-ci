.. scikit-ci documentation master file, created by
   sphinx-quickstart on Sat Oct  8 01:28:33 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to scikit-ci's documentation!
=====================================

scikit-ci enables a centralized and simpler CI configuration for Python
extensions.

By having ``appveyor.yml``, ``circle.yml`` and ``.travis.yml`` calling
the scikit-ci command-line executable, all the CI steps for all
service can be fully described in one ``scikit-ci.yml`` configuration file.

.. toctree::
   :maxdepth: 2
   :caption: User guide

   installation
   usage
   scikit-ci-yml.rst
   contributing
   authors
   history

.. toctree::
   :maxdepth: 2
   :caption: For maintainers

   make_a_release


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Resources
=========

* Free software: Apache Software license
* Documentation: http://scikit-ci.readthedocs.org
* Source code: https://github.com/scikit-build/scikit-ci
* Mailing list: https://groups.google.com/forum/#!forum/scikit-build