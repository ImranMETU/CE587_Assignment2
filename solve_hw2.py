"""CE587 HW2. Run from any directory with NumPy and Matplotlib installed."""
import csv
import math
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
E, AREA, SPAN, HEIGHT, LOAD, ANGLE = 207e9, 1e-5, 1.5, 4.0, 1e4, 30
S = math.hypot(SPAN / 2, HEIGHT)
A = E * AREA / S * (SPAN / (2 * S)) ** 2
B = E * AREA / S * (HEIGHT / S) ** 2
Q1 = LOAD * math.cos(math.radians(ANGLE))
Q2 = LOAD * math.sin(math.radians(ANGLE))
OPT = Q1 / (2 * A), Q2 / (2 * B)


@dataclass(frozen=True)
class Case:
    name: str
    method: str
    width: float = 1e-4
    damping: float = 1000.
    cap: int = 200
    start: tuple[float, float] = (.1, .01)
    relative: float = .01
    factor: float = 2.
    tolerance: float = 1e-5

    def run(self, **options):
        if self.method == "Newton":
            options.setdefault("newton_step_test", True)
        return solve(self.method, self.width, self.damping, self.cap, self.start,
                     self.relative, self.factor, self.tolerance, **options)


CASES = [
    Case("SD baseline", "SD"),
    Case("Newton baseline", "Newton"),
    Case("Marquardt baseline", "Marquardt"),
    Case("SD tighter", "SD", width=1e-13),
    Case("Newton tighter", "Newton", width=1e-13),
    Case("Marquardt larger", "Marquardt", damping=100000),
    Case("SD extended", "SD", width=1e-13, cap=400),
    Case("SD zero start", "SD", width=1e-13, cap=400, start=(0., .01)),
    Case("Newton small stencil", "Newton", relative=1e-4),
    Case("Marquardt factor 10", "Marquardt", factor=10),
    Case("SD loose gradient", "SD", width=1e-13, tolerance=.01),
]


def energy(x, y):
    return A * x*x + B * y*y - Q1*x - Q2*y


def analytical_derivation():
    """Part (c), in the same order as the handwritten derivation.

    s = sqrt((l/2)^2 + h^2).
    a = (EA/s)(l/(2s))^2, b = (EA/s)(h/s)^2.
    f = a*x1^2 + b*x2^2 - q1*x1 - q2*x2.
    Stationarity gives 2*a*x1 - q1 = 0 and 2*b*x2 - q2 = 0.
    Thus x1 = q1/(2*a), x2 = q2/(2*b).
    H = diag(2*a, 2*b). Its leading principal minors are positive,
    establishing a unique global minimum of this quadratic.
    Substitution in the original objective gives the minimum energy.
    """
    x1, x2 = OPT
    h11, h22 = 2*A, 2*B
    return {
        "bar_length_m": S, "axial_rigidity_N": E*AREA,
        "a_N_per_m": A, "b_N_per_m": B, "q1_N": Q1, "q2_N": Q2,
        "h11_N_per_m": h11, "h22_N_per_m": h22,
        "h12_N_per_m": 0., "determinant_N2_per_m2": h11*h22,
        "positive_definite": h11 > 0 and h11*h22 > 0,
        "x1_m": x1, "x2_m": x2,
        "gradient1_N": h11*x1-Q1, "gradient2_N": h22*x2-Q2,
        "minimum_J": energy(x1,x2),
    }


def print_analytical_derivation():
    result = analytical_derivation()
    print("\nAnalytical calculation, part (c)")
    print(f"s = sqrt((l/2)^2+h^2) = {S:.10f} m")
    print(f"EA = {E*AREA:.0f} N")
    print(f"f = {A:.7f}*x1^2 + {B:.7f}*x2^2"
          f" - {Q1:.7f}*x1 - {Q2:.7f}*x2 (J)")
    print(f"df/dx1 = {2*A:.7f}*x1 - {Q1:.7f} = 0")
    print(f"df/dx2 = {2*B:.7f}*x2 - {Q2:.7f} = 0")
    print(f"x1 = q1/(2*a) = {OPT[0]:.10f} m")
    print(f"x2 = q2/(2*b) = {OPT[1]:.10f} m")
    print(f"H = diag({2*A:.7f}, {2*B:.7f}) N/m")
    print(f"det(H) = {result['determinant_N2_per_m2']:.7e} (N/m)^2 > 0")
    print(f"Positive definite: {result['positive_definite']}")
    print(f"f(x*) = {result['minimum_J']:.10f} J")


def derivatives(x, y, relative=.01):
    # Evaluate f(x + d) - f(x) directly to avoid subtracting rounded energies.
    dx = relative * (x if x else 1.)
    dy = relative * (y if y else 1.)
    xp, xm = dx*(2*A*x-Q1+A*dx), -dx*(2*A*x-Q1-A*dx)
    yp, ym = dy*(2*B*y-Q2+B*dy), -dy*(2*B*y-Q2-B*dy)
    # The four mixed stencil terms cancel identically by separability.
    return (xp-xm)/(2*dx), (yp-ym)/(2*dy), (xp+xm)/dx**2, (yp+ym)/dy**2


def raw_derivatives(x, y, relative, value, need_hessian):
    dx = relative * (x if x else 1.)
    dy = relative * (y if y else 1.)
    xp, xm = energy(x+dx,y), energy(x-dx,y)
    yp, ym = energy(x,y+dy), energy(x,y-dy)
    gx, gy = (xp-xm)/(2*dx), (yp-ym)/(2*dy)
    if not need_hessian:
        return gx, gy, 0., 0., 0.
    mixed = (energy(x+dx,y+dy)-energy(x+dx,y-dy)
             -energy(x-dx,y+dy)+energy(x-dx,y-dy))/(4*dx*dy)
    return gx, gy, (xp-2*value+xm)/dx**2, (yp-2*value+ym)/dy**2, mixed


def solve(method, width, damping, cap=200, start=(.1,.01), relative=.01,
          factor=2, tolerance=1e-5, comparison="stable", selection="best",
          stencil="stable", normalize_sd=False, newton_step_test=False):
    x, y = start
    rows = []
    for k in range(cap+1):
        value = energy(x,y)
        if stencil == "raw":
            gx, gy, hxx, hyy, mixed = raw_derivatives(x,y,relative,value,method!="SD")
        else:
            gx, gy, hxx, hyy = derivatives(x, y, relative)
            mixed = 0.
        norm = math.hypot(gx, gy)
        determinant = hxx*hyy-mixed*mixed
        hessian_positive_definite = method == "Newton" and hxx > 0 and determinant > 0
        row = dict(k=k, x=x, y=y, energy=value, gradient=norm,
                   damping=damping, alpha=0., evaluations=5 if method == "SD" else 9,
                   hessian_positive_definite=(hessian_positive_definite if method == "Newton" else None),
                   directional_derivative=None, status="running")
        rows.append(row)
        if not all(map(math.isfinite, (x, y, value, norm))):
            row["status"] = "diverged"
            break
        if method == "Newton" and newton_step_test and k:
            previous = rows[-2]
            scale = math.hypot(previous["x"], previous["y"])
            change = math.hypot(x-previous["x"], y-previous["y"])
            relative_change = change/scale if scale > 0 else change
            if relative_change < tolerance:
                row["status"] = "converged_relative_change"
                break
        gradient_met = norm <= tolerance and not (method == "Newton" and newton_step_test)
        if gradient_met or k == cap:
            row["status"] = "converged" if gradient_met else "cap"
            break
        if method == "SD":
            px, py = -gx, -gy
            if normalize_sd and norm:
                px, py = px/norm, py/norm
        elif stencil == "stable":
            shift = damping if method == "Marquardt" else 0
            px, py = -gx/(hxx+shift), -gy/(hyy+shift)
        else:
            shift = damping if method == "Marquardt" else 0
            xx, yy = hxx+shift, hyy+shift
            determinant = xx*yy-mixed*mixed
            px = (mixed*gy-yy*gx)/determinant
            py = (mixed*gx-xx*gy)/determinant

        if method == "Newton":
            directional = gx*px+gy*py
            row["directional_derivative"] = directional
            if not directional < 0:
                row["status"] = "restart_required"
                break
        if method == "Newton" and newton_step_test and math.hypot(px, py) < tolerance:
            row["status"] = "converged_step"
            break

        def raw_energy(alpha):
            return energy(x+alpha*px, y+alpha*py)

        if comparison == "stable":
            linear = gx*px + gy*py
            quadratic = A*px*px + B*py*py

        if method == "Marquardt":
            decrease = linear+quadratic < 0 if comparison == "stable" else raw_energy(1) < value
            alpha = float(decrease)
            damping = damping/factor if alpha else damping*factor
            row["evaluations"] += 1
        else:
            score = raw_energy
            if comparison == "stable":
                center = -linear/(2*quadratic)

                def score(alpha):
                    # Completing the square gives the same ordering as energy.
                    return abs(alpha-center)
            lo, hi = 0., 1.
            while hi-lo >= width:
                mid = (lo+hi)/2
                left, right = (lo+mid)/2, (mid+hi)/2
                middle_score = score(mid)
                if score(left) < middle_score:
                    hi = mid
                elif score(right) < middle_score:
                    lo = mid
                else:
                    lo, hi = left, right
                row["evaluations"] += 3
            alpha = (lo+hi)/2
            if selection == "best":
                alpha = min((lo,alpha,hi), key=score)
                row["evaluations"] += 3
            if alpha == 0:
                row["status"] = "stalled"
                break
        row["alpha"] = alpha
        x, y = x+alpha*px, y+alpha*py
    return rows


def numerical_derivation():
    """Direct objective evaluations for checking the first step by hand."""
    x, y = .1, .01
    delta1, delta2 = .01*x, .01*y
    gx, gy, h11, h22, h12 = raw_derivatives(x,y,.01,energy(x,y),True)
    stencil = [(x,y),(x+delta1,y),(x-delta1,y),(x,y+delta2),(x,y-delta2),
               (x+delta1,y+delta2),(x+delta1,y-delta2),
               (x-delta1,y+delta2),(x-delta1,y-delta2)]
    sd = (-gx,-gy)
    determinant = h11*h22-h12*h12
    newton = ((h12*gy-h22*gx)/determinant,
              (h12*gx-h11*gy)/determinant)
    damping_determinant = (h11+1000)*(h22+1000)-h12*h12
    marquardt = ((h12*gy-(h22+1000)*gx)/damping_determinant,
                 (h12*gx-(h11+1000)*gy)/damping_determinant)
    halvings = math.floor(-math.log2(1e-4))+1
    newton_alpha = 1-2**(-halvings-1)
    return {
        "stencil": [(u,v,energy(u,v)) for u,v in stencil],
        "gradient": (gx,gy), "hessian": (h11,h22,h12),
        "hessian_determinant": determinant,
        "hessian_positive_definite": h11 > 0 and determinant > 0,
        "SD direction": sd, "Newton direction": newton,
        "Newton directional derivative": gx*newton[0]+gy*newton[1],
        "Newton descent direction": gx*newton[0]+gy*newton[1] < 0,
        "Newton alpha": newton_alpha,
        "Marquardt direction": marquardt,
        "SD final candidates": [(alpha,energy(x+alpha*sd[0],y+alpha*sd[1]))
                                for alpha in (0.,2**-15,2**-14)],
        "SD final midpoint alpha": 2**-15,
        "Newton updated point": (x+newton_alpha*newton[0],y+newton_alpha*newton[1]),
        "Newton full-step point": (x+newton[0],y+newton[1]),
        "Marquardt trial point": (x+marquardt[0],y+marquardt[1]),
    }


def main():
    import matplotlib.pyplot as plt
    import numpy as np

    print_analytical_derivation()
    print("\nFirst numerical update for manual verification")
    for label, values in numerical_derivation().items():
        print(label, values)
    figures = ROOT / "figures"
    figures.mkdir(exist_ok=True)
    runs = {case.name: case.run() for case in CASES}
    # Literal homework procedure: direct f evaluations, final IHM midpoint,
    # and the lecture-note halve/double Marquardt update.
    runs["Literal SD baseline"] = solve(
        "SD",1e-4,1000,comparison="raw",selection="midpoint",stencil="raw")
    runs["Literal SD normalized"] = solve(
        "SD",1e-4,1000,comparison="raw",selection="midpoint",stencil="raw",
        normalize_sd=True)
    runs["Literal Newton baseline"] = solve(
        "Newton",1e-4,1000,factor=2,comparison="raw",selection="midpoint",stencil="raw",
        newton_step_test=True)
    runs["Literal Marquardt baseline"] = solve(
        "Marquardt",1e-4,1000,factor=2,comparison="raw",selection="midpoint",stencil="raw")
    direct = dict(comparison="raw", selection="midpoint", stencil="raw")
    runs["Literal SD tighter"] = solve("SD", 1e-13, 1000, **direct)
    runs["Literal SD extended midpoint"] = solve("SD", 1e-13, 1000, cap=400, **direct)
    runs["Literal Newton gradient"] = solve("Newton", 1e-4, 1000, **direct)
    runs["Literal Newton tighter"] = solve(
        "Newton", 1e-8, 1000, newton_step_test=True, **direct)
    runs["Literal Marquardt factor 10"] = solve(
        "Marquardt", 1e-4, 1000, factor=10, **direct)
    runs["Literal Marquardt larger"] = solve(
        "Marquardt", 1e-4, 100000, factor=2, **direct)
    for comparison, selection in [
        ("stable", "midpoint"), ("raw", "best"), ("raw", "midpoint"),
    ]:
        runs[f"Newton {comparison} {selection}"] = solve(
            "Newton",1e-4,1000,comparison=comparison,selection=selection
        )
    by_name = {case.name: case for case in CASES}
    for name in ("SD baseline", "SD extended", "Newton baseline", "Marquardt factor 10"):
        runs[f"{name} literal"] = by_name[name].run(comparison="raw",stencil="raw")
    runs["Newton midpoint literal"] = by_name["Newton baseline"].run(
        comparison="raw", selection="midpoint", stencil="raw"
    )
    with (ROOT/"python_iterations.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["case", *next(iter(runs.values()))[0]])
        writer.writeheader()
        for name, rows in runs.items():
            writer.writerows(dict(case=name, **row) for row in rows)
            print(name, rows[-1], sum(row["evaluations"] for row in rows))
    baseline_paths = ["Literal SD baseline", "Literal SD normalized", "Literal Newton baseline", "Literal Marquardt baseline"]
    sensitivity_paths = ["Literal SD extended midpoint", "Literal Newton tighter", "Literal Marquardt larger"]
    for label, names, window in [
        ("design_space", [], (0,1,0,.1)),
        ("baseline", baseline_paths, (0,1,0,.1)),
        ("baseline_detail", baseline_paths, (.08,.27,.004,.011)),
        ("sensitivity", sensitivity_paths, (0,1,0,.1)),
        ("detail", sensitivity_paths, (.08,.27,-.003,.014)),
        ("graphical", [], (.225,.275,.0,.011)),
    ]:
        xmin,xmax,ymin,ymax = window
        x,y = np.meshgrid(np.linspace(xmin,xmax,601), np.linspace(ymin,ymax,501))
        fig, ax = plt.subplots(figsize=(6.5,3.65), layout="constrained")
        levels = [-1098,-1097,-1095,-1090] if label=="graphical" else [
            -1097,-1088,-1048,-998,-798,-98,1902
        ]
        contours = ax.contour(x,y,energy(x,y),levels=levels,
                              colors="#53677e",linewidths=.7)
        ax.clabel(contours,fmt="%g",fontsize=7)
        for name in names:
            rows = runs[name][:2] if name == "Literal SD baseline" else runs[name]
            ax.plot([r["x"] for r in rows],[r["y"] for r in rows],
                    "o-",markersize=3, markevery=max(1,len(rows)//16),label=name)
        if label != "graphical":
            ax.plot(*OPT,"k*",markersize=9,label="Analytical minimum")
        ax.set(xlabel="Horizontal displacement $x_1$ (m)",
               ylabel="Vertical displacement $x_2$ (m)", xlim=(xmin,xmax), ylim=(ymin,ymax))
        if label != "graphical":
            ax.legend(loc="upper right",fontsize=7)
        fig.savefig(figures/f"{label}.pdf")
        plt.close(fig)


if __name__ == "__main__":
    main()
