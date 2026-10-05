"""Run the full pipeline from raw data to tables, figures and workbook.

Usage (from the package root or the code directory):
    python code/run_all.py            # everything (~7 minutes; the adoption bootstrap takes ~5)
    python code/run_all.py --skip-adoption
"""
import subprocess
import sys
import time
from pathlib import Path

CODE = Path(__file__).resolve().parent
LOG = CODE.parent / "output" / "logs"
LOG.mkdir(parents=True, exist_ok=True)
STEPS = ["01_build_state_data.py", "02_build_utility_data.py", "03_build_lbnl_data.py",
         "10_main_sdid.py", "11_mechanisms_burden.py", "20_benchmarks_and_bounds.py",
         "21_utility_level.py", "22_compliance_cost_benchmark.py", "23_adoption_event_study.py",
         "30_figures.py", "40_check_against_manuscript.py", "31_results_workbook.py"]
if "--skip-adoption" in sys.argv:
    STEPS.remove("23_adoption_event_study.py")

for step in STEPS:
    t0 = time.time()
    with open(LOG / f"{step[:-3]}.log", "w") as fh:
        res = subprocess.run([sys.executable, step], cwd=CODE, stdout=fh, stderr=subprocess.STDOUT)
    status = "ok" if res.returncode == 0 else f"FAILED (see output/logs/{step[:-3]}.log)"
    print(f"{step:34s} {time.time() - t0:6.1f}s  {status}")
    if res.returncode:
        sys.exit(res.returncode)
