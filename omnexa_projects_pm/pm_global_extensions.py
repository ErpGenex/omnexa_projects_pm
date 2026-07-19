# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""PM global leader extensions — Monte Carlo, stakeholder, change board, P6 XER."""

from __future__ import annotations

import random
import re
from typing import Any

import frappe
from frappe import _
from frappe.utils import getdate


@frappe.whitelist()
def compute_stakeholder_engagement_index(project: str) -> dict:
	"""Stakeholder engagement score (PMBOK) from PM Stakeholder Register."""
	if not project:
		frappe.throw(_("Project is required"))
	rows = frappe.get_all(
		"PM Stakeholder Register",
		filters={"project": project, "docstatus": ["<", 2]},
		fields=["name", "stakeholder_name", "influence", "interest", "engagement_strategy", "status"],
	)
	if not rows:
		return {"project": project, "index": 0, "stakeholders": 0, "rows": []}

	_influence = {"Low": 1, "Medium": 2, "High": 3, "Very High": 4}
	_interest = {"Low": 1, "Medium": 2, "High": 3, "Very High": 4}
	_strategy = {"Monitor": 1, "Keep Informed": 2, "Keep Satisfied": 3, "Manage Closely": 4}
	scores = []
	out_rows = []
	for r in rows:
		inf = _influence.get(r.influence or "Medium", 2)
		int_ = _interest.get(r.interest or "Medium", 2)
		strat = _strategy.get(r.engagement_strategy or "Keep Informed", 2)
		score = round((inf + int_ + strat) / 12 * 100, 1)
		scores.append(score)
		out_rows.append({"name": r.name, "stakeholder": r.stakeholder_name, "score": score, "status": r.status})
	index = round(sum(scores) / len(scores), 1) if scores else 0
	return {"project": project, "index": index, "stakeholders": len(rows), "rows": out_rows}


@frappe.whitelist()
def get_change_control_board_status(company: str | None = None, branch: str | None = None) -> dict:
	"""Change control board pipeline — draft / review / approved / rejected."""
	filters: dict[str, Any] = {"docstatus": ["<", 2]}
	if company:
		filters["company"] = company
	if branch:
		filters["branch"] = branch
	rows = frappe.get_all(
		"PM Change Request",
		filters=filters,
		fields=["name", "project", "status", "change_type", "estimated_cost_impact", "modified"],
		order_by="modified desc",
		limit_page_length=200,
	)
	by_status: dict[str, int] = {}
	for r in rows:
		st = r.status or "Draft"
		by_status[st] = by_status.get(st, 0) + 1
	return {
		"company": company,
		"branch": branch,
		"total": len(rows),
		"by_status": by_status,
		"pending_ccb": by_status.get("Under Review", 0) + by_status.get("Draft", 0),
		"items": rows[:50],
	}


@frappe.whitelist()
def run_monte_carlo_schedule_risk(project: str, iterations: int = 500) -> dict:
	"""Quantitative schedule risk — Monte Carlo on task duration uncertainty."""
	if not project:
		frappe.throw(_("Project is required"))
	iterations = max(100, min(int(iterations or 500), 5000))
	tasks = frappe.get_all(
		"PM WBS Task",
		filters={"project": project, "docstatus": ["<", 2]},
		fields=["name", "task_name", "planned_start", "planned_end", "duration_days"],
		limit_page_length=2000,
	)
	if not tasks:
		return {"project": project, "iterations": 0, "p50_days": 0, "p80_days": 0, "p95_days": 0}

	def _duration(t: dict) -> int:
		if t.get("duration_days"):
			return max(1, int(t["duration_days"]))
		if t.get("planned_start") and t.get("planned_end"):
			return max(1, (getdate(t["planned_end"]) - getdate(t["planned_start"])).days + 1)
		return 5

	base = sum(_duration(t) for t in tasks)
	samples: list[float] = []
	for _ in range(iterations):
		total = 0.0
		for t in tasks:
			d = _duration(t)
			factor = random.triangular(0.85, 1.35, 1.0)
			total += d * factor
		samples.append(total)
	samples.sort()
	n = len(samples)

	def _pct(p: float) -> float:
		idx = min(n - 1, max(0, int(p * n)))
		return round(samples[idx], 1)

	return {
		"project": project,
		"tasks": len(tasks),
		"iterations": iterations,
		"deterministic_days": base,
		"p50_days": _pct(0.50),
		"p80_days": _pct(0.80),
		"p95_days": _pct(0.95),
		"contingency_p80_pct": round((_pct(0.80) - base) / base * 100, 1) if base else 0,
	}


@frappe.whitelist()
def preview_p6_xer_import(xer_content: str) -> dict:
	"""Parse Oracle P6 XER export preview (activities + relationships)."""
	if not xer_content or not str(xer_content).strip():
		frappe.throw(_("XER content is required"))
	text = str(xer_content)
	activities = []
	for line in text.splitlines():
		if line.startswith("%R\tTASK\t") or line.startswith("%R\tACTIVITY\t"):
			parts = line.split("\t")
			if len(parts) >= 4:
				activities.append({"task_id": parts[2], "task_name": parts[3] if len(parts) > 3 else parts[2]})
	relations = []
	for line in text.splitlines():
		if line.startswith("%R\tTASKPRED\t") or line.startswith("%R\tTASKREL\t"):
			parts = line.split("\t")
			if len(parts) >= 5:
				relations.append({"pred": parts[2], "succ": parts[3], "type": parts[4]})
	if not activities:
		for m in re.finditer(r"task_code\s*=\s*['\"]([^'\"]+)['\"]", text, re.I):
			activities.append({"task_id": m.group(1), "task_name": m.group(1)})
	return {
		"activities_found": len(activities),
		"relationships_found": len(relations),
		"sample_activities": activities[:20],
		"sample_relationships": relations[:20],
		"import_ready": len(activities) > 0,
	}
