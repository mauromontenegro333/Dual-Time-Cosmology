#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
p = ROOT / 'source/background.c'
if not p.exists():
    raise SystemExit(f'Missing {p}')
s = p.read_text()
start = s.find('/* DTC_GEOMETRIC_BACKGROUND_BRIDGE_V04_BEGIN')
end = s.find('/* DTC_GEOMETRIC_BACKGROUND_BRIDGE_V04_END */', start)
if start < 0 or end < 0:
    if 'DTC_GEOMETRIC_BACKGROUND_BRIDGE_V04B_BEGIN' in s:
        print('Already has v0.4b hotfix.')
        raise SystemExit(0)
    raise SystemExit('Could not find v0.4 bridge block in source/background.c. Restore/reinstall instead.')
endline = s.find('\n', end)
block = '''
  /* DTC_GEOMETRIC_BACKGROUND_BRIDGE_V04B_BEGIN
     DTC v0.4b geometric background closure with radiation-era IC guard. */
  if (pba->has_dtc_clock == _TRUE_) {
    dtc_clock_background_closure dtc_bg;

    dtc_clock_background_closure_at_a(
      a,
      pba->H0,
      pba->K,
      rho_tot,
      p_tot,
      &(pba->dtc_clock),
      &dtc_bg);

    if (dtc_bg.used_fallback == 0) {
      const double dtc_n_abs = fabs(dtc_bg.n);
      const double dtc_n_gate = dtc_n_abs / (dtc_n_abs + 1.0e-6);
      rho_tot += dtc_n_gate * dtc_bg.rho_add;
      p_tot += dtc_n_gate * dtc_bg.p_add;
    }
  }
  /* DTC_GEOMETRIC_BACKGROUND_BRIDGE_V04B_END */

'''
p.write_text(s[:start] + block + s[endline+1:])
print('Patched source/background.c to v0.4b radiation-IC guard.')
