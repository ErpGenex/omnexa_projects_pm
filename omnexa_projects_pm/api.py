from __future__ import annotations

import frappe
from frappe.utils import add_days, getdate

from omnexa_projects_pm.omnexa_projects_pm.report.pm_cpm_groundwork.pm_cpm_groundwork import _compute_cpm_for_project


@frappe.whitelist()
def cpm_timeline(project: str | None = None):
	task_filters = {"docstatus": ["<", 2]}
	if project:
		task_filters["project"] = project
	tasks = frappe.get_all(
		"PM WBS Task",
		fields=["name", "project", "task_name", "planned_start", "planned_end", "status"],
		filters=task_filters,
		limit_page_length=5000,
	)
	if not tasks:
		return {"items": []}

	dependencies = frappe.get_all(
		"PM Task Dependency",
		fields=["parent", "depends_on_task", "dependency_type", "lag_days"],
		limit_page_length=10000,
	)

	by_project = {}
	for t in tasks:
		by_project.setdefault(t.project, []).append(t)

	items = []
	for project_name, project_tasks in by_project.items():
		task_names = {t.name for t in project_tasks}
		project_deps = [d for d in dependencies if d.parent in task_names and d.depends_on_task in task_names]
		cpm_rows = _compute_cpm_for_project(project_tasks, project_deps, project_name)
		for r in cpm_rows:
			items.append(
				{
					"id": r["name"],
					"project": r["project"],
					"title": r["task_name"],
					"start_offset": r["es"],
					"end_offset": r["ef"],
					"float_days": r["total_float"],
					"is_critical": r["cpm_flag"] == "Critical",
					"marker": r.get("gantt_marker") or "",
				}
			)

	items.sort(key=lambda x: (x["project"] or "", x["start_offset"], x["id"]))
	return {"items": items}


@frappe.whitelist()
def cpm_timeline_calendar(project: str | None = None):
	offset_data = cpm_timeline(project=project)
	items = offset_data.get("items", [])
	if not items:
		return {"items": []}

	base_dates = _project_base_dates(project)
	out = []
	for row in items:
		base = base_dates.get(row["project"])
		if not base:
			continue
		start_date = add_days(base, row["start_offset"])
		# end_offset is EF style, so subtract one day for inclusive end date.
		end_date = add_days(base, max(0, row["end_offset"] - 1))
		out.append(
			{
				**row,
				"base_date": str(base),
				"start_date": str(start_date),
				"end_date": str(end_date),
			}
		)
	return {"items": out}


def _project_base_dates(project: str | None = None) -> dict[str, object]:
	base_dates = {}

	baseline_filters = {"docstatus": ["<", 2]}
	if project:
		baseline_filters["project"] = project
	for row in frappe.get_all(
		"PM Baseline Snapshot",
		fields=["project", "baseline_date"],
		filters=baseline_filters,
		order_by="baseline_date asc",
		limit_page_length=5000,
	):
		if row.project and row.project not in base_dates and row.baseline_date:
			base_dates[row.project] = getdate(row.baseline_date)

	task_filters = {"docstatus": ["<", 2]}
	if project:
		task_filters["project"] = project
	for row in frappe.get_all(
		"PM WBS Task",
		fields=["project", "planned_start"],
		filters=task_filters,
		order_by="planned_start asc",
		limit_page_length=5000,
	):
		if row.project and row.project not in base_dates and row.planned_start:
			base_dates[row.project] = getdate(row.planned_start)

	return base_dates

