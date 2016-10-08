#!/usr/bin/env bash

set -ex

eval "$( pyenv init - )"
pyenv local $PYTHONVERSION

eval "$@"
