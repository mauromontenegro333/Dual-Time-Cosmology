#!/usr/bin/env python3
"""Run the DTC DESI DR2 compact BAO likelihood at the fiducial point."""
from dtc_likelihoods.desi_dr2_compact_bao import fiducial_chi2

if __name__ == "__main__":
    chi2 = fiducial_chi2()
    print(f"fiducial DESI DR2 compact BAO chi2 = {chi2:.6g}")
    print(f"fiducial DESI DR2 compact BAO loglike = {-0.5*chi2:.6g}")
