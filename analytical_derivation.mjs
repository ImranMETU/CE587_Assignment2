// The analytical solution follows the handwritten calculation for part (c).
export function addAnalyticalDerivation(book) {
  const sheet = book.worksheets.add("Analytical derivation");
  sheet.showGridLines = false;
  sheet.getRange("A1").values = [["Analytical minimum — part (c)"]];
  sheet.getRange("A3:D3").values = [["Quantity / step", "Equation", "Calculated value", "Unit"]];
  const rows = [
    ["Bar length, s", "sqrt((l/2)^2 + h^2)", "='Inputs'!B15", "m"],
    ["Axial rigidity, EA", "E * A", "='Inputs'!B3*'Inputs'!B4", "N"],
    ["Horizontal coefficient, a", "(EA/s) * (l/(2s))^2", "='Inputs'!B16", "N/m"],
    ["Vertical coefficient, b", "(EA/s) * (h/s)^2", "='Inputs'!B17", "N/m"],
    ["Horizontal load, q1", "P * cos(theta)", "='Inputs'!B18", "N"],
    ["Vertical load, q2", "P * sin(theta)", "='Inputs'!B19", "N"],
    ["First derivative in x1", "df/dx1 = (2a)*x1 - q1", "=2*C6", "N/m for 2a"],
    ["First derivative in x2", "df/dx2 = (2b)*x2 - q2", "=2*C7", "N/m for 2b"],
    ["Stationarity in x1", "Set df/dx1 = 0, then x1* = q1/(2a)", "=C8/C10", "m"],
    ["Stationarity in x2", "Set df/dx2 = 0, then x2* = q2/(2b)", "=C9/C11", "m"],
    ["Hessian H11", "d2f/dx1^2 = 2a", "=C10", "N/m"],
    ["Hessian H12 = H21", "d2f/(dx1 dx2) = 0", "=0", "N/m"],
    ["Hessian H22", "d2f/dx2^2 = 2b", "=C11", "N/m"],
    ["First principal minor", "H11 > 0", "=C14", "N/m"],
    ["Second principal minor", "det(H) = H11*H22 - H12^2 > 0", "=C14*C16-C15^2", "(N/m)^2"],
    ["Positive definite", "Both leading principal minors are positive", "=AND(C17>0,C18>0)", ""],
    ["Horizontal strain energy", "a*(x1*)^2", "=C6*C12^2", "J"],
    ["Vertical strain energy", "b*(x2*)^2", "=C7*C13^2", "J"],
    ["Horizontal load work", "q1*x1*", "=C8*C12", "J"],
    ["Vertical load work", "q2*x2*", "=C9*C13", "J"],
    ["Minimum potential energy", "f* = a*x1*^2 + b*x2*^2 - q1*x1* - q2*x2*", "=C20+C21-C22-C23", "J"],
    ["Gradient residual in x1", "2a*x1* - q1", "=C10*C12-C8", "N"],
    ["Gradient residual in x2", "2b*x2* - q2", "=C11*C13-C9", "N"],
    ["Horizontal displacement", "1000*x1*", "=1000*C12", "mm"],
    ["Vertical displacement", "1000*x2*", "=1000*C13", "mm"],
  ];
  sheet.getRange("A4:D28").values = rows.map(([label,equation,,unit]) =>
    [label,equation,null,unit]);
  sheet.getRange("C4:C28").formulas = rows.map(row => [row[2]]);
  sheet.getRange("A30").values = [["A positive-definite Hessian proves this stationary point is the unique global minimum."]];
  sheet.getRange("A31").values = [["Positive x1 is rightward. Positive x2 is downward."]];
  sheet.getRange("A1:D31").format.font = { name: "Calibri", size: 11 };
  sheet.getRange("A3:D3").format.fill = "#19334D";
  sheet.getRange("A3:D3").format.font.color = "#FFFFFF";
  sheet.getRange("A3:D3").format.font.bold = true;
  sheet.getRange("A:A").format.columnWidth = 31;
  sheet.getRange("B:B").format.columnWidth = 59;
  sheet.getRange("C:C").format.columnWidth = 24;
  sheet.getRange("D:D").format.columnWidth = 17;
  sheet.getRange("A3:D28").format.rowHeight = 25;
  sheet.getRange("C4:C28").setNumberFormat("0.0000000000");
  sheet.getRange("C18").setNumberFormat("0.000000E+00");
  sheet.getRange("C19").setNumberFormat("General");
  sheet.getRange("C25:C26").setNumberFormat("0.000E+00");
  for (const address of ["A12:D13","A24:D24"]) {
    sheet.getRange(address).format.fill = "#E7EEF5";
    sheet.getRange(address).format.font.bold = true;
  }
}
