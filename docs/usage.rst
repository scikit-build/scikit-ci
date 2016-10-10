=====
Usage
=====

The scikit-ci command line executable allows to execute commands associated
with steps described in a ``scikit-ci.yml`` configuration file.



Calling scikit-ci through ``python -m ci``
------------------------------------------

You can invoke scikit-ci through the Python interpreter from the command line::

    python -m ci [...]

This is equivalent to invoking the command line script ``ci [...]``
directly.


Getting help on version, option names
-------------------------------------

::

    ci --version   # shows where ci was imported from
    ci -h | --help # show help on command line
