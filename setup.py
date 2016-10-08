#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from setuptools import setup

with open('README.rst', 'r') as fp:
    readme = fp.read()

with open('requirements.txt', 'r') as fp:
    requirements = list(filter(bool, (line.strip() for line in fp)))

with open('requirements-dev.txt', 'r') as fp:
    dev_requirements = list(filter(bool, (line.strip() for line in fp)))

# Require pytest-runner only when running tests
pytest_runner = (['pytest-runner>=2.0,<3dev']
                 if any(arg in sys.argv for arg in ('pytest', 'test'))
                 else [])

setup_requires = pytest_runner

setup(
    name='scikit-ci',

    version='0.5.0',

    author='Jean-Christophe Fillion-Robin and the scikit-build team',
    author_email='jchris.fillion',

    url='https://github.com/scikit-build/scikit-ci',

    description='scikit-ci.yml: Centralized CI configuration for '
                'Python extensions.',
    long_description=readme,

    packages=['ci'],
    package_data={},
    include_package_data=True,
    zip_safe=False,

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache 2.0 License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Build Tools'
    ],

    license="Apache 2.0",

    keywords='CI Appveyor CircleCI Travis',

    setup_requires=setup_requires,
    install_requires=requirements,
    tests_require=dev_requirements,
)
