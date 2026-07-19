from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, getdate


@frappe.whitelist()
def sync_wbs_from_boq(project_contract: str, *, chain_dependencies: int = 1) -> dict:
	"""Create/update PM WBS tasks from BOQ lines and optional FS dependency chain."""
	if not project_contract or not frappe.db.exists("Project Contract", project_contract):
		frappe.throw(_("Project Contract is required."), title=_("WBS Sync"))

	contract = frappe.get_doc("Project Contract", project_contract)
	start = getdate(contract.planned_start or getdate())
	end = getdate(contract.planned_completion or add_days(start, 180))
	span = max(1, (end - start).days)

	boq_rows = frappe.get_all(
		"BOQ Item",
		filters={"project_contract": project_contract, "is_group": 0, "docstatus": ["<", 2]},
		fields=[
			"name",
			"item_description",
			"cost_code",
			"planned_cost",
			"pm_wbs_task",
			"planned_start_date",
			"planned_completion_date",
			"construction_phase",
		],
		order_by="cost_code asc, name asc",
		limit_page_length=5000,
	)

	created = updated = linked = 0
	task_names: list[str] = []
	n = len(boq_rows) or 1

	for i, row in enumerate(boq_rows):
		if row.pm_wbs_task and frappe.db.exists("PM WBS Task", row.pm_wbs_task):
			task_name = row.pm_wbs_task
			frappe.db.set_value(
				"PM WBS Task",
				task_name,
				{"cost_code": row.cost_code, "boq_item": row.name},
				update_modified=False,
			)
			updated += 1
		else:
			offset_start = int(span * i / n)
			offset_end = max(offset_start + 7, int(span * (i + 1) / n))
			p_start = getdate(row.planned_start_date) if row.planned_start_date else add_days(start, offset_start)
			p_end = getdate(row.planned_completion_date) if row.planned_completion_date else add_days(start, min(offset_end, span))
			if p_end < p_start:
				p_end = add_days(p_start, 7)
			task = frappe.get_doc(
				{
					"doctype": "PM WBS Task",
					"project": project_contract,
					"task_name": (row.item_description or row.cost_code or row.name)[:140],
					"cost_code": row.cost_code,
					"boq_item": row.name,
					"planned_start": p_start,
					"planned_end": p_end,
					"planned_cost": flt(row.planned_cost),
					"sequence_no": (i + 1) * 10,
					"status": "Planned",
					"company": contract.company,
					"branch": contract.branch,
				}
			)
			task.insert(ignore_permissions=True)
			task_name = task.name
			created += 1
			frappe.db.set_value("BOQ Item", row.name, "pm_wbs_task", task_name, update_modified=False)
			linked += 1

		task_names.append(task_name)

	if cint(chain_dependencies) and len(task_names) > 1:
		_chain_fs_dependencies(task_names)

	if not contract.primary_wbs_task and task_names:
		frappe.db.set_value("Project Contract", project_contract, "primary_wbs_task", task_names[0])

	return {
		"created": created,
		"updated": updated,
		"linked": linked,
		"tasks": len(task_names),
	}


def _chain_fs_dependencies(task_names: list[str]) -> None:
	for i in range(1, len(task_names)):
		parent = task_names[i]
		pred = task_names[i - 1]
		existing = frappe.db.exists(
			"PM Task Dependency",
			{"parent": parent, "depends_on_task": pred, "dependency_type": "FS"},
		)
		if existing:
			continue
		task = frappe.get_doc("PM WBS Task", parent)
		task.append(
			"dependencies",
			{"dependency_type": "FS", "depends_on_task": pred, "lag_days": 0},
		)
		task.flags.ignore_permissions = True
		task.save()