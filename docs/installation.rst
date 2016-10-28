============
Installation
============

Install package with pip
------------------------

To install with pip::

    $ pip install scikit-ci

Install from source
-------------------

To install scikit-ci from the latest source, first obtain the source code::

    $ git clone https://github.com/scikit-build/scikit-ci
    $ cd scikit-ci

then install with::

    $ pip install .

or::

    $ pip install -e .

for development.


Dependencies
------------

Python Packages
^^^^^^^^^^^^^^^

The project has a few common Python package dependencies. The runtime
dependencies are:

.. include:: ../requirements.txt
   :literal:

The development dependencies (for testing and coverage) are:

.. include:: ../requirements-dev.txt
   :literal:
