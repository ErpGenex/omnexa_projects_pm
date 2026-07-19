# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Unified schedule path: Construction Schedule Baseline ↔ PM WBS Task."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, getdate


def _active_baseline(project_contract: str) -> dict | None:
	active = frappe.db.get_value(
		"Construction Schedule Baseline",
		{"project_contract": project_contract, "is_active": 1, "docstatus": 1},
		["name", "planned_start", "planned_completion"],
		as_dict=True,
	)
	if active:
		return active
	rows = frappe.get_all(
		"Construction Schedule Baseline",
		filters={"project_contract": project_contract, "docstatus": 1},
		fields=["name", "planned_start", "planned_completion"],
		order_by="modified desc",
		limit_page_length=1,
	)
	return rows[0] if rows else None


def _match_wbs_task(project_contract: str, baseline_row: dict, index: dict) -> str | None:
	for key in (
		baseline_row.get("boq_item"),
		baseline_row.get("cost_code"),
		baseline_row.get("task_name"),
	):
		if key and index.get(str(key)):
			return index[str(key)]
	return None


def _wbs_index(project_contract: str) -> dict[str, str]:
	index: dict[str, str] = {}
	for row in frappe.get_all(
		"PM WBS Task",
		filters={"project": project_contract, "docstatus": ["<", 2]},
		fields=["name", "task_name", "cost_code", "boq_item", "schedule_baseline_ref"],
		limit_page_length=5000,
	):
		for key in (row.boq_item, row.cost_code, row.task_name, row.schedule_baseline_ref):
			if key:
				index[str(key)] = row.name
	return index


@frappe.whitelist()
def sync_baseline_to_pm_wbs(project_contract: str, *, chain_dependencies: int = 1) -> dict:
	"""Import active Construction Schedule Baseline tasks into PM WBS."""
	if not project_contract:
		frappe.throw(_("Project Contract is required"))
	if not frappe.db.exists("DocType", "Construction Schedule Baseline"):
		frappe.throw(_("Construction Schedule Baseline is not installed"))

	baseline = _active_baseline(project_contract)
	if not baseline:
		return {"created": 0, "updated": 0, "dependencies": 0, "message": "No submitted baseline"}

	contract = frappe.db.get_value(
		"Project Contract",
		project_contract,
		["company", "branch"],
		as_dict=True,
	)
	fields = [
		"task_name",
		"start_date",
		"end_date",
		"duration_days",
		"boq_item",
		"cost_code",
		"progress_percent",
		"is_milestone",
	]
	meta = frappe.get_meta("Construction Schedule Baseline Task")
	if meta.has_field("predecessor_task"):
		fields.append("predecessor_task")

	rows = frappe.get_all(
		"Construction Schedule Baseline Task",
		filters={"parent": baseline.name},
		fields=fields,
		order_by="idx asc",
		limit_page_length=5000,
	)
	index = _wbs_index(project_contract)
	created = updated = deps = 0
	name_map: dict[str, str] = {}

	for i, row in enumerate(rows):
		task_name = row.task_name
		existing = _match_wbs_task(project_contract, row, index)
		planned_cost = 0.0
		if row.boq_item:
			planned_cost = flt(frappe.db.get_value("BOQ Item", row.boq_item, "planned_cost"))

		payload = {
			"task_name": task_name,
			"planned_start": row.start_date,
			"planned_end": row.end_date,
			"progress_percent": flt(row.progress_percent),
			"cost_code": row.cost_code,
			"boq_item": row.boq_item,
			"schedule_baseline_ref": task_name,
			"planned_cost": planned_cost,
			"sequence_no": (i + 1) * 10,
		}
		if existing:
			frappe.db.set_value("PM WBS Task", existing, payload, update_modified=True)
			wbs_name = existing
			updated += 1
		else:
			doc = frappe.get_doc(
				{
					"doctype": "PM WBS Task",
					"project": project_contract,
					"company": contract.company,
					"branch": contract.branch,
					"status": "Planned",
					**payload,
				}
			)
			doc.insert(ignore_permissions=True)
			wbs_name = doc.name
			created += 1
			if row.boq_item:
				frappe.db.set_value("BOQ Item", row.boq_item, "pm_wbs_task", wbs_name, update_modified=False)

		name_map[task_name] = wbs_name
		index[task_name] = wbs_name

	if int(chain_dependencies):
		for row in rows:
			pred_text = (row.get("predecessor_task") or "").strip()
			if not pred_text or row.task_name not in name_map:
				continue
			for pred_name in [p.strip() for p in pred_text.split(",") if p.strip()]:
				if pred_name not in name_map:
					continue
				_ensure_fs_dependency(name_map[row.task_name], name_map[pred_name])
				deps += 1

	return {
		"baseline": baseline.name,
		"created": created,
		"updated": updated,
		"dependencies": deps,
	}


@frappe.whitelist()
def sync_pm_wbs_to_baseline(project_contract: str) -> dict:
	"""Push PM WBS dates/progress back to active schedule baseline tasks."""
	if not frappe.db.exists("DocType", "Construction Schedule Baseline"):
		frappe.throw(_("Construction Schedule Baseline is not installed"))
	baseline = _active_baseline(project_contract)
	if not baseline:
		return {"updated": 0, "message": "No submitted baseline"}

	tasks = frappe.get_all(
		"PM WBS Task",
		filters={"project": project_contract, "docstatus": ["<", 2]},
		fields=["name", "task_name", "planned_start", "planned_end", "progress_percent", "cost_code", "boq_item", "schedule_baseline_ref"],
		limit_page_length=5000,
	)
	by_ref = {t.schedule_baseline_ref or t.task_name: t for t in tasks}
	rows = frappe.get_all(
		"Construction Schedule Baseline Task",
		filters={"parent": baseline.name},
		fields=["name", "task_name", "boq_item", "cost_code"],
		limit_page_length=5000,
	)
	updated = 0
	for row in rows:
		match = by_ref.get(row.task_name)
		if not match and row.boq_item:
			match = next((t for t in tasks if t.boq_item == row.boq_item), None)
		if not match and row.cost_code:
			match = next((t for t in tasks if t.cost_code == row.cost_code), None)
		if not match:
			continue
		frappe.db.set_value(
			"Construction Schedule Baseline Task",
			row.name,
			{
				"start_date": match.planned_start,
				"end_date": match.planned_end,
				"progress_percent": flt(match.progress_percent),
			},
			update_modified=True,
		)
		updated += 1

	return {"baseline": baseline.name, "updated": updated}


def _ensure_fs_dependency(child: str, parent: str) -> None:
	existing = frappe.db.exists(
		"PM Task Dependency",
		{"parent": child, "depends_on_task": parent, "dependency_type": "FS"},
	)
	if existing:
		return
	task = frappe.get_doc("PM WBS Task", child)
	task.append("dependencies", {"depends_on_task": parent, "dependency_type": "FS", "lag_days": 0})
	task.flags.ignore_permissions = True
	task.save()
