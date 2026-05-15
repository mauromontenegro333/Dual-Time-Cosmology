#!/usr/bin/env bash
set -euo pipefail
CLASS_DIR="${1:-$HOME/dtc_run/class_dtc}"
cd "$CLASS_DIR"
CC_BIN="${CC:-cc}"
"$CC_BIN" -Iinclude -DDTC_CLOCK_STANDALONE source/dtc_clock.c -lm -o dtc_clock_check
./dtc_clock_check
