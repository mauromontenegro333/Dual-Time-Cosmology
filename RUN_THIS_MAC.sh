#!/usr/bin/env bash
set -euo pipefail
CLASS_DIR="${1:-$HOME/dtc_run/class_dtc}"
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "[1/5] Restoring prior DTC patch if backup exists"
python3 "$ROOT/class_patch/scripts/restore_dtc_class_bridge.py" "$CLASS_DIR" || true

echo "[2/5] Installing DTC bridge v0.4b"
python3 "$ROOT/class_patch/scripts/install_dtc_class_bridge.py" "$CLASS_DIR"
cp "$ROOT"/class_patch/params/*.ini "$CLASS_DIR"/

echo "[3/5] Building CLASS"
cd "$CLASS_DIR"
make clean
make -j4 || make -j4 PYTHON=python3

echo "[4/5] Running CLASS smoke tests"
./class dtc_background_only.ini 2>&1 | tee dtc_background_only_v04b.log
grep -i "error" dtc_background_only_v04b.log || true
./class dtc_mpk.ini 2>&1 | tee dtc_mpk_v04b.log
grep -i "error" dtc_mpk_v04b.log || true
./class dtc_cls.ini 2>&1 | tee dtc_cls_v04b.log
grep -i "error" dtc_cls_v04b.log || true

echo "[5/5] Done. If each grep printed nothing, CLASS did not report an error."
