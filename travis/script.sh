#!/bin/bash
set -e

echo "Building executables..."
nosetests -v build_exes.py --with-id --with-timer -w ./autotest

if [ "${RUN_TYPE}" = "test" ]; then
  echo "Running flopy autotest suite..."
  nosetests -v --with-id --with-timer -w ./autotest \
    --with-coverage --cover-package=pymake
elif [ "${RUN_TYPE}" = "flake" ]; then
  echo "Checking Python code with flake8..."
  flake8 --exit-zero
  echo "Checking Python code with pylint..."
  pylint --jobs=2 --errors-only ./flopy || pylint-exit $?
  if [ $? -ne 0 ]; then
    echo "An error occurred while running pylint." >&2
    exit 1
  fi
  echo "Running flopy autotest suite..."
  nosetests -v --with-id --with-timer -w ./autotest \
    --with-coverage --cover-package=pymake
else
  echo "Unhandled RUN_TYPE=${RUN_TYPE}" >&2
  exit 1
fi