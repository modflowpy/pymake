#!/bin/bash

sphinx-apidoc -e -o source/ ../pymake/
make html

