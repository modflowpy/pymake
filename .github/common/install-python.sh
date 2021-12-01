#!/bin/bash

python -m pip install --upgrade pip
pip install wheel
pip install .
pip install pytest pytest-cov coverage
pip install pydotplus appdirs
pip install matplotlib
pip install https://github.com/modflowpy/flopy/zipball/develop

