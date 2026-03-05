#!/usr/bin/env bash

SCRIPT_ROOT=$(dirname "$0")
FILENAME=index.js
SCRIPT=export.js

path=$(curl -sSL https://www.fknc.top/ | grep /assets | grep js | cut -d '"' -f 4)
curl -sSL https://www.fknc.top/${path} -o "${FILENAME}"

PYTHONUTF8=1 python "${SCRIPT_ROOT}/extract.py"
node "${SCRIPT}"

rm -rf "${SCRIPT}"
