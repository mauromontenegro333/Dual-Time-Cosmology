# Technical note v0.4

v0.4 fixes v0.3's `rho_crit = 0` failure by:

1. adding explicit DTC density parameters:
   - dtc_Omega_m
   - dtc_Omega_r

2. not overwriting those from CLASS internal Omega fields during background
   initialization;

3. adding fallback checks so the bridge never drives rho_tot to zero or NaN.

The bridge adds geometric closure terms before CLASS computes H from Friedmann.
This keeps CLASS time and distance tables self-consistent, unlike the failed
direct H/H_prime override.
