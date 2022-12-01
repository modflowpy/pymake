#!/bin/bash

python -m pip install --upgrade pip
pip install wheel
pip install ".[lint, test]"
pip install https://github.com/modflowpy/flopy/zipball/develop
pip install .

