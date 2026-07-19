# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from omnexa_core.omnexa_core.utils.report_charts import auto_chart_for_columns

from omnexa_core.omnexa_core.report_print.report_query_filters import (
	get_all_filters,
	prepare_filters,
)
from omnexa_projects_pm.cpm_engine import _compute_cpm_for_project


def execute(filters=None):
	filters = prepare_filters(filters)
	filters_dict = get_all_filters(
		filters,
		"PM WBS Task",
		date_field="creation",
		company=True,
		branch=True,
		extra_links={},
	)
	tasks = frappe.get_all(
		"PM WBS Task",
		fields=["name", "project", "task_name", "planned_start", "planned_end", "status"],
		filters=filters_dict,
		limit_page_length=5000,
	)
	if not tasks:
		return _columns(), []

	dependencies = frappe.get_all(
		"PM Task Dependency",
		fields=["parent", "depends_on_task", "dependency_type", "lag_days"],
		limit_page_length=10000,
	)

	by_project: dict[str, list] = {}
	for task in tasks:
		by_project.setdefault(task.project, []).append(task)

	data: list[dict] = []
	for project_name, project_tasks in by_project.items():
		task_names = {t.name for t in project_tasks}
		project_deps = [
			d
			for d in dependencies
			if d.parent in task_names and d.depends_on_task in task_names
		]
		data.extend(_compute_cpm_for_project(project_tasks, project_deps, project_name))
	columns = _columns()
	chart = auto_chart_for_columns(data, columns)
	return columns, data, None, chart


def _columns():
	return [
		{"label": _("Task"), "fieldname": "name", "fieldtype": "Link", "options": "PM WBS Task", "width": 180},
		{"label": _("Project Contract"), "fieldname": "project", "fieldtype": "Link", "options": "Project Contract", "width": 180},
		{"label": _("Task Name"), "fieldname": "task_name", "fieldtype": "Data", "width": 220},
		{"label": _("Duration (Days)"), "fieldname": "duration_days", "fieldtype": "Int", "width": 120},
		{"label": _("ES"), "fieldname": "es", "fieldtype": "Int", "width": 70},
		{"label": _("EF"), "fieldname": "ef", "fieldtype": "Int", "width": 70},
		{"label": _("LS"), "fieldname": "ls", "fieldtype": "Int", "width": 70},
		{"label": _("LF"), "fieldname": "lf", "fieldtype": "Int", "width": 70},
		{"label": _("Total Float"), "fieldname": "total_float", "fieldtype": "Int", "width": 90},
		{"label": _("Gantt Marker"), "fieldname": "gantt_marker", "fieldtype": "Data", "width": 100},
		{"label": _("CPM Flag"), "fieldname": "cpm_flag", "fieldtype": "Data", "width": 100},
	]
