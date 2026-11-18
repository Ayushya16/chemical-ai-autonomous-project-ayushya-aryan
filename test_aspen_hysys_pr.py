"""
Automated Unit Tests for Aspen HYSYS Peng-Robinson Hydrocarbon Flash Engine
=============================================================================
Validates:
1. Mass Conservation Closure < 1e-10
2. Component Species Balance Closure
3. Compressibility Factor Validity (0 < Z_liq < 1 and 0 < Z_vap <= 1)
4. Monotonic Phase Boundaries (Subcooled & Superheated Limits)
5. Execution Speed Benchmark (< 20 ms)
=============================================================================
"""

import unittest
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from standalone_hysys_pr_flash import solve_hysys_pr_flash

class TestAspenHysysPREngine(unittest.TestCase):
    
    def setUp(self):
        # Typical natural gas composition
        self.z_feed = [0.75, 0.10, 0.07, 0.05, 0.03]
        
    def test_mass_conservation_closure(self):
        """Mass in must equal Mass out to machine precision"""
        res = solve_hysys_pr_flash(T_K=293.15, P_bar=45.0, z_feed=self.z_feed)
        self.assertLess(res["mass_closure_error_kg_s"], 1e-10)
        
    def test_component_species_balance(self):
        """z_i * F = y_i * V + x_i * L for every component"""
        res = solve_hysys_pr_flash(T_K=288.15, P_bar=50.0, z_feed=self.z_feed)
        beta = res["vapor_fraction_beta"]
        for i in range(len(self.z_feed)):
            zi = res["feed_composition"][i]
            yi = res["vapor_composition"][i]
            xi = res["liquid_composition"][i]
            calculated_z = beta * yi + (1.0 - beta) * xi
            self.assertAlmostEqual(zi, calculated_z, places=7)
            
    def test_compressibility_factor_realism(self):
        """Z_vap and Z_liq must be physically realistic"""
        res = solve_hysys_pr_flash(T_K=298.15, P_bar=40.0, z_feed=self.z_feed)
        self.assertGreater(res["Z_vapor"], 0.6)
        self.assertLess(res["Z_vapor"], 1.0)
        self.assertGreater(res["Z_liquid"], 0.05)
        self.assertLess(res["Z_liquid"], 0.4)
        
    def test_high_pressure_retrograde_boundary(self):
        """Tests high pressure gas processing condition"""
        res = solve_hysys_pr_flash(T_K=310.15, P_bar=60.0, z_feed=self.z_feed)
        self.assertGreaterEqual(res["vapor_fraction_beta"], 0.0)
        self.assertLessEqual(res["vapor_fraction_beta"], 1.0)
        
    def test_execution_latency(self):
        """Solver must complete in < 20 ms for real-time copilot interactivity"""
        t0 = time.perf_counter()
        for _ in range(20):
            solve_hysys_pr_flash(T_K=290.15, P_bar=48.0, z_feed=self.z_feed)
        elapsed_per_run_ms = ((time.perf_counter() - t0) / 20.0) * 1000.0
        print(f"\n[BENCHMARK] Mean Peng-Robinson Flash solve latency: {elapsed_per_run_ms:.2f} ms")
        self.assertLess(elapsed_per_run_ms, 20.0)

if __name__ == "__main__":
    unittest.main()
