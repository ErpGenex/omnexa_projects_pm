# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt


def validate_linked_pm_wbs_task(project: str | None, pm_wbs_task: str | None, label: str | None = None) -> None:
	"""Ensure an optional PM WBS Task belongs to the same Project Contract as the parent document."""
	if not pm_wbs_task:
		return
	if not project:
		frappe.throw(
			_("Set {0} before linking a PM WBS Task.").format(_("Project Contract")),
			title=_("Schedule link"),
		)
	task_project = frappe.db.get_value("PM WBS Task", pm_wbs_task, "project")
	if task_project != project:
		frappe.throw(
			_("{0} belongs to a different Project Contract.").format(_(label or "PM WBS Task")),
			title=_("Schedule link"),
		)


def weighted_boq_completion_percent(rows: list[dict]) -> float:
	"""Blend BOQ line completion % using planned_cost as weight (fallback weight 1 when cost is zero)."""
	if not rows:
		return 0.0
	acc = 0.0
	total_w = 0.0
	for row in rows:
		p = flt(row.get("completion_percent"))
		w = flt(row.get("planned_cost"))
		if w <= 0:
			w = 1.0
		acc += p * w
		total_w += w
	if not total_w:
		return 0.0
	return max(0.0, min(100.0, acc / total_w))


def recompute_pm_wbs_progress_from_boq(
	pm_wbs_task: str | None,
	*,
	exclude_boq: str | None = None,
) -> None:
	"""Set PM WBS Task progress from all linked BOQ Items (weighted by planned cost)."""
	if not pm_wbs_task or getattr(frappe.flags, "in_import", False):
		return
	filters = [
		["pm_wbs_task", "=", pm_wbs_task],
		["docstatus", "!=", 2],
	]
	if exclude_boq:
		filters.append(["name", "!=", exclude_boq])
	# Use db.get_all so aggregation is not skewed by the saving user's row-level permissions.
	lines = frappe.db.get_all(
		"BOQ Item",
		filters=filters,
		fields=["completion_percent", "planned_cost"],
	)
	new_pct = weighted_boq_completion_percent(lines)
	frappe.db.set_value(
		"PM WBS Task",
		pm_wbs_task,
		"progress_percent",
		round(new_pct, 2),
	)
