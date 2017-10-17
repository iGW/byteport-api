#!/usr/bin/env bash

pip install wheel

python ./setup.py bdist_wheel --universal

mv ./dist/*.whl .

rm -rf build
rm -rf dist
rm -rf *.egg-info
