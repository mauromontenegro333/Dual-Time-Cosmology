#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
HERE = Path(__file__).resolve().parents[1]

def read(path): return path.read_text()
def write(path, text): path.write_text(text)

def backup(path):
    b = path.with_suffix(path.suffix + ".dtc_v04_backup")
    if not b.exists():
        shutil.copy2(path,b)
        print(f"[backup] {b}")

def require(path):
    if not path.exists():
        raise SystemExit(f"Missing: {path}")

def insert_after_once(s, marker, insertion):
    if insertion.strip() in s:
        return s
    i = s.find(marker)
    if i < 0:
        raise SystemExit(f"Could not find marker: {marker}")
    j = s.find("\n",i)
    return s[:j+1] + insertion + s[j+1:]

def copy_core():
    for rel in ["include/dtc_clock.h","source/dtc_clock.c"]:
        src = HERE/rel
        dst = ROOT/rel
        shutil.copy2(src,dst)
        print(f"[copy] {rel}")

def patch_background_h():
    p = ROOT/"include/background.h"
    require(p); backup(p)
    s = read(p)
    if '#include "dtc_clock.h"' not in s:
        s = insert_after_once(s, '#include "common.h"', '#include "dtc_clock.h"\n')
    if "dtc_clock_parameters dtc_clock;" not in s:
        marker = "double Omega0_de;"
        i = s.find(marker)
        if i < 0:
            marker = "double Omega0_m;"
            i = s.find(marker)
        if i < 0:
            raise SystemExit("Could not find Omega marker in background.h")
        j = s.find("\n",i)
        block = r'''
  /** Dual Time Cosmology native clock bridge. */
  short has_dtc_clock;
  dtc_clock_parameters dtc_clock;
'''
        s = s[:j+1] + block + s[j+1:]
    write(p,s)
    print("[patch] include/background.h")

def patch_input_c():
    p = ROOT/"source/input.c"
    require(p); backup(p)
    s = read(p)
    if '#include "dtc_clock.c"' not in s:
        s = insert_after_once(s, '#include "input.h"', '#include "dtc_clock.c"\n')

    if "dtc_clock_default_parameters(&(pba->dtc_clock));" not in s:
        idx = s.find('parser_read_double(pfc,"Omega_Lambda"')
        if idx < 0:
            raise SystemExit("Could not find Omega_Lambda parser location")
        block = r'''
  /* DTC native clock input. Use integer flag has_dtc_clock=0/1. */
  pba->has_dtc_clock = _FALSE_;
  dtc_clock_default_parameters(&(pba->dtc_clock));

  int dtc_has_clock_int = 0;
  class_call(parser_read_int(pfc,"has_dtc_clock",&dtc_has_clock_int,&flag1,errmsg),
             errmsg, errmsg);
  if (flag1 == _TRUE_) {
    pba->has_dtc_clock = (dtc_has_clock_int != 0) ? _TRUE_ : _FALSE_;
  }

  class_call(parser_read_double(pfc,"dtc_Omega_m",&(pba->dtc_clock.Omega_m),&flag1,errmsg), errmsg, errmsg);
  class_call(parser_read_double(pfc,"dtc_Omega_r",&(pba->dtc_clock.Omega_r),&flag1,errmsg), errmsg, errmsg);
  class_call(parser_read_double(pfc,"dtc_n0",&(pba->dtc_clock.n0),&flag1,errmsg), errmsg, errmsg);
  class_call(parser_read_double(pfc,"dtc_zt",&(pba->dtc_clock.zt),&flag1,errmsg), errmsg, errmsg);
  class_call(parser_read_double(pfc,"dtc_beta",&(pba->dtc_clock.beta),&flag1,errmsg), errmsg, errmsg);
  class_call(parser_read_double(pfc,"dtc_n_shelf",&(pba->dtc_clock.n_shelf),&flag1,errmsg), errmsg, errmsg);
  class_call(parser_read_double(pfc,"dtc_z_on",&(pba->dtc_clock.z_on),&flag1,errmsg), errmsg, errmsg);
  class_call(parser_read_double(pfc,"dtc_z_off",&(pba->dtc_clock.z_off),&flag1,errmsg), errmsg, errmsg);
  class_call(parser_read_double(pfc,"dtc_alpha",&(pba->dtc_clock.alpha),&flag1,errmsg), errmsg, errmsg);
  class_call(parser_read_double(pfc,"dtc_gamma",&(pba->dtc_clock.gamma),&flag1,errmsg), errmsg, errmsg);
  class_call(parser_read_double(pfc,"dtc_M_chi_over_H0",&(pba->dtc_clock.M_chi_over_H0),&flag1,errmsg), errmsg, errmsg);
  class_call(parser_read_double(pfc,"dtc_Z_chi",&(pba->dtc_clock.Z_chi),&flag1,errmsg), errmsg, errmsg);
  class_call(parser_read_double(pfc,"dtc_C_X",&(pba->dtc_clock.C_X),&flag1,errmsg), errmsg, errmsg);

'''
        s = s[:idx] + block + s[idx:]
    else:
        # Add v0.4 Omega parsers if older DTC parser exists.
        if 'dtc_Omega_m' not in s:
            anchor = 'dtc_clock_default_parameters(&(pba->dtc_clock));'
            i = s.find(anchor)
            j = s.find("\n", i)
            add = r'''
  class_call(parser_read_double(pfc,"dtc_Omega_m",&(pba->dtc_clock.Omega_m),&flag1,errmsg), errmsg, errmsg);
  class_call(parser_read_double(pfc,"dtc_Omega_r",&(pba->dtc_clock.Omega_r),&flag1,errmsg), errmsg, errmsg);
'''
            s = s[:j+1] + add + s[j+1:]
    write(p,s)
    print("[patch] source/input.c")

def patch_background_c():
    p = ROOT/"source/background.c"
    require(p); backup(p)
    s = read(p)
    if '#include "dtc_clock.h"' not in s:
        s = insert_after_once(s, '#include "background.h"', '#include "dtc_clock.h"\n')

    if "DTC_GEOMETRIC_BACKGROUND_BRIDGE_V04B_BEGIN" not in s:
        # Remove older v0.3/v0.4 blocks if present.
        for bmarker, emarker in [
            ("/* DTC_GEOMETRIC_BACKGROUND_BRIDGE_BEGIN", "/* DTC_GEOMETRIC_BACKGROUND_BRIDGE_END */"),
            ("/* DTC_GEOMETRIC_BACKGROUND_BRIDGE_V04_BEGIN", "/* DTC_GEOMETRIC_BACKGROUND_BRIDGE_V04_END */"),
            ("/* DTC_GEOMETRIC_BACKGROUND_BRIDGE_V04B_BEGIN", "/* DTC_GEOMETRIC_BACKGROUND_BRIDGE_V04B_END */"),
        ]:
            while True:
                begin_old = s.find(bmarker)
                end_old = s.find(emarker, begin_old)
                if begin_old >= 0 and end_old >= 0:
                    end_old = s.find("\n", end_old)
                    s = s[:begin_old] + s[end_old+1:]
                else:
                    break

        markers = [
            "/** - compute expansion rate H from Friedmann equation",
            "/* - compute expansion rate H from Friedmann equation",
            "compute expansion rate H from Friedmann equation"
        ]
        idx = -1
        for m in markers:
            idx = s.find(m)
            if idx >= 0:
                break
        if idx < 0:
            raise SystemExit("Could not find Friedmann H computation comment in background.c")

        block = r'''
  /* DTC_GEOMETRIC_BACKGROUND_BRIDGE_V04B_BEGIN
     DTC v0.4b geometric background closure with radiation-era IC guard.

     The original v0.4 closure was applied even when n(z) was effectively zero.
     That adds a normalization closure at the ultra-early CLASS initial point,
     so CLASS sees Omega_r far from 1 and aborts in background_initial_conditions.

     v0.4b smoothly gates the closure by n(z). When n is tiny, rho_tot/p_tot
     remain the native CLASS radiation/matter values, so initial conditions are
     radiation dominated. Once the clock transition/shelf is active, the full
     DTC geometric closure is restored.
  */
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
        s = s[:idx] + block + s[idx:]
    write(p,s)
    print("[patch] source/background.c")

def main():
    copy_core()
    patch_background_h()
    patch_input_c()
    patch_background_c()
    print("\nInstalled DTC CLASS bridge v0.4b radiation-IC fix.")
    print("Now run: make clean && make -j4")

if __name__ == "__main__":
    main()
