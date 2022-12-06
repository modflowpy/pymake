#!/bin/bash

python -m pip install --upgrade pip
pip install wheel
pip install pytest pytest-cov pytest-xdist pytest-dependency coverage
pip install appdirs matplotlib
pip install https://github.com/modflowpy/flopy/zipball/develop
pip install .

