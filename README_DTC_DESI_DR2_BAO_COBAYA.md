# DTC DESI DR2 compact BAO likelihood for Cobaya

This pack adds a real data likelihood to the DTC v0.4b CLASS bridge.

It compares the patched CLASS predictions for

- `D_M(z)/r_d`
- `D_H(z)/r_d`
- `D_V(z)/r_d`

against the DESI DR2 compact BAO summary table used in the DTC manuscript.

## What this is

This is a real BAO data likelihood: it computes `chi2 = residual^T C^{-1} residual` and returns `loglike = -chi2/2`.

It is not the dummy `chi2_one = 0` likelihood.

## Scope

This is the compact table-level DESI DR2 BAO likelihood. It uses:

- BGS `D_V/r_d`
- anisotropic `D_M/r_d` and `D_H/r_d` for LRG1, LRG2, LRG3+ELG1, ELG2, QSO, and Ly-alpha
- the listed per-bin `D_M-D_H` correlations

It is not a substitute for the official DESI full likelihood if that official release includes a larger covariance matrix or extra cross-bin correlations. Use this first to turn the DTC pipeline into a real data run; then replace or extend it with the official covariance for the paper-grade run.

## Files

```text
dtc_likelihoods/desi_dr2_compact_bao.py   # likelihood code
cobaya/dtc_desi_dr2_bao_real.yaml         # 5000 accepted samples
cobaya/dtc_desi_dr2_bao_test200.yaml      # quick 200 accepted-sample test
data/desi_dr2_bao_compact_summary.csv     # table-level data used by the likelihood
scripts/check_python_import.py            # checks local likelihood and classy import
scripts/run_fiducial_bao.py               # evaluates fiducial chi2 directly
```

## Install into your DTC v0.4b folder

Run this from Terminal:

```bash
cd ~/Downloads/dtc_class_cobaya_bridge_v0_4b_radiation_ic_fix
unzip -o ~/Downloads/dtc_desi_dr2_bao_likelihood_pack.zip
source ~/dtc_run/cobaya_env/bin/activate
```

If your browser downloads the zip somewhere else, adjust the path after `unzip -o`.

## Check imports

```bash
cd ~/Downloads/dtc_class_cobaya_bridge_v0_4b_radiation_ic_fix
source ~/dtc_run/cobaya_env/bin/activate
python scripts/check_python_import.py
```

You should see paths for both:

```text
likelihood module: .../dtc_likelihoods/desi_dr2_compact_bao.py
classy module: .../dtc_run/class_dtc/...
```

## Fiducial likelihood check

```bash
cd ~/Downloads/dtc_class_cobaya_bridge_v0_4b_radiation_ic_fix
source ~/dtc_run/cobaya_env/bin/activate
python scripts/run_fiducial_bao.py
```

For detailed BAO pulls, run:

```bash
DTC_BAO_DEBUG=1 python scripts/run_fiducial_bao.py
```

## Quick Cobaya data-likelihood test

```bash
cd ~/Downloads/dtc_class_cobaya_bridge_v0_4b_radiation_ic_fix
source ~/dtc_run/cobaya_env/bin/activate
cobaya-run cobaya/dtc_desi_dr2_bao_test200.yaml
```

This should create:

```text
chains/dtc_desi_dr2_bao_test200.1.txt
chains/dtc_desi_dr2_bao_test200.log
chains/dtc_desi_dr2_bao_test200.updated.yaml
```

## Longer BAO MCMC

```bash
cd ~/Downloads/dtc_class_cobaya_bridge_v0_4b_radiation_ic_fix
source ~/dtc_run/cobaya_env/bin/activate
cobaya-run cobaya/dtc_desi_dr2_bao_real.yaml
```

This should create:

```text
chains/dtc_desi_dr2_bao_real.1.txt
chains/dtc_desi_dr2_bao_real.log
chains/dtc_desi_dr2_bao_real.updated.yaml
```

## Save the result bundle

```bash
cd ~/Downloads/dtc_class_cobaya_bridge_v0_4b_radiation_ic_fix
mkdir -p ~/Desktop/dtc_desi_bao_results
cp cobaya/dtc_desi_dr2_bao_real.yaml ~/Desktop/dtc_desi_bao_results/
cp cobaya/dtc_desi_dr2_bao_test200.yaml ~/Desktop/dtc_desi_bao_results/
cp -r dtc_likelihoods data scripts chains ~/Desktop/dtc_desi_bao_results/
cd ~/Desktop
zip -r dtc_desi_bao_results.zip dtc_desi_bao_results
```

## What success looks like

You want Cobaya to show actual MCMC sampling with no warning that the likelihood is independent of parameters.

The old dummy run printed this warning:

```text
Theories {classy} do not appear to be actually used for anything
```

This likelihood bypasses that issue by calling patched `classy` directly inside the likelihood. Every likelihood evaluation runs CLASS, computes BAO distances, and returns a real DESI DR2 compact BAO log-likelihood.

## Next paper-grade upgrade

For the 10/10 manuscript requirement, replace the compact table-level covariance in `desi_dr2_compact_bao.py` with the official DESI DR2 full covariance/likelihood when available in your analysis repo. The likelihood code is written so the data vector and covariance block can be swapped cleanly.
