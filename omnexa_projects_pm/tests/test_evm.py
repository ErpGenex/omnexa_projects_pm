# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from datetime import date

from frappe.tests.utils import FrappeTestCase

from omnexa_projects_pm.evm import planned_percent_complete


class TestEvmPlannedPercent(FrappeTestCase):
	def test_before_start_zero(self):
		self.assertEqual(planned_percent_complete(date(2026, 6, 15), date(2026, 6, 20), date(2026, 6, 30)), 0.0)

	def test_after_end_one(self):
		self.assertEqual(planned_percent_complete(date(2026, 7, 15), date(2026, 6, 20), date(2026, 6, 30)), 1.0)

	def test_mid_duration(self):
		# 11 calendar days Jun20–Jun30; as_of Jun25 => 6 elapsed / 11
		p = planned_percent_complete(date(2026, 6, 25), date(2026, 6, 20), date(2026, 6, 30))
		self.assertAlmostEqual(p, 6 / 11, places=5)

	def test_no_dates_zero(self):
		self.assertEqual(planned_percent_complete(date(2026, 1, 1), None, None), 0.0)
