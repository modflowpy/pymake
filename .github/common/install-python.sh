#!/bin/bash

python -m pip install --upgrade pip
pip install wheel
pip install pytest pytest-cov pytest-xdist pytest-dependency pytest-benchmark pytest-cases pytest-dotenv pytest-virtualenv flaky coverage
pip install appdirs matplotlib
pip install https://github.com/modflowpy/flopy/zipball/develop
pip install https://github.com/MODFLOW-USGS/modflow-devtools/zipball/develop

pip install .

