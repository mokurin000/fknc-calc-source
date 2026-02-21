#!/usr/bin/env bash

SCRIPT_ROOT=$(dirname "$0")
FILENAME=index.js
SCRIPT=export.js

curl -sSL https://www.fknc.top/assets/index-oOwWjGI1.js -o "${FILENAME}"

PYTHONUTF8=1 python "${SCRIPT_ROOT}/extract.py"
node "${SCRIPT}"

rm -rf "${SCRIPT}"
