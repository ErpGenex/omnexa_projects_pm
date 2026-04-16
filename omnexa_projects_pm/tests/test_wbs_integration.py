# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from frappe.tests.utils import FrappeTestCase

from omnexa_projects_pm.wbs_integration import (
	validate_linked_pm_wbs_task,
	weighted_boq_completion_percent,
)


class TestWbsIntegration(FrappeTestCase):
	def test_validate_linked_pm_wbs_task_skips_when_no_task(self):
		validate_linked_pm_wbs_task("Some Project", None)
		validate_linked_pm_wbs_task(None, None)

	def test_weighted_boq_completion_percent_empty(self):
		self.assertEqual(weighted_boq_completion_percent([]), 0.0)

	def test_weighted_boq_completion_percent_equal_weights_when_no_cost(self):
		pct = weighted_boq_completion_percent(
			[
				{"completion_percent": 40, "planned_cost": 0},
				{"completion_percent": 60, "planned_cost": 0},
			]
		)
		self.assertEqual(pct, 50.0)

	def test_weighted_boq_completion_percent_cost_weighted(self):
		pct = weighted_boq_completion_percent(
			[
				{"completion_percent": 0, "planned_cost": 900},
				{"completion_percent": 100, "planned_cost": 100},
			]
		)
		self.assertEqual(pct, 10.0)

	def test_weighted_boq_completion_percent_clamped(self):
		pct = weighted_boq_completion_percent(
			[{"completion_percent": 150, "planned_cost": 1}],
		)
		self.assertEqual(pct, 100.0)
