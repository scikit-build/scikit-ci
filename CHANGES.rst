=============
Release Notes
=============

This is the list of changes to scikit-build between each release. For full
details, see the commit logs at http://github.com/scikit-build/scikit-ci

Next Release
============

* Fix installation of using Python 3.4

Scikit-ci 0.20.0
================

* Support environment file `env.json` update from within step.

Scikit-ci 0.19.0
================

* Streamline use of `ci.driver.Driver.save_env` ensuring provided dictionary is stringified.

Scikit-ci 0.18.0
================

* Add support for Azure Pipelines

Scikit-ci 0.17.0
================

* Add support for ruamel.yaml >= 0.15.52 and fix `AttributeError: 'CommentedMap' object has no attribute 'replace'` error.
