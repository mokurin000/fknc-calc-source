#!/usr/bin/env bash

SCRIPT_ROOT=$(dirname "$0")
FILENAME=index.js

curl -sSL https://www.fknc.top/assets/index-CIyMZ-Re.js -o "${FILENAME}"

PYTHONUTF8=1 python "${SCRIPT_ROOT}/extract.py"
node export.js
