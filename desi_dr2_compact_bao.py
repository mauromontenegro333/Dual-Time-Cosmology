"""
DESI DR2 compact BAO likelihood for the DTC CLASS bridge.

This is a real data likelihood, not a smoke/dummy likelihood. It compares
CLASS predictions for D_M/r_d, D_H/r_d, and D_V/r_d against the compact
DESI DR2 BAO summary table used in the DTC manuscript.

Important scope note:
- This uses the table-level per-bin errors and the listed D_M-D_H
  correlations.
- It is not a replacement for the official DESI likelihood package if that
  package provides a larger covariance matrix or extra cross-bin correlations.
- It is suitable as the first real Cobaya data-likelihood test for the DTC
  CLASS bridge.

The function is intentionally implemented as a plain external Cobaya
likelihood. It imports `classy` directly from the active Python environment,
so it uses the patched CLASS/classy installation you already built.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple
import math
import os

import numpy as np

LOGZERO = -1.0e100
FIDUCIAL_H = 0.674
FIDUCIAL_DTC_OMEGA_R = 9.2e-5
FIDUCIAL_DTC_OMEGA_R_H2 = FIDUCIAL_DTC_OMEGA_R * FIDUCIAL_H * FIDUCIAL_H


@dataclass(frozen=True)
class BaoDatum:
    tracer: str
    z: float
    observable: str  # "DVrd", "DMrd", or "DHrd"
    value: float
    sigma: float
    corr_group: str = ""


# Compact DESI DR2 BAO summary used in the DTC manuscript table.
# The BGS point is isotropic DV/rd. The remaining points are anisotropic
# pairs DM/rd and DH/rd with the listed pairwise correlation coefficient.
BAO_DATA: Tuple[BaoDatum, ...] = (
    BaoDatum("BGS", 0.295, "DVrd", 7.942, 0.075),
    BaoDatum("LRG1", 0.510, "DMrd", 13.588, 0.167, "LRG1"),
    BaoDatum("LRG1", 0.510, "DHrd", 21.863, 0.425, "LRG1"),
    BaoDatum("LRG2", 0.706, "DMrd", 17.351, 0.177, "LRG2"),
    BaoDatum("LRG2", 0.706, "DHrd", 19.455, 0.330, "LRG2"),
    BaoDatum("LRG3_ELG1", 0.934, "DMrd", 21.576, 0.152, "LRG3_ELG1"),
    BaoDatum("LRG3_ELG1", 0.934, "DHrd", 17.641, 0.193, "LRG3_ELG1"),
    BaoDatum("ELG2", 1.321, "DMrd", 27.601, 0.318, "ELG2"),
    BaoDatum("ELG2", 1.321, "DHrd", 14.176, 0.221, "ELG2"),
    BaoDatum("QSO", 1.484, "DMrd", 30.512, 0.760, "QSO"),
    BaoDatum("QSO", 1.484, "DHrd", 12.817, 0.516, "QSO"),
    BaoDatum("LYA", 2.330, "DMrd", 38.988, 0.531, "LYA"),
    BaoDatum("LYA", 2.330, "DHrd", 8.632, 0.101, "LYA"),
)

PAIR_CORRELATIONS: Dict[str, float] = {
    "LRG1": -0.459,
    "LRG2": -0.404,
    "LRG3_ELG1": -0.416,
    "ELG2": -0.434,
    "QSO": -0.500,
    "LYA": -0.431,
}


def _build_covariance(data: Iterable[BaoDatum]) -> np.ndarray:
    data = tuple(data)
    cov = np.diag([d.sigma * d.sigma for d in data])
    for group, corr in PAIR_CORRELATIONS.items():
        idx = [i for i, d in enumerate(data) if d.corr_group == group]
        if len(idx) != 2:
            raise ValueError(f"Expected exactly two BAO entries for group {group}, got {len(idx)}")
        i, j = idx
        cov[i, j] = corr * data[i].sigma * data[j].sigma
        cov[j, i] = cov[i, j]
    return cov


COV = _build_covariance(BAO_DATA)
INV_COV = np.linalg.inv(COV)
DATA_VECTOR = np.array([d.value for d in BAO_DATA], dtype=float)


def _finite_positive(x: float, name: str) -> float:
    y = float(x)
    if not math.isfinite(y) or y <= 0.0:
        raise ValueError(f"{name} is not finite positive: {x!r}")
    return y


def _class_params(
    h: float,
    omega_b: float,
    omega_cdm: float,
    A_s: float,
    n_s: float,
    tau_reio: float,
    dtc_n0: float,
    dtc_zt: float,
    dtc_beta: float,
    dtc_n_shelf: float,
    dtc_z_on: float,
    dtc_z_off: float,
) -> Dict[str, object]:
    """Build CLASS input parameters matching the DTC v0.4b bridge."""
    return {
        # Minimal output keeps this likelihood fast. CLASS still computes the
        # background/thermo quantities needed for distances and r_d.
        "output": "",
        "h": _finite_positive(h, "h"),
        "omega_b": _finite_positive(omega_b, "omega_b"),
        "omega_cdm": _finite_positive(omega_cdm, "omega_cdm"),
        "A_s": _finite_positive(A_s, "A_s"),
        "n_s": _finite_positive(n_s, "n_s"),
        "tau_reio": _finite_positive(tau_reio, "tau_reio"),
        # DTC bridge switch and density bookkeeping. Keep the explicit
        # DTC density parameters synchronized with the sampled physical
        # densities. At the benchmark point this gives Omega_m close to 0.315
        # and Omega_r close to 9.2e-5.
        "has_dtc_clock": 1,
        "dtc_Omega_m": float((omega_b + omega_cdm) / (h * h)),
        "dtc_Omega_r": float(FIDUCIAL_DTC_OMEGA_R_H2 / (h * h)),
        # DTC clock-transition parameters sampled by Cobaya.
        "dtc_n0": float(dtc_n0),
        "dtc_zt": float(dtc_zt),
        "dtc_beta": float(dtc_beta),
        "dtc_n_shelf": float(dtc_n_shelf),
        "dtc_z_on": float(dtc_z_on),
        "dtc_z_off": float(dtc_z_off),
        "dtc_alpha": 8.0,
        "dtc_gamma": 8.0,
        "dtc_M_chi_over_H0": 1000.0,
        "dtc_Z_chi": 1.0,
        "dtc_C_X": 0.0,
    }


def _prediction_vector(cosmo) -> np.ndarray:
    """Return predictions in the same order as DATA_VECTOR."""
    rd = float(cosmo.rs_drag())
    _finite_positive(rd, "rs_drag")

    preds: List[float] = []
    for d in BAO_DATA:
        z = float(d.z)
        da = float(cosmo.angular_distance(z))  # Mpc
        h_z = float(cosmo.Hubble(z))           # 1/Mpc in CLASS units where c=1
        _finite_positive(da, f"angular_distance({z})")
        _finite_positive(h_z, f"Hubble({z})")
        dm = (1.0 + z) * da
        dh = 1.0 / h_z
        dv = (z * dm * dm * dh) ** (1.0 / 3.0)
        if d.observable == "DMrd":
            preds.append(dm / rd)
        elif d.observable == "DHrd":
            preds.append(dh / rd)
        elif d.observable == "DVrd":
            preds.append(dv / rd)
        else:
            raise ValueError(f"Unknown BAO observable {d.observable!r}")
    return np.array(preds, dtype=float)


def bao_chi2_from_predictions(preds: np.ndarray) -> float:
    residual = np.asarray(preds, dtype=float) - DATA_VECTOR
    return float(residual @ INV_COV @ residual)


def bao_chi2(
    h: float,
    omega_b: float,
    omega_cdm: float,
    A_s: float,
    n_s: float,
    tau_reio: float,
    dtc_n0: float,
    dtc_zt: float,
    dtc_beta: float,
    dtc_n_shelf: float,
    dtc_z_on: float,
    dtc_z_off: float,
) -> float:
    """Compute DESI DR2 compact BAO chi^2 by running patched CLASS/classy."""
    from classy import Class

    params = _class_params(
        h, omega_b, omega_cdm, A_s, n_s, tau_reio,
        dtc_n0, dtc_zt, dtc_beta, dtc_n_shelf, dtc_z_on, dtc_z_off,
    )
    cosmo = Class()
    try:
        cosmo.set(params)
        cosmo.compute()
        preds = _prediction_vector(cosmo)
        chi2 = bao_chi2_from_predictions(preds)
        if os.environ.get("DTC_BAO_DEBUG"):
            print("DTC DESI DR2 BAO chi2 =", chi2)
            for datum, pred in zip(BAO_DATA, preds):
                pull = (pred - datum.value) / datum.sigma
                print(f"  {datum.tracer:10s} z={datum.z:5.3f} {datum.observable:4s} pred={pred:10.5f} data={datum.value:10.5f} pull={pull:+8.3f}")
        if not math.isfinite(chi2):
            return float("inf")
        return chi2
    finally:
        try:
            cosmo.struct_cleanup()
        except Exception:
            pass
        try:
            cosmo.empty()
        except Exception:
            pass


def loglike(
    h: float,
    omega_b: float,
    omega_cdm: float,
    A_s: float,
    n_s: float,
    tau_reio: float,
    dtc_n0: float,
    dtc_zt: float,
    dtc_beta: float,
    dtc_n_shelf: float,
    dtc_z_on: float,
    dtc_z_off: float,
) -> float:
    """Cobaya external likelihood: return log L = -chi^2/2."""
    try:
        chi2 = bao_chi2(
            h, omega_b, omega_cdm, A_s, n_s, tau_reio,
            dtc_n0, dtc_zt, dtc_beta, dtc_n_shelf, dtc_z_on, dtc_z_off,
        )
        if not math.isfinite(chi2):
            return LOGZERO
        return -0.5 * chi2
    except Exception as exc:
        if os.environ.get("DTC_BAO_DEBUG"):
            print("DTC DESI DR2 BAO likelihood failed:", repr(exc))
        return LOGZERO


def fiducial_chi2() -> float:
    """Convenience check at the DTC v0.4 benchmark point."""
    return bao_chi2(
        h=0.674,
        omega_b=0.02237,
        omega_cdm=0.1200,
        A_s=2.1e-9,
        n_s=0.965,
        tau_reio=0.054,
        dtc_n0=0.7194,
        dtc_zt=1.5454,
        dtc_beta=6.8739,
        dtc_n_shelf=0.3793,
        dtc_z_on=2.350,
        dtc_z_off=11.003,
    )


if __name__ == "__main__":
    print(f"fiducial DESI DR2 compact BAO chi2 = {fiducial_chi2():.6g}")
