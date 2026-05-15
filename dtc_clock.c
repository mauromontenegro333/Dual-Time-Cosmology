#include <math.h>
#include <stdio.h>
#include "dtc_clock.h"

static int dtc_bad(double x) {
  return (!isfinite(x)) || (x <= 0.0);
}

static double dtc_safe_positive(double x, double fallback) {
  if ((!isfinite(x)) || (x <= 0.0)) return fallback;
  return x;
}

static double dtc_safe_pow(double x, double y) {
  if ((!isfinite(x)) || x <= 0.0) x = 1.0e-300;
  return pow(x, y);
}

void dtc_clock_default_parameters(dtc_clock_parameters *p) {
  p->H0_km_s_Mpc = 67.4;
  p->Omega_m = 0.315;
  p->Omega_r = 9.2e-5;
  p->z_star = 1089.92;
  p->ell_A_target = 301.47;
  p->n0 = 0.7194;
  p->zt = 1.5454;
  p->beta = 6.8739;
  p->n_shelf = 0.3793;
  p->z_on = 2.350;
  p->z_off = 11.003;
  p->alpha = 8.0;
  p->gamma = 8.0;
  p->Z_chi = 1.0;
  p->M_chi_over_H0 = 1.0e3;
  p->C_X = 0.0;
}

static double dtc_clock_shelf_window(double z, const dtc_clock_parameters *p) {
  const double zp1 = 1.0 + z;
  const double left = 1.0 / (1.0 + dtc_safe_pow((1.0 + p->z_on) / zp1, p->alpha));
  const double right = 1.0 / (1.0 + dtc_safe_pow(zp1 / (1.0 + p->z_off), p->gamma));
  return left * right;
}

double dtc_clock_n_of_z(double z, const dtc_clock_parameters *p) {
  if (!isfinite(z)) z = 1.0e300;
  if (z < -0.999999999) z = -0.999999999;
  const double zp1 = 1.0 + z;
  const double zt1 = 1.0 + p->zt;
  const double beta = dtc_safe_positive(p->beta, 6.8739);
  const double n_late = p->n0 / (1.0 + dtc_safe_pow(zp1 / zt1, beta));
  return n_late + p->n_shelf * dtc_clock_shelf_window(z, p);
}

double dtc_clock_E_abs(double z, const dtc_clock_parameters *p) {
  const double zp1 = 1.0 + z;
  const double Om = dtc_safe_positive(p->Omega_m, 0.315);
  const double Or = dtc_safe_positive(p->Omega_r, 9.2e-5);
  return sqrt(Or * dtc_safe_pow(zp1, 4.0) + Om * dtc_safe_pow(zp1, 3.0));
}

double dtc_clock_E_obs(double z, const dtc_clock_parameters *p) {
  if (!isfinite(z)) z = 1.0e300;
  if (z < -0.999999999) z = -0.999999999;

  const double Om = dtc_safe_positive(p->Omega_m, 0.315);
  const double Or = dtc_safe_positive(p->Omega_r, 9.2e-5);
  const double zp1 = 1.0 + z;
  const double n = dtc_clock_n_of_z(z, p);
  const double n_today = dtc_clock_n_of_z(0.0, p);
  const double omega_sum = Or*dtc_safe_pow(zp1,4.0) + Om*dtc_safe_pow(zp1,3.0);
  const double today_sum = Or + Om;

  double numerator = dtc_safe_pow(omega_sum, 1.0/(2.0*(1.0+n)));
  double denominator = dtc_safe_pow(today_sum, 1.0/(2.0*(1.0+n_today)));
  double E = numerator/denominator;

  if (dtc_bad(E)) {
    /* Last-resort safety fallback: standard matter/radiation branch. */
    E = sqrt(omega_sum / today_sum);
  }
  return E;
}

double dtc_clock_z_eq(const dtc_clock_parameters *p) {
  const double Om = dtc_safe_positive(p->Omega_m, 0.315);
  const double Or = dtc_safe_positive(p->Omega_r, 9.2e-5);
  return Om/Or - 1.0;
}

double dtc_clock_q0_numeric(const dtc_clock_parameters *p) {
  const double h = 1.0e-4;
  const double z_plus = exp(-h) - 1.0;
  const double z_minus = exp(h) - 1.0;
  const double lnE_plus = log(dtc_clock_E_obs(z_plus,p));
  const double lnE_minus = log(dtc_clock_E_obs(z_minus,p));
  const double dlnE_dln_a = (lnE_plus-lnE_minus)/(2.0*h);
  return -1.0 - dlnE_dln_a;
}

static double dtc_Hphys_of_a(double a, double H0_class, const dtc_clock_parameters *p) {
  if ((!isfinite(a)) || a <= 0.0) a = 1.0e-300;
  double z = 1.0/a - 1.0;
  return H0_class * dtc_clock_E_obs(z,p);
}

static double dtc_Hprime_tau_of_a(double a, double H0_class, const dtc_clock_parameters *p) {
  const double eps = 2.0e-5;
  const double ap = a * exp(eps);
  const double am = a * exp(-eps);
  const double Hp = dtc_Hphys_of_a(ap,H0_class,p);
  const double Hm = dtc_Hphys_of_a(am,H0_class,p);
  const double H = dtc_Hphys_of_a(a,H0_class,p);
  const double dH_dln_a = (Hp-Hm)/(2.0*eps);
  return a * H * dH_dln_a;
}

void dtc_clock_background_closure_at_a(
  double a,
  double H0_class,
  double K_class,
  double rho_standard_total,
  double p_standard_total,
  const dtc_clock_parameters *p,
  dtc_clock_background_closure *out) {

  out->used_fallback = 0;
  out->E_obs = 1.0;
  out->H_phys = 0.0;
  out->H_prime_tau = 0.0;
  out->rho_target = rho_standard_total;
  out->p_required_total = p_standard_total;
  out->rho_add = 0.0;
  out->p_add = 0.0;
  out->n = 0.0;

  if ((!isfinite(a)) || a <= 0.0 || (!isfinite(H0_class)) || H0_class <= 0.0) {
    out->used_fallback = 1;
    return;
  }

  const double z = 1.0/a - 1.0;
  const double E = dtc_clock_E_obs(z,p);
  const double H = H0_class * E;

  if (dtc_bad(E) || dtc_bad(H)) {
    out->used_fallback = 1;
    return;
  }

  const double Hp_tau = dtc_Hprime_tau_of_a(a,H0_class,p);
  const double rho_target = H*H + K_class/(a*a);

  if ((!isfinite(rho_target)) || rho_target <= 0.0) {
    out->used_fallback = 1;
    return;
  }

  double p_required_total = (K_class/a - Hp_tau)/(1.5*a) - rho_target;
  if (!isfinite(p_required_total)) {
    out->used_fallback = 1;
    return;
  }

  out->E_obs = E;
  out->H_phys = H;
  out->H_prime_tau = Hp_tau;
  out->rho_target = rho_target;
  out->p_required_total = p_required_total;
  out->rho_add = rho_target - rho_standard_total;
  out->p_add = p_required_total - p_standard_total;
  out->n = dtc_clock_n_of_z(z,p);
}

void dtc_clock_constraint_variables(double z, double k_mpc, double psi,
                                    const dtc_clock_parameters *p,
                                    dtc_clock_perturbations *out) {
  (void)k_mpc;
  const double n = dtc_clock_n_of_z(z,p);
  out->delta_X = 0.0;
  out->delta_chi = 0.0;
  out->delta_chi_prime = 0.0;
  out->delta_lambda = 0.0;
  out->delta_sigma = 0.0;
  if (fabs(n) > 1.0e-6) {
    out->delta_Theta_over_Theta = psi/n;
    out->tip_constraint_residual = -psi + n*out->delta_Theta_over_Theta;
  } else {
    out->delta_Theta_over_Theta = 0.0;
    out->tip_constraint_residual = 0.0;
  }
  out->current_constraint_residual = 0.0;
  out->mu = 1.0;
  out->gamma_slip = 1.0;
  out->Sigma = 1.0;
}

#ifdef DTC_CLOCK_STANDALONE
int main(void) {
  dtc_clock_parameters p;
  dtc_clock_perturbations q;
  dtc_clock_default_parameters(&p);
  printf("z_eq %.10g\n",dtc_clock_z_eq(&p));
  printf("q0 %.10g\n",dtc_clock_q0_numeric(&p));
  printf("n(zstar) %.10e\n",dtc_clock_n_of_z(p.z_star,&p));
  printf("n(BBN) %.10e\n",dtc_clock_n_of_z(1.0e9,&p));
  dtc_clock_constraint_variables(p.z_star,0.01,1.0e-5,&p,&q);
  printf("delta_X %.4g delta_lambda %.4g delta_sigma %.4g residual %.4g\n",
         q.delta_X,q.delta_lambda,q.delta_sigma,q.tip_constraint_residual);
  return 0;
}
#endif
