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


where ``before_install`` can be any of these:

.. automodule:: ci.constants
   :members: STEPS


.. _step_mapping:

Mapping with Appveyor, CircleCI and TravisCI steps
--------------------------------------------------

scikit-ci do not impose any particular mapping.

Documentation specific to each services is available here:

  - `Appveyor build pipeline <https://www.appveyor.com/docs/build-configuration/#build-pipeline>`_
  - `CircleCI configuration <https://circleci.com/docs/configuration/>`_
  - `TravisCI build lifecycle <https://docs.travis-ci.com/user/customizing-the-build/#The-Build-Lifecycle>`_

Reported below are some recommended associations that
are know to work.

  - ``appveyor.yml``:

  .. literalinclude:: ../appveyor.yml
     :language: yaml
     :start-after: scikit-ci-yml.rst: start
     :end-before: scikit-ci-yml.rst: end
     :emphasize-lines: 2-3, 6-7, 10, 13

  .. note:: Since on windows the ``ci`` executable is installed in the ``Scripts``
            directory (e.g `C:\\Python27\\Scripts\\ci.exe`) which is not in the
            ``PATH`` by default, the ``python -m ci`` syntax is used.


  - ``circle.yml``:


  .. literalinclude:: ../circle.yml
     :language: yaml
     :start-after: scikit-ci-yml.rst: start
     :end-before: scikit-ci-yml.rst: end
     :emphasize-lines: 7, 9, 13, 16, 19, 25


  - ``.travis.yml``

  .. literalinclude:: ../.travis.yml
     :language: yaml
     :start-after: scikit-ci-yml.rst: start
     :end-before: scikit-ci-yml.rst: end
     :emphasize-lines: 2-3, 6, 9-10, 13


Order of steps
--------------

scikit-ci does not impose any order. The order is defined by the
:ref:`mapping specified <step_mapping>` in the continuous integration file.


Environment variable persistence
--------------------------------

Environment variable defined in any given step are always guaranteed to be
set in step executed afterward.

This is made possible by serializing the environment on the filesystem.


Step specialization
-------------------

For any given step, it is possible to specify ``commands`` and ``environment``
variables specific to each continuous integration service.

Recognized services are:

  - ``appveyor``
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
