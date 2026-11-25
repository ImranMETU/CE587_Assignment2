# CE587 Homework 2 — Structural Optimization

**Imran Shahriar · 2735835 · 25 November 2026**

The submission contains three main files.

| File | Contents |
| --- | --- |
| [CE587_HW2_Final.pdf](https://github.com/ImranMETU/CE587_Assignment2/blob/main/CE587_HW2_Final.pdf) | Report addressing parts (a)–(h), including worked derivatives, contours and convergence comparisons |
| [CE587_HW2_Validation.xlsx](https://github.com/ImranMETU/CE587_Assignment2/blob/main/CE587_HW2_Validation.xlsx) | Formula-based calculations. Open **Direct comparison** for the numerical results, **Inputs** for the parameters, and **Numerical derivation** for the first step |
| [solve_hw2.py](https://github.com/ImranMETU/CE587_Assignment2/blob/main/solve_hw2.py) | Python solver for the two-bar truss, iteration data and report figures |

The archive groups the handout, calculation data, LaTeX source, plots, workbook builder, tests and verifier in **Supporting_files**. The three main files open or run directly. To rebuild from an extracted archive, copy the **contents** of Supporting_files into the folder containing the three main files, preserving the report and figures subfolders. The repository already uses this working layout.

## Reproduce the calculations

1. Run `python solve_hw2.py` with NumPy and Matplotlib installed. This writes `python_iterations.csv` and the six vector plots.
2. In Excel, compare the direct runs with the Python reference values on **Direct comparison**. **Analytical derivation** provides the closed-form equilibrium. **Results** summarizes the stabilized runs in Appendix A. The saved direct runs illustrate how rounding affects the terminal gradient and iteration count.
3. Run `python verify_workbook.py --check-only` with openpyxl installed to check the first-step derivation and the eleven saved stabilized traces. Omit the flag to regenerate `excel_python_check.csv`.
4. Run `python -m unittest -v test_hw2` with all three Python dependencies installed for the regression and integration checks.
5. Run `pdflatex CE587_HW2_Final.tex` twice to rebuild the report.
6. To regenerate the workbook, run the solver first, then `node build_workbook.mjs <absolute-path-to-artifact_tool.mjs>` using the bundled artifact-tool runtime.

[Project repository](https://github.com/ImranMETU/CE587_Assignment2)
