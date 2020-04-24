#!/bin/bash
set -e

if [ "${RUN_TYPE}" = "flake" ]; then
  echo "Checking Python code with flake8..."
  flake8 --exit-zero
  echo "Checking Python code with pylint..."
  pylint --jobs=2 --errors-only ./flopy || pylint-exit $?
  if [ $? -ne 0 ]; then
    echo "An error occurred while running pylint." >&2
    exit 1
  fi
fi

echo "Running flopy autotest suite..."
nosetests -v --with-id --with-timer -w ./autotest \
  --with-coverage --cover-package=pymake
