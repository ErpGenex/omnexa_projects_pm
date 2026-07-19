# Copyright (c) 2026, ErpGenEx
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.vertical_parity import preview_for_vertical


class TestSapParitySector(FrappeTestCase):
	def test_vertical_kpi_preview(self):
		out = preview_for_vertical("projects_pm", planned_value=100, earned_value=80, actual_cost=90)
		self.assertEqual(out["vertical"], "projects_pm")
		self.assertIn("kpi", out)
		self.assertIn("sap_module", out)
