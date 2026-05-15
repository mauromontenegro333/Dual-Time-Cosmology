#ifndef DTC_CLOCK_H
#define DTC_CLOCK_H

#ifdef __cplusplus
extern "C" {
#endif

typedef struct dtc_clock_parameters {
  double H0_km_s_Mpc;
  double Omega_m;
  double Omega_r;
  double z_star;
  double ell_A_target;
  double n0;
  double zt;
  double beta;
  double n_shelf;
  double z_on;
  double z_off;
  double alpha;
  double gamma;
  double Z_chi;
  double M_chi_over_H0;
  double C_X;
} dtc_clock_parameters;

typedef struct dtc_clock_background_closure {
  double E_obs;
  double H_phys;
  double H_prime_tau;
  double rho_target;
  double p_required_total;
  double rho_add;
  double p_add;
  double n;
  int used_fallback;
} dtc_clock_background_closure;

typedef struct dtc_clock_perturbations {
  double delta_X;
  double delta_Theta_over_Theta;
  double delta_chi;
  double delta_chi_prime;
  double delta_lambda;
  double delta_sigma;
  double tip_constraint_residual;
  double current_constraint_residual;
  double mu;
  double gamma_slip;
  double Sigma;
} dtc_clock_perturbations;

void dtc_clock_default_parameters(dtc_clock_parameters *p);

double dtc_clock_n_of_z(double z, const dtc_clock_parameters *p);
double dtc_clock_E_abs(double z, const dtc_clock_parameters *p);
double dtc_clock_E_obs(double z, const dtc_clock_parameters *p);
double dtc_clock_z_eq(const dtc_clock_parameters *p);
double dtc_clock_q0_numeric(const dtc_clock_parameters *p);

void dtc_clock_constraint_variables(double z, double k_mpc, double psi,
                                    const dtc_clock_parameters *p,
                                    dtc_clock_perturbations *out);

/*
  CLASS background bridge v0.4.

  IMPORTANT:
  - v0.3 tried to overwrite Omega_m/Omega_r from CLASS internal fields.
    On some CLASS stages these can be zero/unavailable, causing rho_crit=0.
  - v0.4 uses explicit DTC density parameters read from the .ini:
      dtc_Omega_m, dtc_Omega_r
    with safe defaults.

  CLASS computes:
    H^2 = rho_tot - K/a^2
  The bridge adds a geometric closure contribution so that CLASS's own
  equations return H_target = H0 E_DTC(z) while preserving its background
  table machinery.
*/
void dtc_clock_background_closure_at_a(
  double a,
  double H0_class,
  double K_class,
  double rho_standard_total,
  double p_standard_total,
  const dtc_clock_parameters *p,
  dtc_clock_background_closure *out);

#ifdef __cplusplus
}
#endif

#endif
