#!/bin/bash
set -e

echo "Installing pip for Python ${TRAVIS_PYTHON_VERSION} ${RUN_TYPE} run"
pip install --upgrade pip
pip install -r requirements.travis.txt
pip install --no-binary rasterio rasterio
pip install --upgrade numpy
if [ "${RUN_TYPE}" = "flake" ]; then
  pip install flake8 pylint pylint-exit
fi
pip install shapely[vectorize]
pip install https://github.com/modflowpy/flopy/zipball/develop
pip install coveralls nose-timer
