# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Program entity API — ISO 21500 portfolio/program prioritization."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from omnexa_projects_pm.evm import compute_evm_for_project


@frappe.whitelist()
def get_program_portfolio(company: str, branch: str | None = None) -> dict:
	"""Programs with prioritized project list and rolled-up KPIs."""
	if not company:
		frappe.throw(_("Company is required"))

	if not frappe.db.exists("DocType", "PM Program"):
		return {"programs": [], "unassigned_projects": _unassigned_projects(company, branch)}

	filters: dict = {"company": company, "status": ["!=", "Closed"], "docstatus": ["<", 2]}
	if branch:
		filters["branch"] = branch

	programs = frappe.get_all(
		"PM Program",
		filters=filters,
		fields=["name", "program_title", "portfolio_priority", "status", "program_manager"],
		order_by="portfolio_priority asc, modified desc",
		limit_page_length=100,
	)
	assigned: set[str] = set()
	out_programs = []

	for prog in programs:
		doc = frappe.get_doc("PM Program", prog.name)
		projects = []
		for line in sorted(doc.projects or [], key=lambda r: (flt(r.priority_rank) or 999, -flt(r.strategic_score))):
			if not line.project_contract:
				continue
			assigned.add(line.project_contract)
			evm = compute_evm_for_project(line.project_contract)
			projects.append(
				{
					"project_contract": line.project_contract,
					"priority_rank": flt(line.priority_rank),
					"strategic_score": flt(line.strategic_score),
					"weight": flt(line.weight),
					"spi": evm.get("spi"),
					"cpi": evm.get("cpi"),
					"schedule_health": evm.get("schedule_health_status"),
				}
			)
		out_programs.append(
			{
				"name": prog.name,
				"program_title": prog.program_title,
				"portfolio_priority": prog.portfolio_priority,
				"status": prog.status,
				"program_manager": prog.program_manager,
				"project_count": len(projects),
				"projects": projects,
			}
		)

	return {
		"programs": out_programs,
		"unassigned_projects": _unassigned_projects(company, branch, exclude=assigned),
		"program_count": len(out_programs),
	}


def _unassigned_projects(company: str, branch: str | None = None, exclude: set[str] | None = None) -> list[dict]:
	filters: dict = {"company": company, "docstatus": ["<", 2]}
	if branch:
		filters["branch"] = branch
	rows = frappe.get_all(
		"Project Contract",
		filters=filters,
		fields=["name", "contract_title", "status", "contract_value"],
		limit_page_length=200,
	)
	exclude = exclude or set()
	return [r for r in rows if r.name not in exclude]


@frappe.whitelist()
def prioritize_portfolio(company: str, branch: str | None = None) -> list[dict]:
	"""Flat prioritized project list across programs (lower rank = higher priority)."""
	data = get_program_portfolio(company, branch)
	flat: list[dict] = []
	for prog in data.get("programs", []):
		for p in prog.get("projects", []):
			flat.append(
				{
					**p,
					"program": prog["name"],
					"program_title": prog["program_title"],
					"program_priority": prog.get("portfolio_priority"),
					"composite_rank": flt(prog.get("portfolio_priority")) * 1000 + flt(p.get("priority_rank")),
				}
			)
	for row in data.get("unassigned_projects", []):
		flat.append(
			{
				"project_contract": row["name"],
				"program": None,
				"program_title": _("Unassigned"),
				"composite_rank": 999999,
			}
		)
	flat.sort(key=lambda r: r.get("composite_rank", 999999))
	return flat
