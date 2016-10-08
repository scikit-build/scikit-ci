.. :changelog:

History
-------

scikit-ci was initially developed in May 2016 by Omar Padron to facilitate the
continuous integration of the scikit-build project.

At that time, it already consisted of a driver script calling methods specific
to each continuous integration service. By having each CI service calling the
same driver script, there was no need to deal with implementing install/test/build
steps over and over in different scripting languages (power shell, shell or
windows batch). Instead all code was implemented in python code leveraging the
subprocess module.

Later in early September 2016, with the desire to setup cross-platform continuous
integration for other project and avoid duplication or maintenance hell, a
dedicated repository was created. By simply cloning the repository, it was
possible to more easily enable CI for other projects.

While this was an improvement, all the steps were still hardcoded in the driver
scripts, the project was not easily customizable. More could be done to improve
the user experience.

Finally, in late September 2016, all hardcoded code was moved into standalone
executable python scripts. Then, Jean-Christophe came up with the concept of
scikit-ci.yml configuration file. This configuration file allows to describe the
commands and environment for each step (install, test and build) specific to a
project and associated continuous integration services.
