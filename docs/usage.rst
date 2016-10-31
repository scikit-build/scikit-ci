=====
Usage
=====

The scikit-ci command line executable allows to execute commands associated
with steps described in a scikit-ci
:doc:`configuration file </scikit-ci-yml>`.


Executing scikit-ci steps
-------------------------

Invoking scikit-ci will execute all steps listed in
a scikit-ci :doc:`configuration file </scikit-ci-yml>`::

    ci

This command executes in order the steps listed below:

- before_install
- install
- before_build
- build
- test
- after_test

It also possible to execute a given step and its dependent steps::

    ci build

In that case, the executed steps will be:

- before_install
- install
- before_build
- build

.. note::

    Remember that:

    - steps are executed following a specific :ref:`ordering <step_order>`

    - scikit-ci :ref:`keeps track <keeping_track_executed_steps>` of previously
      executed steps.

    - environment variables set in ``step(n)`` will be available in ``step(n+1)``.
      For more details, see :ref:`environment_variable_persistence`


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
