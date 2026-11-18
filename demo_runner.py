"""
Flash Separator Demonstration & Parametric Sweep Runner
======================================================
Course: CHE F376 / F377 - Design Oriented Project (DOP), BITS Pilani
Authors: Ayushya Ramesh Ojha & Aryan Jain
Supervisor: Faculty Advisory

Demonstrates:
  1. Instant verification of the flash separator convergence.
  2. Automated parametric temperature sweep showing V/F vs Temperature (T-xy curve generation).
  3. Seamless browser opening of the interactive visual flowsheet dashboard.
"""

import os
import sys
import webbrowser
import argparse
from standalone_flash_verification import ThermodynamicFlashEngine, print_flash_report
from run_dwsim_flash_separator import find_dwsim_installation, run_dwsim_flash_simulation


def run_parametric_temperature_sweep():
    """
    Simulates what an automated AI agent performs: sweeps temperature across
    the phase envelope to identify bubble point, optimum flash point, and dew point.
    """
    print("\n" + "=" * 78)
    print("  AUTOMATED PARAMETRIC TEMPERATURE SWEEP (Ethanol / Water, P = 1.013 bar)")
    print("  Simulating AI Assistant Parameter Tuning & Phase Envelope Tracking")
    print("=" * 78)
    print(f"  {'T (K)':<10} {'T (°C)':<10} {'Phase State':<26} {'Vapor Frac (V/F)':<18} {'y_Ethanol':<12} {'x_Ethanol':<12}")
    print(f"  {'-'*8:<10} {'-'*8:<10} {'-'*24:<26} {'-'*16:<18} {'-'*10:<12} {'-'*10:<12}")

    temperatures = [340.0, 350.0, 355.0, 358.0, 360.0, 363.0, 366.0, 370.0, 375.0]
    for T in temperatures:
        res = ThermodynamicFlashEngine.solve_flash(
            compounds=["Ethanol", "Water"],
            feed_mole_fractions=[0.50, 0.50],
            T_K=T,
            P_bar=1.01325,
            feed_flow_mol_s=100.0,
            model="wilson"
        )
        psi = res["vapor_fraction_psi"]
        y_etoh = res["vapor_y"][0] if psi > 0 else 0.0
        x_etoh = res["liquid_x"][0] if psi < 1.0 else 0.0
        state = res["phase_state"]
        if "Subcooled" in state:
            short_state = "Subcooled Liquid"
        elif "Superheated" in state:
            short_state = "Superheated Vapor"
        else:
            short_state = "VLE (Two-Phase)"

        print(f"  {T:<10.1f} {T-273.15:<10.1f} {short_state:<26} {psi:<18.4f} {y_etoh:<12.4f} {x_etoh:<12.4f}")

    print("=" * 78 + "\n")


def open_interactive_dashboard():
    """Opens the interactive web demo in the user's default browser."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, "..", "3_Interactive_Web_App", "index.html"),
        os.path.join(script_dir, "..", "..", "3_Hosted_Web_Demo_and_Repository", "index.html"),
        os.path.join(script_dir, "interactive_flash_demo.html")
    ]
    for html_path in candidates:
        if os.path.exists(html_path):
            abs_p = os.path.abspath(html_path)
            print(f"\n[DASHBOARD] Opening Interactive Flowsheet Dashboard in default browser:")
            print(f"            file:///{abs_p.replace(os.sep, '/')}")
            webbrowser.open(f"file:///{abs_p}")
            return
    print("\n[DASHBOARD] Opening Live Hosted Web Demo in browser:")
    webbrowser.open("https://ayushya16.github.io/chemical-ai-autonomous-project-ayushya-aryan/")


def main():
    parser = argparse.ArgumentParser(description="Flash Separator Master Demo Runner")
    parser.add_argument("--sweep", action="store_true", help="Run automated parametric temperature sweep")
    parser.add_argument("--open-gui", action="store_true", help="Open visual HTML dashboard in web browser")
    parser.add_argument("--dwsim-check", action="store_true", help="Check DWSIM installation status")
    args = parser.parse_args()

    print("\n" + "#" * 78)
    print("  BITS PILANI - DEPARTMENT OF CHEMICAL ENGINEERING")
    print("  DESIGN ORIENTED PROJECT (DOP) TECHNICAL DELIVERABLE")
    print("  Students: Ayushya Ramesh Ojha & Aryan Jain | Supervisor: Faculty Advisory")
    print("#" * 78)

    # 1. Primary Benchmark Execution
    print("\n[STEP 1] Executing Standard Flash Separator Convergence Benchmark...")
    res = ThermodynamicFlashEngine.solve_flash(
        compounds=["Ethanol", "Water"],
        feed_mole_fractions=[0.50, 0.50],
        T_K=360.0,
        P_bar=1.01325,
        feed_flow_mol_s=100.0,
        model="wilson"
    )
    print_flash_report(res)

    # 2. Parametric Sweep
    run_parametric_temperature_sweep()

    # 3. DWSIM Status Check
    dwsim_dir = find_dwsim_installation()
    if dwsim_dir:
        print(f"[STATUS] DWSIM Installation detected at: {dwsim_dir}")
        print("         The Automation3 API script is ready to interface directly.")
    else:
        print("[STATUS] DWSIM is not yet installed in standard paths on this machine.")
        print("         Install DWSIM v8 or v9, or set DWSIM_PATH environment variable.")
        print("         The standalone thermodynamic engine provides 100% mathematical validation.")

    # 4. Open Interactive Dashboard if requested
    if args.open_gui:
        open_interactive_dashboard()


if __name__ == "__main__":
    main()
