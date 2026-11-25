// Direct central differences and first updates for manual checking.
export function addNumericalDerivation(book) {
  const sheet = book.worksheets.add("Numerical derivation");
  sheet.showGridLines = false;
  sheet.getRange("A1").values = [["First numerical update — parts (d)–(f)"]];
  sheet.getRange("A3:D3").values = [["Quantity", "Equation / procedure", "Calculated value", "Unit"]];
  const f = (x,y) => "'Inputs'!$B$16*("+x+")^2+'Inputs'!$B$17*("+y+")^2-'Inputs'!$B$18*("+x+")-'Inputs'!$B$19*("+y+")";
  function row(r, label, equation, formula, unit) {
    sheet.getRange("A"+r+":D"+r).values = [[label,equation,null,unit]];
    sheet.getRange("C"+r).formulas = [["="+formula]];
  }
  row(4,"Starting x1","Initial horizontal displacement","'Inputs'!B9","m");
  row(5,"Starting x2","Initial vertical displacement","'Inputs'!B10","m");
  row(6,"delta 1","0.01*x1","'Inputs'!B11*C4","m");
  row(7,"delta 2","0.01*x2","'Inputs'!B11*C5","m");
  row(8,"Starting energy","f(x1,x2)",f("C4","C5"),"J");
  row(9,"Energy +1","f(x1+delta1,x2)",f("C4+C6","C5"),"J");
  row(10,"Energy -1","f(x1-delta1,x2)",f("C4-C6","C5"),"J");
  row(11,"Energy +2","f(x1,x2+delta2)",f("C4","C5+C7"),"J");
  row(12,"Energy -2","f(x1,x2-delta2)",f("C4","C5-C7"),"J");
  row(13,"Gradient g1","(f(+1)-f(-1))/(2*delta1)","(C9-C10)/(2*C6)","N");
  row(14,"Gradient g2","(f(+2)-f(-2))/(2*delta2)","(C11-C12)/(2*C7)","N");
  row(15,"Hessian H11","(f(+1)-2*f0+f(-1))/delta1^2","(C9-2*C8+C10)/C6^2","N/m");
  row(16,"Hessian H22","(f(+2)-2*f0+f(-2))/delta2^2","(C11-2*C8+C12)/C7^2","N/m");
  row(17,"Energy ++","f(x1+delta1,x2+delta2)",f("C4+C6","C5+C7"),"J");
  row(18,"Energy +-","f(x1+delta1,x2-delta2)",f("C4+C6","C5-C7"),"J");
  row(19,"Energy -+","f(x1-delta1,x2+delta2)",f("C4-C6","C5+C7"),"J");
  row(20,"Energy --","f(x1-delta1,x2-delta2)",f("C4-C6","C5-C7"),"J");
  row(21,"Hessian H12 check","(f(++)-f(+-)-f(-+)+f(--))/(4*delta1*delta2)","(C17-C18-C19+C20)/(4*C6*C7)","N/m");
  row(22,"Gradient norm","sqrt(g1^2+g2^2)","SQRT(C13^2+C14^2)","N");
  sheet.getRange("A24").values = [["Steepest descent"]];
  row(25,"Direction p1","-g1","-C13","");
  row(26,"Direction p2","-g2","-C14","");
  row(27,"Line-search width","Baseline interval stopping width","'Inputs'!F4","");
  row(28,"Number of halvings","Smallest n with 2^(-n) < width","INT(-LOG(C27,2))+1","");
  row(29,"Final midpoint alpha","2^(-n-1)","2^(-C28-1)","");
  row(30,"Final upper alpha","2^(-n)","2^(-C28)","");
  row(31,"Energy at alpha=0","Starting energy","C8","J");
  row(32,"Energy at midpoint","f(x0+alpha_mid*p)",f("C4+C29*C25","C5+C29*C26"),"J");
  row(33,"Energy at upper","f(x0+alpha_upper*p)",f("C4+C30*C25","C5+C30*C26"),"J");
  row(34,"Selected alpha","Lowest energy among final candidates","IF(C31<=MIN(C32,C33),0,IF(C32<=C33,C29,C30))","");
  row(35,"Updated x1","x1+alpha*p1","C4+C34*C25","m");
  row(36,"Updated x2","x2+alpha*p2","C5+C34*C26","m");
  sheet.getRange("A38").values = [["Newton"]];
  row(39,"Direction p1","-g1/H11","-C13/C15","m");
  row(40,"Direction p2","-g2/H22","-C14/C16","m");
  row(41,"Selected alpha","Baseline interval-search result","'Newton baseline'!G2","");
  row(42,"Updated x1","x1+alpha*p1","C4+C41*C39","m");
  row(43,"Updated x2","x2+alpha*p2","C5+C41*C40","m");
  row(44,"Updated energy","f(updated x1,updated x2)",f("C42","C43"),"J");
  sheet.getRange("A46").values = [["Marquardt"]];
  row(47,"Initial lambda","Damping prescribed in the handout","'Inputs'!G6","N/m");
  row(48,"Direction p1","-g1/(H11+lambda)","-C13/(C15+C47)","m");
  row(49,"Direction p2","-g2/(H22+lambda)","-C14/(C16+C47)","m");
  row(50,"Trial x1","x1+p1","C4+C48","m");
  row(51,"Trial x2","x2+p2","C5+C49","m");
  row(52,"Trial energy","f(trial x1,trial x2)",f("C50","C51"),"J");
  row(53,"Accepted","Trial energy is lower than starting energy","C52<C8","");
  row(54,"Next lambda","Divide after acceptance, multiply after rejection","IF(C53,C47/'Inputs'!B14,C47*'Inputs'!B14)","N/m");
  sheet.getRange("A56").values = [["H12 is exactly zero for this objective. Newton and Marquardt use the diagonal Hessian."]];
  sheet.getRange("A57").values = [["Direct differences here may differ slightly from stabilized arithmetic in the iteration sheets."]];
  sheet.getRange("A58").values = [["The interval shown is the baseline SD result. Full searches and later updates are in the method sheets."]];
  sheet.getRange("A59").values = [["The gradient-norm stopping test and factor-of-ten damping update are adopted conventions."]];
  sheet.getRange("A1:D59").format.font = {name:"Calibri",size:11};
  sheet.getRange("A:A").format.columnWidth=31;
  sheet.getRange("B:B").format.columnWidth=70;
  sheet.getRange("C:C").format.columnWidth=24;
  sheet.getRange("D:D").format.columnWidth=14;
  sheet.getRange("A3:D54").format.rowHeight=24;
  sheet.getRange("C4:C54").setNumberFormat("0.0000000000");
  sheet.getRange("C21").setNumberFormat("0.000E+00");
  sheet.getRange("C53").setNumberFormat("General");
  sheet.getRange("C28").setNumberFormat("0");
  for (const address of ["A3:D3","A24:D24","A38:D38","A46:D46"]) {
    sheet.getRange(address).format.fill="#19334D";
    sheet.getRange(address).format.font.color="#FFFFFF";
    sheet.getRange(address).format.font.bold=true;
  }
}
