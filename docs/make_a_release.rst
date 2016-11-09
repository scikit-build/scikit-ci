=====================
How to Make a Release
=====================

A core developer should use the following steps to create a release of
**scikit-ci**.

0. Configure `~/.pypirc` as described `here <https://packaging.python.org/distributing/#uploading-your-project-to-pypi>`_.

1. Make sure that all CI tests are passing.

2. Tag the release. Requires a GPG key with signatures. For version *X.Y.Z*::

    git tag -s -m "scikit-ci X.Y.Z" X.Y.Z upstream/master

3. Create the source tarball and binary wheels::

    git checkout master
    git fetch upstream
    git reset --hard upstream/master
    rm -rf dist/
    python setup.py sdist bdist_wheel

4. Upload the packages to the testing PyPI instance::

    twine upload --sign -r pypitest dist/*

5. Check the `PyPI testing package page <https://testpypi.python.org/pypi/scikit-ci/>`_.

6. Upload the packages to the PyPI instance::

    twine upload --sign dist/*

7. Check the `PyPI package page <https://pypi.python.org/pypi/scikit-ci/>`_.

8. Make sure the package can be installed::

    mkvirtualenv test-pip-install
    pip install scikit-ci
    rmvirtualenv test-pip-install
