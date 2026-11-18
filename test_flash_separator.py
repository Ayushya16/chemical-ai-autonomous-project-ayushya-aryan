"""
Automated Unit Tests & Convergence Assertion Suite
==================================================
Course: CHE F376 / F377 - Design Oriented Project (DOP), BITS Pilani
Students: Ayushya Ramesh Ojha & Aryan Jain
Supervisor: Faculty Advisory

Verifies:
  1. Bubble point boundary conditions (Subcooled single-phase liquid).
  2. Dew point boundary conditions (Superheated single-phase vapor).
  3. Two-phase vapor-liquid equilibrium (Rachford-Rice root finding).
  4. Mass conservation and species conservation down to machine precision.
  5. Multi-component stability (Binary and Ternary systems).
"""

import unittest
from standalone_flash_verification import ThermodynamicFlashEngine


class TestFlashSeparatorConvergence(unittest.TestCase):
    """Test suite asserting rigorous thermodynamic behavior and numerical stability."""

    def test_two_phase_ethanol_water_convergence(self):
        """Tests standard two-phase flash of 50-50 mol% Ethanol/Water at 360 K, 1 atm."""
        res = ThermodynamicFlashEngine.solve_flash(
            compounds=["Ethanol", "Water"],
            feed_mole_fractions=[0.50, 0.50],
            T_K=360.0,
            P_bar=1.01325,
            feed_flow_mol_s=100.0,
            model="wilson"
        )
        self.assertTrue(res["converged"])
        self.assertEqual(res["phase_state"], "Two-Phase (Vapor + Liquid Equilibrium)")
        self.assertGreater(res["vapor_fraction_psi"], 0.20)
        self.assertLess(res["vapor_fraction_psi"], 0.40)
        # Verify relative volatility (Ethanol is more volatile than Water)
        self.assertGreater(res["k_values"][0], res["k_values"][1])
        # Vapor is enriched in Ethanol
        self.assertGreater(res["vapor_y"][0], res["liquid_x"][0])
        # Mass conservation
        self.assertLess(res["relative_mass_error"], 1e-10)
        self.assertLess(res["max_component_balance_error"], 1e-8)

    def test_subcooled_liquid_boundary(self):
        """Tests that flash at cold temperature (300 K / 27 °C, 1 atm) yields 100% liquid (psi = 0)."""
        res = ThermodynamicFlashEngine.solve_flash(
            compounds=["Ethanol", "Water"],
            feed_mole_fractions=[0.50, 0.50],
            T_K=300.0,
            P_bar=1.01325,
            feed_flow_mol_s=100.0,
            model="wilson"
        )
        self.assertTrue(res["converged"])
        self.assertEqual(res["phase_state"], "Subcooled Liquid (Single Phase)")
        self.assertEqual(res["vapor_fraction_psi"], 0.0)
        self.assertEqual(res["vapor_flow_mol_s"], 0.0)
        self.assertEqual(res["liquid_flow_mol_s"], 100.0)
        self.assertLess(res["relative_mass_error"], 1e-12)

    def test_superheated_vapor_boundary(self):
        """Tests that flash at high temperature (395 K / 122 °C, 1 atm) yields 100% vapor (psi = 1)."""
        res = ThermodynamicFlashEngine.solve_flash(
            compounds=["Ethanol", "Water"],
            feed_mole_fractions=[0.50, 0.50],
            T_K=395.0,
            P_bar=1.01325,
            feed_flow_mol_s=100.0,
            model="wilson"
        )
        self.assertTrue(res["converged"])
        self.assertEqual(res["phase_state"], "Superheated Vapor (Single Phase)")
        self.assertEqual(res["vapor_fraction_psi"], 1.0)
        self.assertEqual(res["liquid_flow_mol_s"], 0.0)
        self.assertEqual(res["vapor_flow_mol_s"], 100.0)
        self.assertLess(res["relative_mass_error"], 1e-12)

    def test_ternary_hydrocarbon_flash(self):
        """Tests multi-component hydrocarbon flash (Propane, n-Butane, n-Pentane)."""
        res = ThermodynamicFlashEngine.solve_flash(
            compounds=["Propane", "n-Butane", "n-Pentane"],
            feed_mole_fractions=[0.25, 0.50, 0.25],
            T_K=320.0,
            P_bar=4.0,
            feed_flow_mol_s=200.0,
            model="wilson"
        )
        self.assertTrue(res["converged"])
        self.assertGreater(res["vapor_fraction_psi"], 0.0)
        self.assertLess(res["vapor_fraction_psi"], 1.0)
        # Verify K-ordering: K_propane > K_butane > K_pentane
        self.assertGreater(res["k_values"][0], res["k_values"][1])
        self.assertGreater(res["k_values"][1], res["k_values"][2])
        # Strict mass balance
        self.assertLess(res["relative_mass_error"], 1e-10)

    def test_rachford_rice_monotonicity(self):
        """Verifies that the Rachford-Rice derivative f'(psi) is strictly negative everywhere."""
        z = [0.3, 0.4, 0.3]
        K = [4.5, 1.8, 0.6]
        for psi in [0.05, 0.25, 0.5, 0.75, 0.95]:
            f, df = ThermodynamicFlashEngine.rachford_rice_objective(psi, z, K)
            self.assertLess(df, 0.0, f"Derivative must be negative at psi={psi}, got {df}")


if __name__ == "__main__":
    unittest.main()
