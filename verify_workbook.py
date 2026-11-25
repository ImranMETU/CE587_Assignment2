"""Cross-check two implementations of the stabilized arithmetic."""
import csv
import sys
from collections import defaultdict
from pathlib import Path

from openpyxl import load_workbook
from solve_hw2 import CASES, analytical_derivation, numerical_derivation

root = Path(__file__).resolve().parent
workbook = load_workbook(root / "CE587_HW2_Validation.xlsx", data_only=True, read_only=True)
analytical = analytical_derivation()
sheet = workbook["Analytical derivation"]
for address, key, tolerance in [
    ("C4", "bar_length_m", 1e-10),
    ("C5", "axial_rigidity_N", 1e-6),
    ("C12", "x1_m", 1e-10),
    ("C13", "x2_m", 1e-10),
    ("C18", "determinant_N2_per_m2", 1e-3),
    ("C24", "minimum_J", 1e-8),
]:
    assert abs(sheet[address].value - analytical[key]) <= tolerance, address
assert sheet["C19"].value == analytical["positive_definite"]
worked = numerical_derivation()
numerical = workbook["Numerical derivation"]
for address, expected, tolerance in [
    ("C13", worked["gradient"][0], 1e-7),
    ("C14", worked["gradient"][1], 1e-7),
    ("C15", worked["hessian"][0], 1e-3),
    ("C16", worked["hessian"][1], 1e-2),
    ("C34", worked["SD final midpoint alpha"], 1e-12),
    ("C41", worked["Newton alpha"], 1e-12),
    ("C42", worked["Newton updated point"][0], 1e-8),
    ("C43", worked["Newton updated point"][1], 1e-8),
    ("C50", worked["Marquardt trial point"][0], 1e-8),
    ("C51", worked["Marquardt trial point"][1], 1e-8),
    ("C54", 500., 0.),
    ("C57", worked["hessian_determinant"], 1e-2),
    ("C59", worked["Newton directional derivative"], 1e-8),
]:
    assert abs(numerical[address].value-expected) <= tolerance, address
assert numerical["C58"].value is True
assert numerical["C60"].value is True
assert numerical["C61"].value == "Proceed"
traces = defaultdict(list)
with (root / "python_iterations.csv").open(newline="") as stream:
    for entry in csv.DictReader(stream):
        traces[entry["case"]].append(entry)

results = []
for case in CASES:
    name = case.name
    expected = traces[name]
    observed = [
        row for row in workbook[name].iter_rows(min_row=2, max_col=9, values_only=True)
        if isinstance(row[0], (int, float))
    ]
    assert len(observed) == len(expected), name
    largest_position_error = largest_energy_error = largest_gradient_error = 0.
    for row, reference in zip(observed, expected):
        k, x, y, energy, gradient, damping, alpha, status, evaluations = row
        assert (k, status, evaluations) == (
            int(reference["k"]), reference["status"], int(reference["evaluations"])
        ), (name, k)
        position_error = max(abs(x-float(reference["x"])), abs(y-float(reference["y"])))
        energy_error = abs(energy-float(reference["energy"]))
        gradient_error = abs(gradient-float(reference["gradient"]))
        largest_position_error = max(largest_position_error, position_error)
        largest_energy_error = max(largest_energy_error, energy_error)
        largest_gradient_error = max(largest_gradient_error, gradient_error)
        # Long SD paths can amplify last-bit differences in interval-halving branch
        # decisions. These tolerances cover the measured drift while preserving
        # exact checks on row counts, statuses, evaluations, alpha, and damping.
        assert position_error < 4e-8 and energy_error < 1.3e-4 and gradient_error < 6e-3, (name,k)
        assert abs(alpha-float(reference["alpha"])) < 1e-10, (name,k)
        assert damping == float(reference["damping"]), (name,k)
    results.append([name,len(observed),largest_position_error,largest_energy_error,
                    largest_gradient_error])

if "--check-only" not in sys.argv:
    with (root / "excel_python_check.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["case","matched_rows","max_coordinate_difference_m",
                         "max_energy_difference_J","max_gradient_norm_difference_N"])
        writer.writerows(results)
for result in results:
    print(*result)
