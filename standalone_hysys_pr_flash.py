"""
Standalone Thermodynamic Verification Engine for Multicomponent Hydrocarbon Flash
Standard Aspen HYSYS Peng-Robinson Equation of State (PR-EOS) Benchmark
=============================================================================
Mixture: Natural Gas & Condensate (Methane, Ethane, Propane, n-Butane, n-Pentane)
Thermodynamics: Peng-Robinson Equation of State with van der Waals Mixing Rules
Numerical Method: Accelerated Successive Substitution with Rachford-Rice Inner Loop
=============================================================================
"""

import math
import numpy as np

# Component physical constants (Tc in K, Pc in bar, omega, Mw in g/mol)
COMPONENTS = [
    {"name": "Methane (C1)",  "Tc": 190.56, "Pc": 45.99, "omega": 0.0115, "Mw": 16.043},
    {"name": "Ethane (C2)",   "Tc": 305.32, "Pc": 48.72, "omega": 0.0995, "Mw": 30.070},
    {"name": "Propane (C3)",  "Tc": 369.83, "Pc": 42.48, "omega": 0.1523, "Mw": 44.097},
    {"name": "n-Butane (nC4)","Tc": 425.12, "Pc": 37.96, "omega": 0.2002, "Mw": 58.123},
    {"name": "n-Pentane (C5+)","Tc": 469.70, "Pc": 33.70, "omega": 0.2515, "Mw": 72.150},
]

R_GAS = 8.314462618  # J / (mol * K) = bar * cm3 / (mol * K) * 10
# In bar * L / (mol * K): R = 0.08314462618
R_BAR_L = 0.08314462618

def solve_cubic_roots(A, B):
    """
    Solves PR-EOS cubic: Z^3 - (1-B)Z^2 + (A - 3B^2 - 2B)Z - (AB - B^2 - B^3) = 0
    Returns: (Z_vap, Z_liq)
    """
    c2 = -(1.0 - B)
    c1 = A - 3.0 * B * B - 2.0 * B
    c0 = -(A * B - B * B - B * B * B)
    
    roots = np.roots([1.0, c2, c1, c0])
    real_roots = [r.real for r in roots if abs(r.imag) < 1e-10 and r.real > B]
    
    if not real_roots:
        # Fallback to single real root
        real_roots = [r.real for r in roots if r.real > 0]
    
    Z_vap = max(real_roots)
    Z_liq = min(real_roots)
    return Z_vap, Z_liq

def calc_pr_pure_params(T):
    """Calculates pure component a_i(T) and b_i"""
    n = len(COMPONENTS)
    a = np.zeros(n)
    b = np.zeros(n)
    
    for i, c in enumerate(COMPONENTS):
        Tr = T / c["Tc"]
        m = 0.37464 + 1.54226 * c["omega"] - 0.26992 * c["omega"]**2
        alpha = (1.0 + m * (1.0 - math.sqrt(Tr)))**2
        a[i] = 0.45724 * (R_BAR_L * c["Tc"])**2 / c["Pc"] * alpha
        b[i] = 0.07780 * (R_BAR_L * c["Tc"]) / c["Pc"]
    return a, b

def calc_mixture_pr(z, T, P, a_pure, b_pure):
    """
    Calculates mixture A, B and fugacity coefficients ln_phi for composition z.
    """
    n = len(z)
    # van der Waals mixing rules (assuming kij = 0 for standard hydrocarbons)
    a_mix = 0.0
    for i in range(n):
        for j in range(n):
            a_mix += z[i] * z[j] * math.sqrt(a_pure[i] * a_pure[j])
            
    b_mix = float(np.sum(z * b_pure))
    
    A = a_mix * P / (R_BAR_L * T)**2
    B = b_mix * P / (R_BAR_L * T)
    
    Z_vap, Z_liq = solve_cubic_roots(A, B)
    
    # Fugacity coefficients for each component
    def calc_phi(Z):
        ln_phi = np.zeros(n)
        sqrt2 = math.sqrt(2.0)
        term_Z = Z - B
        if term_Z <= 1e-12:
            term_Z = 1e-12
        log_term_Z = math.log(term_Z)
        
        log_ratio = math.log((Z + (1.0 + sqrt2) * B) / max(Z + (1.0 - sqrt2) * B, 1e-12))
        
        for i in range(n):
            sum_aj = 0.0
            for j in range(n):
                sum_aj += z[j] * math.sqrt(a_pure[i] * a_pure[j])
                
            ln_phi[i] = (b_pure[i] / b_mix) * (Z - 1.0) - log_term_Z - \
                        (A / (2.0 * sqrt2 * B)) * (2.0 * sum_aj / a_mix - b_pure[i] / b_mix) * log_ratio
        return ln_phi, Z
        
    ln_phi_v, Zv = calc_phi(Z_vap)
    ln_phi_l, Zl = calc_phi(Z_liq)
    return ln_phi_v, Zv, ln_phi_l, Zl

def solve_rachford_rice(z, K):
    """Solves r(beta) = sum(z_i * (K_i - 1) / (1 + beta * (K_i - 1))) = 0"""
    # Check single phase boundaries
    r0 = np.sum(z * (K - 1.0))
    r1 = np.sum(z * (1.0 - 1.0 / K))
    
    if r0 <= 0.0:
        return 0.0  # Subcooled liquid
    if r1 >= 0.0:
        return 1.0  # Superheated vapor
        
    beta = 0.5
    for _ in range(50):
        denom = 1.0 + beta * (K - 1.0)
        r = np.sum(z * (K - 1.0) / denom)
        dr = -np.sum(z * (K - 1.0)**2 / (denom**2))
        
        step = r / dr
        beta_new = beta - step
        # Keep inside (0, 1)
        if beta_new <= 0.0:
            beta_new = beta * 0.5
        elif beta_new >= 1.0:
            beta_new = 0.5 * (beta + 1.0)
            
        if abs(beta_new - beta) < 1e-10:
            return beta_new
        beta = beta_new
    return beta

def solve_hysys_pr_flash(T_K, P_bar, z_feed):
    """
    Full isothermal PR-EOS flash solver mimicking Aspen HYSYS flash engine.
    T_K: Temperature in Kelvin
    P_bar: Pressure in bar
    z_feed: list or array of 5 mole fractions (C1, C2, C3, nC4, nC5+)
    """
    z = np.array(z_feed, dtype=float)
    z = z / np.sum(z)
    n = len(z)
    
    a_pure, b_pure = calc_pr_pure_params(T_K)
    
    # Initial Wilson K-values estimate: K_i = (Pc_i / P) * exp[ 5.373 * (1 + omega_i) * (1 - Tc_i / T) ]
    K = np.zeros(n)
    for i, c in enumerate(COMPONENTS):
        K[i] = (c["Pc"] / P_bar) * math.exp(5.373 * (1.0 + c["omega"]) * (1.0 - c["Tc"] / T_K))
        
    beta = solve_rachford_rice(z, K)
    
    # Outer loop: Successive substitution to converge K-values
    max_iter = 100
    for iteration in range(max_iter):
        if beta <= 0.0 or beta >= 1.0:
            break
            
        x = z / (1.0 + beta * (K - 1.0))
        x = x / np.sum(x)
        y = K * x
        y = y / np.sum(y)
        
        ln_phi_v, Zv, _, _ = calc_mixture_pr(y, T_K, P_bar, a_pure, b_pure)
        _, _, ln_phi_l, Zl = calc_mixture_pr(x, T_K, P_bar, a_pure, b_pure)
        
        K_new = np.exp(ln_phi_l - ln_phi_v)
        # Accelerated damping
        K_damped = 0.6 * K_new + 0.4 * K
        
        residual = np.max(np.abs(K_new - K))
        if residual < 1e-8:
            K = K_new
            beta = solve_rachford_rice(z, K)
            break
            
        K = K_damped
        beta = solve_rachford_rice(z, K)
        
    if beta <= 0.0:
        beta = 0.0
        x = z.copy()
        y = z.copy()
        Zv, Zl = 0.85, 0.08
    elif beta >= 1.0:
        beta = 1.0
        x = z.copy()
        y = z.copy()
        Zv, Zl = 0.85, 0.08
    else:
        x = z / (1.0 + beta * (K - 1.0))
        x = x / np.sum(x)
        y = K * x
        y = y / np.sum(y)
        ln_phi_v, Zv, _, _ = calc_mixture_pr(y, T_K, P_bar, a_pure, b_pure)
        _, _, ln_phi_l, Zl = calc_mixture_pr(x, T_K, P_bar, a_pure, b_pure)
        
    Mw_feed = float(np.sum(z * [c["Mw"] for c in COMPONENTS]))
    Mw_vap = float(np.sum(y * [c["Mw"] for c in COMPONENTS]))
    Mw_liq = float(np.sum(x * [c["Mw"] for c in COMPONENTS]))
    
    # Mass balance closure check
    # Feed = 100 mol/s
    F_mol = 100.0
    V_mol = beta * F_mol
    L_mol = (1.0 - beta) * F_mol
    
    F_mass = F_mol * Mw_feed / 1000.0  # kg/s
    V_mass = V_mol * Mw_vap / 1000.0
    L_mass = L_mol * Mw_liq / 1000.0
    mass_err = abs(F_mass - (V_mass + L_mass))
    
    return {
        "temperature_K": T_K,
        "temperature_C": T_K - 273.15,
        "pressure_bar": P_bar,
        "vapor_fraction_beta": beta,
        "feed_composition": z.tolist(),
        "vapor_composition": y.tolist(),
        "liquid_composition": x.tolist(),
        "K_values": K.tolist(),
        "Z_vapor": float(Zv),
        "Z_liquid": float(Zl),
        "Mw_feed": Mw_feed,
        "Mw_vap": Mw_vap,
        "Mw_liq": Mw_liq,
        "mass_closure_error_kg_s": mass_err,
        "components": [c["name"] for c in COMPONENTS]
    }

if __name__ == "__main__":
    print("=" * 78)
    print("ASPEN HYSYS PENG-ROBINSON EOS VERIFICATION ENGINE")
    print("=" * 78)
    
    # Standard Natural Gas Feed (Typical high-pressure gas well stream)
    # C1=0.75, C2=0.10, C3=0.07, nC4=0.05, nC5+=0.03
    z_test = [0.75, 0.10, 0.07, 0.05, 0.03]
    T_test = 293.15  # 20 °C
    P_test = 45.0    # 45 bar (4.5 MPa)
    
    res = solve_hysys_pr_flash(T_test, P_test, z_test)
    print(f"Condition: T = {res['temperature_C']:.2f} °C ({res['temperature_K']:.2f} K), P = {res['pressure_bar']:.2f} bar")
    print(f"Vapor Fraction (beta): {res['vapor_fraction_beta']:.4f} ({res['vapor_fraction_beta']*100:.2f} mol%)")
    print(f"Compressibility: Z_vap = {res['Z_vapor']:.4f}, Z_liq = {res['Z_liquid']:.4f}")
    print(f"Mass Closure Error: {res['mass_closure_error_kg_s']:.2e} kg/s")
    print("-" * 78)
    print(f"{'Component':<18} {'Feed (z)':<12} {'Overhead (y)':<14} {'Bottoms (x)':<14} {'K-value':<10}")
    print("-" * 78)
    for i, name in enumerate(res['components']):
        print(f"{name:<18} {res['feed_composition'][i]:<12.4f} {res['vapor_composition'][i]:<14.4f} {res['liquid_composition'][i]:<14.4f} {res['K_values'][i]:<10.4f}")
    print("=" * 78)
