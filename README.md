
## Repository

Requested repository: https://github.com/ImranMETU/CE587_Assignment2

## Main deliverables

- [Final report PDF](CE587_HW2_Final.pdf)
- [Validation workbook](CE587_HW2_Validation.xlsx)
- [Python optimization code](solve_hw2.py)
- [Python and Excel verification script](verify_workbook.py)
- [Iteration results](python_iterations.csv)

# CE587 Homework 2

The report main results use direct objective evaluations and the final IHM
midpoint. It shows the unnormalized steepest-descent divergence and the
normalized direction comparison, with direct Newton and lecture-rule
Marquardt results. Stabilized results are retained as Appendix A and in the
Excel verification workbook.
The Excel **Numerical derivation** sheet shows the first direct update.
**Direct comparison** compares Python reference results with separate formula
runs for the three methods, normalized and extended steepest descent, and
Newton at the common gradient target. Excel rebuilds the path from the
starting point. Direct energy comparisons can round differently near
equilibrium. The baseline Marquardt factor is 2, following the class notes. Python's `numerical_derivation()`
returns the stencil values and worked steps for checking by hand.
`numerical_derivation.mjs` supplies this sheet in the workbook builder.

The PDF's part (c) gives the full analytical derivation from bar geometry to
stationarity, the Hessian test, and substitution into the potential energy.
The workbook's **Analytical derivation** sheet shows the same steps with
linked formulas and units. The Python function `analytical_derivation()`
returns the intermediate quantities, and `print_analytical_derivation()`
prints the equations and values before the numerical runs.
`analytical_derivation.mjs` supplies the derivation sheet when rebuilding
the workbook with `build_workbook.mjs`.

The report answers parts (a)–(h). The source handout is included as `CE587_HW2_Handout.pdf`.

- Open `CE587_HW2_Validation.xlsx` in Microsoft Excel. **Results** shows the stabilized formula outputs alongside the Python reference coordinates. **Inputs** contains the physical and numerical settings. Each run has its own formula trace.
- Run `python solve_hw2.py` with NumPy and Matplotlib installed to regenerate the Python trace and plots alongside the script. It creates the figures directory as needed.
- Run `python -m unittest -v test_hw2` to check the objective, derivative stencils, solver settings, baseline and extended behavior, clean-directory generation, and saved workbook agreement. The generation test needs Matplotlib and NumPy, and the workbook test needs openpyxl.
- Recalculate and save the workbook in Excel, then run `python verify_workbook.py` with openpyxl installed to compare every saved iterate with the Python trace.
- The CSV contains the literal runs, the normalized steepest-descent case, and the stabilized comparison runs. The verifier's row-by-row CSV covers the stabilized runs. The Direct comparison sheet shows the direct results and their differences.
- Run `pdflatex CE587_HW2_Final.tex` twice from this directory to rebuild the report. Keep the `report` and `figures` directories and METU logo alongside the main source.
- The optional workbook builder takes the bundled artifact-tool module path as its argument. Run the Python solver first to populate the reference CSV, then run `node build_workbook.mjs <absolute-artifact_tool.mjs-path>` and recalculate in Excel.
