# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt
"""Earned value metrics from WBS tasks (PMBOK / ISO 21500 performance measurement)."""

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


def compute_evm_for_project(
	project_contract: str,
	as_of_date: str | date | None = None,
	*,
	sync_gl_ac: bool = False,
) -> dict[str, Any]:
	"""
	Roll up from **PM WBS Task** for one Project Contract:

	- **BAC** (budget at completion): sum of planned_cost
	- **EV** (earned value): sum of planned_cost × (progress_percent / 100)
	- **AC** (actual cost): GL when posted, else sum of task actual_cost
	- **PV** (planned value): sum of planned_cost × time-based planned % complete
	"""
	if not project_contract:
		return _empty_evm()
	as_of = as_of_date or frappe.utils.nowdate()
	if sync_gl_ac:
		try:
			from omnexa_projects_pm.gl_cost_bridge import sync_gl_actual_cost_to_wbs

			sync_gl_actual_cost_to_wbs(project_contract, str(as_of))
		except Exception:
			frappe.log_error(frappe.get_traceback(), "EVM GL sync failed")

	tasks = frappe.get_all(
		"PM WBS Task",
		filters={"project": project_contract, "docstatus": ["<", 2]},
		fields=["planned_cost", "actual_cost", "progress_percent", "planned_start", "planned_end"],
	)
	bac = 0.0
	ev = 0.0
	pv = 0.0
	for t in tasks:
		pc = flt(t.get("planned_cost"))
		bac += pc
		ev += pc * flt(t.get("progress_percent")) / 100.0
		pv += pc * planned_percent_complete(as_of, t.get("planned_start"), t.get("planned_end"))

	from omnexa_projects_pm.gl_cost_bridge import resolve_project_actual_cost

	ac, ac_source = resolve_project_actual_cost(project_contract, str(as_of))
	result = compute_evm_indices(bac=bac, pv=pv, ev=ev, ac=ac)
	result["ac_source"] = ac_source
	return result


def compute_evm_indices(
	*,
	bac: float,
	pv: float,
	ev: float,
	ac: float,
) -> dict[str, Any]:
	"""PMI-style earned value indices from BAC, PV, EV, AC."""
	bac = flt(bac)
	pv = flt(pv)
	ev = flt(ev)
	ac = flt(ac)

	sv = ev - pv
	cv = ev - ac
	spi = ev / pv if pv else 0.0
	cpi = ev / ac if ac else 0.0

	# EAC (typical): BAC / CPI when CPI > 0, else BAC
	eac = bac / cpi if cpi else bac
	etc = max(0.0, eac - ac)
	vac = bac - eac
	tcpi_bac = (bac - ev) / (bac - ac) if (bac - ac) else 0.0

	return {
		"bac": round(bac, 2),
		"pv": round(pv, 2),
		"ev": round(ev, 2),
		"ac": round(ac, 2),
		"schedule_variance": round(sv, 2),
		"cost_variance": round(cv, 2),
		"spi": round(spi, 4),
		"cpi": round(cpi, 4),
		"estimate_at_completion": round(eac, 2),
		"estimate_to_complete": round(etc, 2),
		"variance_at_completion": round(vac, 2),
		"to_complete_performance_index": round(tcpi_bac, 4),
		"schedule_health_status": _schedule_health(spi),
		"cost_health_status": _cost_health(cpi)
	}


def _schedule_health(spi: float) -> str:
	if spi >= 0.95:
		return "On Track"
	if spi >= 0.85:
		return "At Risk"
	return "Delayed"


def _cost_health(cpi: float) -> str:
	if cpi >= 0.95:
		return "On Budget"
	if cpi >= 0.85:
		return "At Risk"
	return "Over Budget"


def _empty_evm() -> dict[str, Any]:
	return compute_evm_indices(bac=0, pv=0, ev=0, ac=0)
