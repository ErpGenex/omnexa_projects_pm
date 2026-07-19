# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from frappe.tests.utils import FrappeTestCase

from omnexa_projects_pm.evm import compute_evm_indices
from omnexa_projects_pm.gl_cost_bridge import get_gl_actual_cost
from omnexa_projects_pm.qhse_quality_bridge import _project_quality
from omnexa_projects_pm.resource_leveling import detect_resource_overloads


class TestGapClosure(FrappeTestCase):
	def test_gl_cost_empty_project(self):
		out = get_gl_actual_cost("__nonexistent__")
		self.assertEqual(out["total"], 0.0)
		self.assertEqual(out["source"], "none")

	def test_quality_score_penalty(self):
		out = _project_quality("__test__")
		self.assertEqual(out["quality_score"], 100.0)
		self.assertIn("open_ncrs", out)

	def test_resource_overloads_empty(self):
		self.assertEqual(detect_resource_overloads("__none__"), [])

	def test_evm_ac_source_field(self):
		out = compute_evm_indices(bac=100, pv=50, ev=40, ac=30)
		self.assertEqual(out["ac"], 30)
