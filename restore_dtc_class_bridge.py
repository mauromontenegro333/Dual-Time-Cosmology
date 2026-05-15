#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path.cwd().resolve()
for rel in ["include/background.h","source/input.c","source/background.c"]:
    p = ROOT/rel
    for suffix in [".dtc_v04_backup",".dtc_bridge_backup"]:
        b = p.with_suffix(p.suffix + suffix)
        if b.exists():
            shutil.copy2(b,p)
            print(f"[restore] {b} -> {p}")
            break
    else:
        print(f"[skip] no backup for {p}")
