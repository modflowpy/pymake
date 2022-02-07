#!/bin/bash

# SPDX-FileCopyrightText: 2020 Intel Corporation
#
# SPDX-License-Identifier: MIT

source /opt/intel/oneapi/setvars.sh

# print intel compiler versions
ifort --version
icc --version

# run pytest
pytest -v -n=auto --dist=loadfile -m=base --durations=0 --cov=pymake --cov-report=xml autotest/

