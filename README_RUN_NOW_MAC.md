# IMPORTANT v0.4b fix

This build fixes the CLASS abort:

```text
Omega_r = ... not close enough to 1. Decrease a_ini_over_a_today_default
```

The problem was not just `a_ini`; v0.4 applied the DTC closure even when the clock index `n(z)` was effectively zero, which spoiled CLASS radiation-era initial conditions. v0.4b gates the closure by `n(z)` so the ultra-early background remains native CLASS radiation/matter, then restores the DTC closure when the clock transition is active.

# DTC CLASS + Cobaya bridge v0.4b radiation-IC fix

This version fixes the v0.3 failure:

    rho_crit = 0.000000e+00

Cause:
v0.3 overwrote DTC Omega_m/Omega_r from CLASS fields that can be zero or unavailable
during background initialization. v0.4 reads explicit:

    dtc_Omega_m = 0.315
    dtc_Omega_r = 9.2e-5

and uses safe fallback guards.

## Run on Mac

```bash
cd ~/Desktop
unzip dtc_class_cobaya_bridge_v0_4b_radiation_ic_fixb_radiation_ic_fix.zip
cd dtc_class_cobaya_bridge_v0_4b_radiation_ic_fix

python3.11 class_patch/scripts/install_dtc_class_bridge.py ~/dtc_run/class_dtc
cp class_patch/params/*.ini ~/dtc_run/class_dtc/

cd ~/dtc_run/class_dtc
make clean
make -j4

./class dtc_background_only.ini 2>&1 | tee dtc_background_only_v04.log
grep -i "error" dtc_background_only_v04.log

./class dtc_mpk.ini 2>&1 | tee dtc_mpk_v04.log
grep -i "error" dtc_mpk_v04.log

./class dtc_cls.ini 2>&1 | tee dtc_cls_v04.log
grep -i "error" dtc_cls_v04.log
```

No output from grep means no CLASS error line was detected.

## Cobaya smoke

Only after CLASS `dtc_cls.ini` passes:

```bash
cd ~/dtc_run/class_dtc
python3.11 -m venv ~/dtc_run/cobaya_env
source ~/dtc_run/cobaya_env/bin/activate
pip install --upgrade pip setuptools wheel
pip install cobaya numpy scipy cython pyyaml
pip install -e .

cd ~/Desktop/dtc_class_cobaya_bridge_v0_4b_radiation_ic_fix
cobaya-run cobaya/dtc_smoke.yaml
```

## Restore

```bash
cd ~/Desktop/dtc_class_cobaya_bridge_v0_4b_radiation_ic_fix
python3.11 class_patch/scripts/restore_dtc_class_bridge.py ~/dtc_run/class_dtc
cd ~/dtc_run/class_dtc
make clean
make -j4
```

## Scientific status

This is a CLASS background bridge and Cobaya smoke-test package. It is not yet
the final paper-grade native perturbation implementation for the variables

    delta_X, delta_Theta, delta_chi, delta_lambda, delta_sigma

inside CLASS perturbations.
