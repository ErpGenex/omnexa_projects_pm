# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Resource leveling — delay non-critical tasks to resolve over-allocation."""

from __future__ import annotations

import frappe
from frappe.utils import add_days, date_diff, flt, getdate

from omnexa_projects_pm.api import cpm_timeline_calendar


@frappe.whitelist()
def detect_resource_overloads(
	project_contract: str,
	*,
	hours_per_day: float = 8.0,
) -> list[dict]:
	"""Return days where a resource exceeds daily capacity."""
	assignments = frappe.get_all(
		"PM Resource Assignment",
		filters={"project": project_contract, "docstatus": ["<", 2]},
		fields=["name", "user", "resource_label", "from_date", "to_date", "planned_hours", "pm_wbs_task"],
		limit_page_length=5000,
	)
	if not assignments:
		return []

	daily_load: dict[tuple[str, str], float] = {}
	for row in assignments:
		resource = row.user or row.resource_label or row.name
		start = getdate(row.from_date) if row.from_date else None
		end = getdate(row.to_date) if row.to_date else start
		if not start:
			continue
		if not end:
			end = start
		days = max(1, date_diff(end, start) + 1)
		per_day = flt(row.planned_hours) / days if row.planned_hours else hours_per_day
		cursor = start
		while cursor <= end:
			key = (resource, str(cursor))
			daily_load[key] = daily_load.get(key, 0.0) + per_day
			cursor = add_days(cursor, 1)

	overloads = []
	for (resource, day), hours in sorted(daily_load.items()):
		if hours > hours_per_day:
			overloads.append(
				{
					"resource": resource,
					"date": day,
					"hours": round(hours, 2),
					"capacity": hours_per_day,
					"overload_hours": round(hours - hours_per_day, 2),
				}
			)
	return overloads


@frappe.whitelist()
def apply_resource_leveling(
	project_contract: str,
	*,
	hours_per_day: float = 8.0,
	max_shifts: int = 50,
) -> dict:
	"""Shift task dates forward to reduce resource overload (greedy, preserves duration)."""
	if not project_contract:
		frappe.throw(frappe._("Project Contract is required"))

	overloads = detect_resource_overloads(project_contract, hours_per_day=hours_per_day)
	if not overloads:
		return {"shifted_tasks": 0, "remaining_overloads": 0, "message": "No overload detected"}

	cpm = {row["id"]: row for row in cpm_timeline_calendar(project_contract).get("items", [])}
	assignments = frappe.get_all(
		"PM Resource Assignment",
		filters={"project": project_contract, "docstatus": ["<", 2]},
		fields=["name", "user", "resource_label", "from_date", "to_date", "planned_hours", "pm_wbs_task"],
		limit_page_length=5000,
	)
	task_ids = {a.pm_wbs_task for a in assignments if a.pm_wbs_task}
	tasks = {
		t.name: t
		for t in frappe.get_all(
			"PM WBS Task",
			filters={"name": ["in", list(task_ids)], "docstatus": ["<", 2]},
			fields=["name", "planned_start", "planned_end", "sequence_no"],
		)
	}

	shifted = 0
	for _ in range(max_shifts):
		overloads = detect_resource_overloads(project_contract, hours_per_day=hours_per_day)
		if not overloads:
			break
		target = overloads[0]
		candidates = [
			a
			for a in assignments
			if (a.user or a.resource_label) == target["resource"]
			and a.from_date
			and str(getdate(a.from_date)) <= target["date"] <= str(getdate(a.to_date or a.from_date))
			and a.pm_wbs_task
		]
		if not candidates:
			break
		candidates.sort(
			key=lambda a: (
				1 if cpm.get(a.pm_wbs_task, {}).get("is_critical") else 0,
				-cpm.get(a.pm_wbs_task, {}).get("float_days", 0),
				tasks.get(a.pm_wbs_task).sequence_no if tasks.get(a.pm_wbs_task) else 0,
			),
		)
		pick = candidates[0]
		task = tasks.get(pick.pm_wbs_task)
		if not task or not task.planned_start or not task.planned_end:
			break
		new_start = add_days(getdate(task.planned_start), 1)
		duration = max(1, date_diff(getdate(task.planned_end), getdate(task.planned_start)))
		new_end = add_days(new_start, duration)
		frappe.db.set_value("PM WBS Task", task.name, "planned_start", new_start, update_modified=False)
		frappe.db.set_value("PM WBS Task", task.name, "planned_end", new_end, update_modified=False)
		task.planned_start = new_start
		task.planned_end = new_end
		if pick.from_date:
			pick.from_date = add_days(getdate(pick.from_date), 1)
			pick.to_date = add_days(getdate(pick.to_date or pick.from_date), 1)
			frappe.db.set_value("PM Resource Assignment", pick.name, "from_date", pick.from_date, update_modified=False)
			frappe.db.set_value("PM Resource Assignment", pick.name, "to_date", pick.to_date, update_modified=False)
		shifted += 1

	remaining = len(detect_resource_overloads(project_contract, hours_per_day=hours_per_day))
	return {
		"shifted_tasks": shifted,
		"remaining_overloads": remaining,
		"hours_per_day": hours_per_day,
	}
