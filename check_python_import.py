#!/usr/bin/env python3
"""Check that the local likelihood and patched classy import."""
import importlib

like = importlib.import_module("dtc_likelihoods.desi_dr2_compact_bao")
print("likelihood module:", like.__file__)

try:
    import classy
    print("classy module:", classy.__file__)
except Exception as exc:
    raise SystemExit(f"Could not import classy: {exc}")
