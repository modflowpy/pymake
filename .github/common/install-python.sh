#!/bin/bash

python -m pip install --upgrade pip
pip install wheel
pip install pytest pytest-cov pytest-xdist coverage
pip install pydotplus appdirs
pip install matplotlib
pip install https://github.com/modflowpy/flopy/zipball/develop
pip install .

