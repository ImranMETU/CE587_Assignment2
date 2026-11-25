"""Run the independent checks with python -m unittest test_hw2."""
import math
from importlib.util import find_spec
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from solve_hw2 import A, B, CASES, Q1, Q2, OPT, ROOT, derivatives, energy, solve


class HomeworkChecks(unittest.TestCase):
    def test_energy_and_closed_form(self):
        self.assertEqual(energy(0, 0), 0)
        self.assertAlmostEqual(energy(*OPT), -1098.13829172, places=7)

    def test_stencil_against_direct_objective(self):
        x, y = .1, .01
        dx, dy = .001, .0001
        gx, gy, hxx, hyy = derivatives(x, y)
        self.assertAlmostEqual(gx, (energy(x+dx,y)-energy(x-dx,y))/(2*dx), places=7)
        self.assertAlmostEqual(gy, (energy(x,y+dy)-energy(x,y-dy))/(2*dy), places=7)
        self.assertAlmostEqual(hxx, 2*A, places=6)
        self.assertAlmostEqual(hyy, 2*B, places=6)

    def test_zero_coordinate(self):
        for x, y in [(0., .01), (.1, 0.), (0., 0.)]:
            gx, gy, hxx, hyy = derivatives(x, y)
            self.assertAlmostEqual(gx, 2*A*x-Q1, places=7)
            self.assertAlmostEqual(gy, 2*B*y-Q2, places=7)
            self.assertAlmostEqual(hxx, 2*A, places=6)
            self.assertAlmostEqual(hyy, 2*B, places=6)

    def test_baseline_regression(self):
        for method, k, status in [("SD",0,"stalled"), ("Newton",1,"converged"),
                                  ("Marquardt",4,"converged")]:
            with self.subTest(method=method):
                rows = solve(method,1e-4,1000)
                self.assertEqual((rows[-1]["k"],rows[-1]["status"]),(k,status))
                if status == "converged":
                    self.assertLess(math.dist((rows[-1]["x"],rows[-1]["y"]),OPT),1e-9)

    def test_steepest_descent_cap_and_convergence(self):
        capped = solve("SD",1e-13,1000)
        extended = solve("SD",1e-13,1000,400)
        self.assertEqual(capped, extended[:200]+[dict(extended[200],status="cap",
                                                        alpha=0.,evaluations=4)])
        self.assertEqual((extended[-1]["k"],extended[-1]["status"]),(290,"converged"))
        self.assertLessEqual(extended[-1]["gradient"],1e-5)
        self.assertLess(math.dist((extended[-1]["x"],extended[-1]["y"]),OPT),1e-9)

    def test_sensitivity_settings(self):
        cases = {case.name: case for case in CASES}
        for relative in (.01, 1e-4):
            gx, gy, hxx, hyy = derivatives(.1, .01, relative)
            self.assertAlmostEqual(gx, .2*A-Q1, places=7)
            self.assertAlmostEqual(gy, .02*B-Q2, places=7)
            self.assertTrue(math.isclose(hxx, 2*A, rel_tol=1e-10))
            self.assertTrue(math.isclose(hyy, 2*B, rel_tol=1e-10))
        damped = cases["Marquardt factor 2"].run()
        self.assertEqual(damped[1]["damping"], 500.)
        loose = cases["SD loose gradient"].run()
        self.assertGreater(loose[-2]["gradient"], .01)
        self.assertLessEqual(loose[-1]["gradient"], .01)
        self.assertEqual(loose[-1]["status"], "converged")

    def test_newton_final_selection(self):
        endpoint = solve("Newton", 1e-4, 1000, selection="best")
        midpoint = solve("Newton", 1e-4, 1000, selection="midpoint")
        self.assertEqual(endpoint[0]["alpha"], 1.)
        self.assertEqual(midpoint[0]["alpha"], 1.-2**-15)
        self.assertGreater(midpoint[1]["gradient"], 1e-5)

    def test_literal_steepest_descent(self):
        cases = {case.name: case for case in CASES}
        baseline = cases["SD baseline"].run(comparison="raw", stencil="raw")
        self.assertEqual(baseline[-1]["status"], "stalled")
        extended = cases["SD extended"].run(comparison="raw", stencil="raw")
        self.assertEqual(extended[-1]["status"], "converged")
        self.assertLessEqual(extended[-1]["gradient"], 1e-5)

    def test_literal_midpoint_runs_and_divergence_status(self):
        sd = solve("SD", 1e-4, 1000, comparison="raw", selection="midpoint",
                   stencil="raw")
        self.assertEqual((sd[-1]["k"], sd[-1]["status"]), (103, "diverged"))
        self.assertFalse(math.isfinite(sd[-1]["gradient"]))
        normalized = solve("SD", 1e-4, 1000, comparison="raw",
                           selection="midpoint", stencil="raw", normalize_sd=True)
        self.assertEqual((normalized[-1]["k"], normalized[-1]["status"]),
                         (200, "cap"))
        self.assertAlmostEqual(normalized[-1]["gradient"], 18.5706469, places=5)
        newton = solve("Newton", 1e-4, 1000, comparison="raw",
                       selection="midpoint", stencil="raw", newton_step_test=True)
        self.assertEqual((newton[-1]["k"], newton[-1]["status"]),
                         (1, "converged_step"))
        self.assertLess(newton[-1]["gradient"], 1.)
        marquardt = solve("Marquardt", 1e-4, 1000, factor=2,
                          comparison="raw", selection="midpoint", stencil="raw")
        self.assertEqual((marquardt[-1]["k"], marquardt[-1]["status"]),
                         (8, "converged"))

    @unittest.skipUnless(find_spec("matplotlib"), "Matplotlib required")
    def test_generate_from_clean_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            project.mkdir()
            script = project / "solve_hw2.py"
            shutil.copyfile(ROOT / "solve_hw2.py", script)
            subprocess.run([sys.executable, str(script)], cwd=temporary,
                           check=True, capture_output=True, timeout=60)
            self.assertTrue((project / "python_iterations.csv").is_file())
            self.assertEqual({p.stem for p in (project / "figures").glob("*.pdf")},
                             {"baseline", "baseline_detail", "design_space", "detail", "graphical", "sensitivity"})

    @unittest.skipUnless(find_spec("openpyxl"), "openpyxl required")
    def test_saved_workbook_trace(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "verify_workbook.py"), "--check-only"],
            check=True, capture_output=True, text=True, timeout=90
        )
        self.assertEqual(len(result.stdout.splitlines()), len(CASES))


if __name__ == "__main__":
    unittest.main()
