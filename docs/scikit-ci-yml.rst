==================
Configuration file
==================

The configuration file is read by the scikit-ci executable to find out which
commands to execute for a given step.

The configuration file should named ``scikit-ci.yml`` and is usually added
to the root of a project.

It is a `YAML <http://www.yaml.org/spec/1.2/spec.html>`_ file that
can be validated against `scikit-ci-schema.yml <https://github.com/scikit-build/scikit-ci-schema>`_.


Concept of Step
---------------

A step consist of a list of ``commands`` and optional key/value pairs
describing the ``environment``.

More specifically, a step can be described using the following
structure:

.. code-block:: yaml

  before_install:
    environment:
      FOO: bar
    commands:
      - echo "Hello world"


where ``before_install`` can be replaced by any of these:

- ``before_install``
- ``install``
- ``before_build``
- ``build``
- ``test``
- ``after_test``


.. _step_mapping:

Mapping with Appveyor, CircleCI and TravisCI steps
--------------------------------------------------

scikit-ci do not impose any particular mapping.

Documentation specific to each services is available here:

  - `Appveyor build pipeline <https://www.appveyor.com/docs/build-configuration/#build-pipeline>`_
  - `Azure pipelines <https://docs.microsoft.com/en-us/azure/devops/pipelines/>`_
  - `CircleCI configuration 2.0 <https://circleci.com/docs/2.0/configuration-reference/>`_
  - `CircleCI configuration 1.0 <https://circleci.com/docs/configuration/>`_ (deprecated)
  - `TravisCI build lifecycle <https://docs.travis-ci.com/user/customizing-the-build/#The-Build-Lifecycle>`_

Reported below are some recommended associations that
are know to work.

  - ``appveyor.yml``:

  .. literalinclude:: ../appveyor.yml
     :language: yaml
     :start-after: scikit-ci-yml.rst: start
     :end-before: scikit-ci-yml.rst: end
     :emphasize-lines: 2, 5, 8, 11

  .. note:: Since on windows the ``ci`` executable is installed in the ``Scripts``
            directory (e.g `C:\\Python27\\Scripts\\ci.exe`) which is not in the
            ``PATH`` by default, the ``python -m ci`` syntax is used.

  - ``azure-pipelines.yml``:
     :language: yaml
     :start-after: scikit-ci-yml.rst: start
     :end-before: scikit-ci-yml.rst: end
     :emphasize-lines: 1, 4, 7, 10

  - ``.circleci/config.yml`` (CircleCI 2.0):


  .. literalinclude:: ../.circleci/config.yml
     :language: yaml
     :start-after: scikit-ci-yml.rst: start
     :end-before: scikit-ci-yml.rst: end
     :emphasize-lines: 23, 28, 33, 38, 43


  - ``circle.yml`` (CircleCI 1.0):


  .. literalinclude:: circle-v1-yml.txt
     :language: yaml
     :start-after: scikit-ci-yml.rst: start
     :end-before: scikit-ci-yml.rst: end
     :emphasize-lines: 6, 10, 16


  - ``.travis.yml``

  .. literalinclude:: ../.travis.yml
     :language: yaml
     :start-after: scikit-ci-yml.rst: start
     :end-before: scikit-ci-yml.rst: end
     :emphasize-lines: 2, 5, 8

.. _step_order:

Order of steps
--------------

scikit-ci execute steps considering the following order:

#. ``before_install``
#. ``install``
#. ``before_build``
#. ``build``
#. ``test``
#. ``after_test``

This means that the :ref:`mapping specified <step_mapping>` in the continuous
integration file has to be done accordingly.


Automatic execution of dependent steps
--------------------------------------

Considering the :ref:`step ordering <step_order>`, executing any ``step(n)``
ensures that ``step(n-1)`` has been executed before.


.. _keeping_track_executed_steps:

Keeping track of executed steps
-------------------------------

scikit-ci keeps track of executed steps setting environment variables of the
form ``SCIKIT_CI_<STEP_NAME>`` where ``<STEP_NAME>`` is any of the step name
in upper-case.

.. note::

    Specifying the command line option ``--force`` allows to force
    the execution of the steps ignoring the values of the ``SCIKIT_CI_<STEP_NAME>``
    environment variables.

.. _environment_variable_persistence:

Environment variable persistence
--------------------------------

Environment variable defined in any given step are always guaranteed to be
set in steps executed afterward.

This is made possible by serializing the environment on the filesystem.


.. note::

    After executing steps, a file named ``env.json`` is created in the current
    directory along side ``scikit-ci.yml``. This is where the environment is
    cached for re-use in subsequent steps.

    Specifying the command line option ``--clear-cached-env`` allows to execute
    steps after removing the ``env.json`` file.


Step specialization
-------------------

For any given step, it is possible to specify ``commands`` and ``environment``
variables specific to each continuous integration service.

Recognized services are:

  - ``appveyor``
  - ``azure``
  - ``circle``
  - ``travis``

Commands
^^^^^^^^

``commands`` common to all services are executed first, then ``commands`` specific
to each services are executed.

For example, considering this configuration used on CircleCI and TravisCI:

.. code-block:: yaml

  before_install:
    commands:
      - echo "Hello Everywhere"

    circle:
      commands:
        - echo "Hello on CircleCI"

    travis:
      linux:
        commands:
          - echo "Hello on TravisCI"


The output on the different service will be the following:


  - CircleCI:

  ::

    Hello Everywhere
    Hello on CircleCI


  - TravisCI:

  ::

    Hello Everywhere
    Hello on TravisCI


.. note:: Sections :ref:`command_specification` and :ref:`python_command_specification`
          describe the different types of command.

Environment
^^^^^^^^^^^

Similarly, ``environment`` can be overridden for each service.

For example, considering this configuration used on CircleCI and TravisCI:

.. code-block:: yaml

  before_install:

    circle:
      environment:
        CATEGORY_2: 42

    travis:
      linux:
        environment:
          CATEGORY_1: 99

    environment:
      CATEGORY_1: 1
      CATEGORY_2: 2

    commands:
      - echo "CATEGORY_1 is ${CATEGORY_1}"
      - echo "CATEGORY_2 is ${CATEGORY_2}"


The output on the different service will be the following:

  - on CircleCI:

  ::

    CATEGORY_1 is 1
    CATEGORY_2 is 42

  - on TravisCI:

  ::

    CATEGORY_1 is 99
    CATEGORY_2 is 2


Reserved Environment Variables
------------------------------

  - ``CI_NAME``:  This variable is automatically set by scikit-ci and will
    contain the name of the continuous integration service currently executing
    the step.

.. _environment_variable_usage:

Environment variable usage
--------------------------

To facilitate the `use <https://en.wikipedia.org/wiki/Environment_variable#Use_and_display>`_
of environment variable across interpreters, scikit-ci uses a specific syntax.

Environment variable specified using ``$<NAME_OF_VARIABLE>`` in both commands
and environment variable will be expanded.

For example, considering this configuration used on Appveyor, CircleCI
and TravisCI:

.. code-block:: yaml

  before_install:

    appveyor:
      environment:
        TEXT: Windows$<TEXT>

    travis:
      linux:
        environment:
          TEXT: LinuxWorld

    environment:
      TEXT: World

    commands:
      - echo $<TEXT>

The output on the different service will be the following:

  - on Appveyor:

  ::

    WindowsWorld

  - on CircleCI:

  ::

    World

  - on TravisCI:

  ::

    LinuxWorld


.. note:: On system having a POSIX interpreter, the environment variable will
          **NOT** be expanded if included in string start with a single quote.

          .. autoclass:: ci.driver.Driver
             :members: expand_command

.. _command_specification:

Command Specification
---------------------

Specifying command composed of a program name and arguments is supported on all
platforms.

For example:

.. code-block:: yaml

  test:
    commands:
      - echo "Hello"
      - python -c "print('world')"
      - git clone git://github.com/scikit-build/scikit-ci

On unix based platforms (e.g CircleCI and TravisCI), commands are interpreted
using ``bash``.

On windows based platform (e.g Appveyor), commands are
interpreted using the windows command terminal ``cmd.exe``.

Since both interpreters expand quotes differently, we recommend to avoid single
quoting argument. The following table list working recipes:


.. table::

    +----------------------------------------+----------------------------+-----------------------------------+
    |                                        |  CircleCi, TravisCI        | Appveyor                          |
    +========================================+============================+===================================+
    | **scikit-ci command**                  |  **bash output**           | **cmd output**                    |
    +----------------------------------------+----------------------------+-----------------------------------+
    | ``echo Hello1``                        |  Hello1                    | Hello1                            |
    +----------------------------------------+----------------------------+-----------------------------------+
    | ``echo "Hello2"``                      |  Hello2                    | "Hello2"                          |
    +----------------------------------------+----------------------------+-----------------------------------+
    | ``echo 'Hello3'``                      |  Hello3                    | 'Hello3'                          |
    +----------------------------------------+----------------------------+-----------------------------------+
    | ``python -c "print('Hello4')"``        |  Hello4                    | Hello4                            |
    +----------------------------------------+----------------------------+-----------------------------------+
    | ``python -c 'print("Hello5")'``        |  Hello5                    | ``no output``                     |
    +----------------------------------------+----------------------------+-----------------------------------+
    | ``python -c "print('Hello6\'World')"`` |  Hello6'World              | Hello6'World                      |
    +----------------------------------------+----------------------------+-----------------------------------+

And here are the values associated with ``sys.argv`` for different scikit-ci commands:

::

    python program.py --things "foo" "bar" --more-things "doo" 'dar'


Output on CircleCi, TravisCI::

     arg_1 [--things]
     arg_2 [foo]
     arg_3 [bar]
     arg_4 [--more-things]
     arg_5 [doo]
     arg_6 [dar]


Output on Appveyor::

     arg_1 [--things]
     arg_2 [foo]
     arg_3 [bar]
     arg_4 [--more-things]
     arg_5 [doo]
     arg_6 ['dar']    # <-- Note the presence of single quotes


::

    python program.py --things "foo" "bar" --more-things "doo" 'dar'


Output on CircleCi, TravisCI::

     arg_1 [--the-foo=foo]
     arg_2 [-the-bar=bar]

Output on Appveyor::

     arg_1 [--the-foo=foo]
     arg_2 [-the-bar='bar']    # <-- Note the presence of single quotes


.. note::

    Here are the source of ``program.py``:

    .. code-block:: python

        import sys
        for index, arg in enumerate(sys.argv):
            if index == 0:
                continue
            print("arg_%s [%s]" % (index, sys.argv[index]))


.. _python_command_specification:

Python Command Specification
----------------------------

.. versionadded:: 0.10.0

The ``python`` commands are supported on all platforms.

For example:

.. code-block:: yaml

  test:
    commands:
      - python: print("single_line")
      - python: "for letter in ['a', 'b', 'c']: print(letter)"
      - python: |
                import os
                if 'FOO' in os.environ:
                    print("FOO is set")
                else:
                    print("FOO is *NOT* set")


.. note::

    By using ``os.environ``, they remove the need for specifying environment
    variable using the ``$<NAME_OF_VARIABLE>`` syntax described in
    :ref:`environment_variable_usage`.
