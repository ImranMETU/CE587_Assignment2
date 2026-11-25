import fs from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import { addAnalyticalDerivation } from "./analytical_derivation.mjs";
import { addNumericalDerivation } from "./numerical_derivation.mjs";

const { Workbook, SpreadsheetFile } = await import(pathToFileURL(process.argv[2]).href);
const root = path.dirname(fileURLToPath(import.meta.url));
const book = Workbook.create();
const summary = book.worksheets.add("Results");
const inputs = book.worksheets.add("Inputs");
const cases = [
  ["SD baseline", "SD", 1e-4, 1000], ["Newton baseline", "Newton", 1e-4, 1000],
  ["Marquardt baseline", "Marquardt", 1e-4, 1000],
  ["SD tighter", "SD", 1e-13, 1000], ["Newton tighter", "Newton", 1e-13, 1000],
  ["Marquardt larger", "Marquardt", 1e-4, 100000],
  ["SD extended","SD",1e-13,1000,400],
  ["SD zero start","SD",1e-13,1000,400,0],
  ["Newton small stencil","Newton",1e-4,1000,200,.1,.01,1e-4],
  ["Marquardt factor 2","Marquardt",1e-4,1000,200,.1,.01,.01,2],
  ["SD loose gradient","SD",1e-13,1000,200,.1,.01,.01,10,.01],
];
const parameters = [
  ["E (Pa)",207e9], ["Area (m²)",1e-5], ["Span (m)",1.5], ["Height (m)",4],
  ["P (N)",1e4], ["Angle (deg)",30], ["Initial x1 (m)",.1], ["Initial x2 (m)",.01],
  ["Relative perturbation",.01], ["Gradient tolerance (N)",1e-5], ["Iteration cap",200],
  ["Damping factor",10], ["Bar length (m)"], ["a (N/m)"], ["b (N/m)"],
  ["q1 (N)"], ["q2 (N)"], ["Analytical x1 (m)"], ["Analytical x2 (m)"], ["Minimum (J)"],
];
inputs.getRange("A1").values = [["Source: CE587 Homework 2, Fall 2026–2027"]];
inputs.getRange("A3:B22").values = parameters.map(([label,value]) => [label,value ?? null]);
inputs.getRange("B15:B22").formulas = [
  "=SQRT((B5/2)^2+B6^2)","=B3*B4/B15*(B5/(2*B15))^2","=B3*B4/B15*(B6/B15)^2",
  "=B7*COS(RADIANS(B8))","=B7*SIN(RADIANS(B8))","=B18/(2*B16)","=B19/(2*B17)",
  "=-B16*B20^2-B17*B21^2",
].map(value=>[value]);
inputs.getRange("D3:M14").values = [
  ["Run","Method","Line width","Initial damping","Cap","x1 start","x2 start","Stencil factor","Damping factor","Gradient tolerance"],
  ...cases.map(([name,method,width,damping,cap,x,y,relative,factor,tolerance]) =>
    [name,method,width,damping,cap??null,x??null,y??null,relative??null,factor??null,tolerance??null]),
];
inputs.getRange("D16").values = [["Blank case overrides use the defaults in column B. Trace limit is 400 updates."]];
summary.getRange("A1").values = [["CE587 HW2 | Python–Excel verification"]];
summary.getRange("A3:K3").values = [[
  "Run","Iterations","Status","Excel x1 (m)","Excel x2 (m)","Energy (J)",
  "Gradient (N)","Evaluations","Python x1 (m)","Python x2 (m)","Distance (m)",
]];
const csv = (await fs.readFile(path.join(root,"python_iterations.csv"),"utf8")).trim().split(/\r?\n/);
const finals = new Map(csv.slice(1).map(line => {
  const [name,k,x,y] = line.split(",");
  return [name,[Number(x),Number(y)]];
}));
const column = n => n <= 26 ? String.fromCharCode(64+n) : column(Math.floor((n-1)/26)) + column((n-1)%26+1);
const a = "Inputs!$B$16", b = "Inputs!$B$17", q1 = "Inputs!$B$18", q2 = "Inputs!$B$19";
function heading(sheet,address) {
  const style = sheet.getRange(address).format;
  style.fill = "#19334D";
  style.font.color = "#FFFFFF";
  style.font.bold = true;
}
function widths(sheet,address,width) {
  sheet.getRange(address).format.columnWidth = width;
}
for (const [index,[name,method]] of cases.entries()) {
  const sheet = book.worksheets.add(name);
  const inputRow = index + 4;
  const lastRow = 402;
  const setting = (col,base) => `IF(ISNUMBER(Inputs!$${col}$${inputRow}),Inputs!$${col}$${inputRow},Inputs!$B$${base})`;
  const cap = `MIN(400,${setting("H",13)})`;
  const tolerance = setting("M",12);
  const search = method !== "Marquardt";
  const headers = [
    "k","x1 (m)","x2 (m)","Energy (J)","Gradient (N)","Damping","Alpha","Status",
    "Evaluations","Delta 1","Delta 2","Energy +1","Energy −1","Energy +2","Energy −2",
    "Gradient 1","Gradient 2","Hessian 11","Hessian 22","Direction 1","Direction 2",
    "Line linear","Line quadratic","Line center","Halvings",
  ];
  if (search) {
    headers.push(...Array.from({length:45},(_,i)=>`Midpoint ${i}`));
  }
  sheet.getRange(`A1:${column(headers.length)}1`).values = [headers];
  const rows = [];
  for (let r=2;r<=lastRow;r++) {
    const prior=r-1;
    const active = formula => `=IF(A${r}="","",${formula})`;
    const step = formula => active(`IF(OR(E${r}<=${tolerance},A${r}>=${cap}),0,${formula})`);
    const x=`B${r}`,y=`C${r}`,dx=`J${r}`,dy=`K${r}`;
    const shift = search ? "" : `+F${r}`;
    const last = `INDEX(Z${r}:BR${r},1,Y${r}+1)`;
    const quarter = `2^(-Y${r}-1)`;
    const center = `X${r}`;
    const alpha = search
      ? `IF(${center}<=${last}-${quarter}/2,${last}-${quarter},IF(${center}>=${last}+${quarter}/2,${last}+${quarter},${last}))`
      : `IF(V${r}+W${r}<0,1,0)`;
    const data = [
      r===2?"=0":`=IF(H${prior}="running",A${prior}+1,"")`,
      active(r===2?setting("I",9):`B${prior}+G${prior}*T${prior}`),
      active(r===2?setting("J",10):`C${prior}+G${prior}*U${prior}`),
      active(`${a}*${x}^2+${b}*${y}^2-${q1}*${x}-${q2}*${y}`),
      active(`SQRT(P${r}^2+Q${r}^2)`),
      active(r===2 || search ? `Inputs!$G$${inputRow}` :
        `IF(G${prior}=1,F${prior}/${setting("L",14)},F${prior}*${setting("L",14)})`),
      step(alpha),
      active(`IF(E${r}<=${tolerance},"converged",IF(A${r}>=${cap},"cap",${search?`IF(G${r}=0,"stalled","running")`:'"running"'}))`),
      active(`${method==="SD"?4:9}+IF(OR(H${r}="cap",H${r}="converged"),0,${search?`3*Y${r}+3`:1})`),
      active(`${setting("K",11)}*IF(${x}=0,1,${x})`),
      active(`${setting("K",11)}*IF(${y}=0,1,${y})`),
      active(`${dx}*(2*${a}*${x}-${q1}+${a}*${dx})`),
      active(`-${dx}*(2*${a}*${x}-${q1}-${a}*${dx})`),
      active(`${dy}*(2*${b}*${y}-${q2}+${b}*${dy})`),
      active(`-${dy}*(2*${b}*${y}-${q2}-${b}*${dy})`),
      active(`(L${r}-M${r})/(2*${dx})`), active(`(N${r}-O${r})/(2*${dy})`),
      active(`(L${r}+M${r})/${dx}^2`), active(`(N${r}+O${r})/${dy}^2`),
      step(method==="SD"?`-P${r}`:`-P${r}/(R${r}${shift})`),
      step(method==="SD"?`-Q${r}`:`-Q${r}/(S${r}${shift})`),
      step(`P${r}*T${r}+Q${r}*U${r}`),
      step(`${a}*T${r}^2+${b}*U${r}^2`),
      step(search?`-V${r}/(2*W${r})`:"0"),
      step(search?`INT(-LOG(Inputs!$F$${inputRow},2))+1`:"0"),
    ];
    if (search) {
      data.push(step("0.5"));
      for(let i=1;i<=44;i++) {
        const midpoint = `${column(25+i)}${r}`;
        const quarterWidth = `2^(-${i+1})`;
        data.push(step(`IF(${i}>Y${r},${midpoint},IF(${center}<${midpoint}-${quarterWidth}/2,${midpoint}-${quarterWidth},IF(${center}>${midpoint}+${quarterWidth}/2,${midpoint}+${quarterWidth},${midpoint})))`));
      }
    }
    rows.push(data);
  }
  sheet.getRange(`A2:${column(headers.length)}${lastRow}`).formulas = rows;
  heading(sheet,`A1:${column(headers.length)}1`);
  widths(sheet,"A:A",6);
  widths(sheet,`B:${column(headers.length)}`,16);
  sheet.getRange("B2:C202").setNumberFormat("0.000000000");
  sheet.getRange("D2:D202").setNumberFormat("0.000000");
  sheet.getRange("E2:G202").setNumberFormat("0.000E+00");
  const s=index+4;
  const ref=`'${name}'!`;
  const lookup = col => `INDEX(${ref}${col}2:${col}${lastRow},B${s}+1)`;
  summary.getRange(`A${s}`).values = [[name]];
  summary.getRange(`B${s}:H${s}`).formulas = [[
    `=COUNT(${ref}A2:A${lastRow})-1`, ...["H","B","C","D","E"].map(col=>`=${lookup(col)}`),
    `=SUM(${ref}I2:I${lastRow})`,
  ]];
  summary.getRange(`I${s}:J${s}`).values = [finals.get(name)];
  summary.getRange(`K${s}`).formulas = [[`=SQRT((D${s}-I${s})^2+(E${s}-J${s})^2)`]];
}
summary.getRange("A16:D16").values = [["Analytical minimum","x1 (m)","x2 (m)","Energy (J)"]];
summary.getRange("B17:D17").formulas = [["=Inputs!B20","=Inputs!B21","=Inputs!B22"]];
for (const area of ["A1:K1","A3:K3","A16:D16"]) heading(summary,area);
heading(inputs,"A1:M1");
heading(inputs,"D3:M3");
widths(inputs,"A:A",27);
widths(inputs,"B:M",21);
widths(summary,"A:A",24);
widths(summary,"B:K",17);
summary.getRange("D4:E14").setNumberFormat("0.000000000");
summary.getRange("F4:F14").setNumberFormat("0.000000");
summary.getRange("I4:J14").setNumberFormat("0.000000000");
summary.getRange("G4:G14").setNumberFormat("0.000E+00");
summary.getRange("K4:K14").setNumberFormat("0.000E+00");
addAnalyticalDerivation(book);
addNumericalDerivation(book);
book.recalculate();
const output = await SpreadsheetFile.exportXlsx(book);
await output.save(path.join(root,"CE587_HW2_Validation.xlsx"));
