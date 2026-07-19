# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Portfolio dashboard API — ISO 21500 portfolio / program view."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

from omnexa_projects_pm.evm import compute_evm_for_project
from omnexa_projects_pm.program_api import get_program_portfolio
from omnexa_projects_pm.qhse_quality_bridge import get_portfolio_quality_kpis


@frappe.whitelist()
def get_portfolio_dashboard(company: str, branch: str | None = None) -> dict:
	"""Portfolio KPIs from PM WBS EVM (PMBOK). Uses construction EVM when app installed."""
	if not company:
		frappe.throw(_("Company is required"))

	if frappe.db.exists("Module", "Omnexa Construction"):
		try:
			from omnexa_construction.portfolio_api import get_portfolio_dashboard as construction_portfolio

			return construction_portfolio(company, branch)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "PM portfolio: construction bridge failed")

	return _pm_portfolio_dashboard(company, branch)


def _pm_portfolio_dashboard(company: str, branch: str | None = None) -> dict:
	filters: dict = {"company": company, "docstatus": ["<", 2]}
	if branch:
		filters["branch"] = branch

	contracts = frappe.get_all(
		"Project Contract",
		filters=filters,
		fields=["name", "contract_title", "status", "contract_value", "planned_completion"],
		limit_page_length=100,
	)

	total_bac = 0.0
	total_ev = 0.0
	weighted_spi = 0.0
	weight = 0.0
	delayed = at_risk = on_track = 0
	rows = []

	open_issues = 0
	if frappe.db.exists("DocType", "PM Issue Log"):
		open_issues = frappe.db.count(
			"PM Issue Log",
			{"company": company, "status": ["in", ["Open", "In Progress"]], "docstatus": ["<", 2]},
		)
	open_risks = 0
	if frappe.db.exists("DocType", "Risk Register"):
		open_risks = frappe.db.count(
			"Risk Register",
			{"company": company, "status": ["in", ["Open", "Monitoring"]], "docstatus": ["<", 2]},
		)
	open_changes = 0
	if frappe.db.exists("DocType", "PM Change Request"):
		cr_filters = {"company": company, "status": ["in", ["Draft", "Under Review", "Approved"]]}
		if branch:
			cr_filters["branch"] = branch
		open_changes = frappe.db.count("PM Change Request", cr_filters)

	for c in contracts:
		evm = compute_evm_for_project(c.name)
		bac = flt(evm.get("bac")) or flt(c.contract_value)
		total_bac += bac
		total_ev += flt(evm.get("ev"))
		if bac:
			weighted_spi += flt(evm.get("spi")) * bac
			weight += bac
		health = evm.get("schedule_health_status") or "On Track"
		if health == "Delayed":
			delayed += 1
		elif health == "At Risk":
			at_risk += 1
		else:
			on_track += 1
		rows.append(
			{
				"name": c.name,
				"title": c.contract_title,
				"status": c.status,
				"bac": bac,
				"spi": evm.get("spi"),
				"cpi": evm.get("cpi"),
				"schedule_health": health,
				"cost_health": evm.get("cost_health_status"),
			}
		)

	programs = get_program_portfolio(company, branch)
	quality = get_portfolio_quality_kpis(company, branch)

	return {
		"contract_count": len(contracts),
		"total_bac": round(total_bac, 2),
		"total_ev": round(total_ev, 2),
		"portfolio_spi": round(weighted_spi / weight, 4) if weight else 0,
		"delayed_contracts": delayed,
		"at_risk_contracts": at_risk,
		"on_track_contracts": on_track,
		"open_issues": open_issues,
		"open_risks": open_risks,
		"open_change_requests": open_changes,
		"contracts": rows,
		"programs": programs.get("programs", []),
		"program_count": programs.get("program_count", 0),
		"unassigned_projects": programs.get("unassigned_projects", []),
		"quality_kpis": quality,
		"source": "omnexa_projects_pm",
	}
