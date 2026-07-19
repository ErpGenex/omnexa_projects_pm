# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from types import SimpleNamespace

from frappe.tests.utils import FrappeTestCase

from omnexa_projects_pm.cpm_engine import _compute_cpm_for_project


class TestCpmEngine(FrappeTestCase):
	def test_critical_path_chain(self):
		tasks = [
			SimpleNamespace(name="A", task_name="A", planned_start="2026-01-01", planned_end="2026-01-05"),
			SimpleNamespace(name="B", task_name="B", planned_start="2026-01-06", planned_end="2026-01-10"),
		]
		deps = [
			SimpleNamespace(parent="B", depends_on_task="A", dependency_type="FS", lag_days=0),
		]
		rows = _compute_cpm_for_project(tasks, deps, "TEST")
		self.assertEqual(len(rows), 2)
		critical = [r for r in rows if r["cpm_flag"] == "Critical"]
		self.assertEqual(len(critical), 2)
