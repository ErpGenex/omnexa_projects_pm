# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt
"""Earned value metrics from WBS tasks (PMBOK-style roll-up, task level)."""

from __future__ import annotations

from datetime import date
from typing import Any

import frappe
from frappe.utils import date_diff, flt, getdate


def planned_percent_complete(as_of: str | date, planned_start, planned_end) -> float:
	"""Share of task duration elapsed by as_of (0..1). No dates => 0."""
	if not (planned_start and planned_end):
		return 0.0
	as_of_d = getdate(as_of)
	start_d = getdate(planned_start)
	end_d = getdate(planned_end)
	if as_of_d < start_d:
		return 0.0
	if as_of_d >= end_d:
		return 1.0
	total = date_diff(end_d, start_d) + 1
	elapsed = date_diff(as_of_d, start_d) + 1
	return max(0.0, min(1.0, float(elapsed) / float(total)))


def compute_evm_for_project(project_contract: str, as_of_date: str | date | None = None) -> dict[str, Any]:
	"""
	Roll up from **PM WBS Task** for one Project Contract:

	- **BAC** (budget at completion): sum of planned_cost
	- **EV** (earned value): sum of planned_cost × (progress_percent / 100)
	- **AC** (actual cost): sum of actual_cost
	- **PV** (planned value): sum of planned_cost × time-based planned % complete (from planned dates)

	Does not yet pull accounting GL; AC is task-entered actuals only.
	"""
	if not project_contract:
		return {"bac": 0.0, "pv": 0.0, "ev": 0.0, "ac": 0.0}
	as_of = as_of_date or frappe.utils.nowdate()
	tasks = frappe.get_all(
		"PM WBS Task",
		filters={"project": project_contract, "docstatus": ["<", 2]},
		fields=["planned_cost", "actual_cost", "progress_percent", "planned_start", "planned_end"],
	)
	bac = 0.0
	ev = 0.0
	ac = 0.0
	pv = 0.0
	for t in tasks:
		pc = flt(t.get("planned_cost"))
		bac += pc
		ev += pc * flt(t.get("progress_percent")) / 100.0
		ac += flt(t.get("actual_cost"))
		pv += pc * planned_percent_complete(as_of, t.get("planned_start"), t.get("planned_end"))
	return {"bac": round(bac, 2), "pv": round(pv, 2), "ev": round(ev, 2), "ac": round(ac, 2)}
