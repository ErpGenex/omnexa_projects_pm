# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from frappe.tests.utils import FrappeTestCase

from omnexa_projects_pm.omnexa_projects_pm.report.pm_resource_loading.pm_resource_loading import execute


class TestPmResourceLoadingReport(FrappeTestCase):
	def test_execute_returns_columns_and_rows(self):
		columns, rows = execute({})
		self.assertTrue(columns)
		self.assertIsInstance(rows, list)
		fieldnames = {c["fieldname"] for c in columns}
		self.assertIn("project", fieldnames)
		self.assertIn("utilization_pct", fieldnames)

	def test_utilization_pct_computed_when_planned_hours_set(self):
		columns, rows = execute({})
		for r in rows:
			ph = float(r.get("planned_hours") or 0)
			ah = float(r.get("actual_hours") or 0)
			expected = (ah / ph * 100.0) if ph else 0.0
			self.assertAlmostEqual(float(r.get("utilization_pct") or 0), expected, places=5)
