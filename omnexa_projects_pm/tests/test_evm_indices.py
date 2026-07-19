# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from frappe.tests.utils import FrappeTestCase

from omnexa_projects_pm.evm import compute_evm_indices


class TestEvmIndices(FrappeTestCase):
	def test_pmi_indices(self):
		out = compute_evm_indices(bac=1000, pv=500, ev=450, ac=400)
		self.assertEqual(out["schedule_variance"], -50)
		self.assertEqual(out["cost_variance"], 50)
		self.assertAlmostEqual(out["spi"], 0.9, places=4)
		self.assertAlmostEqual(out["cpi"], 1.125, places=4)
		self.assertEqual(out["schedule_health_status"], "At Risk")
		self.assertEqual(out["cost_health_status"], "On Budget")

	def test_delayed_and_over_budget(self):
		out = compute_evm_indices(bac=1000, pv=800, ev=500, ac=700)
		self.assertEqual(out["schedule_health_status"], "Delayed")
		self.assertEqual(out["cost_health_status"], "Over Budget")
