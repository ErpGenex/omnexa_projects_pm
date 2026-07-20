# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Unified PM quality view over Construction QHSE registers."""

from __future__ import annotations

import frappe
from frappe.utils import flt


@frappe.whitelist()
def get_project_quality_summary(project_contract: str | None = None, company: str | None = None) -> dict:
	"""Aggregate NCR, inspection requests, and ITP for PM portfolio reporting."""
	summary = {
		"open_ncrs": 0,
		"critical_ncrs": 0,
		"open_inspections": 0,
		"failed_inspections": 0,
		"active_itps": 0,
		"quality_score": 100.0,
		"projects": [],
		"source": "omnexa_projects_pm"
	}

	if project_contract:
		return _project_quality(project_contract)

	if not company:
		frappe.throw(frappe._("Company or Project Contract is required"))

	contracts = frappe.get_all(
		"Project Contract",
		filters={"company": company, "docstatus": ["<", 2]},
		pluck="name",
		limit_page_length=200,
	)
	for name in contracts:
		row = _project_quality(name)
		summary["open_ncrs"] += row["open_ncrs"]
		summary["critical_ncrs"] += row["critical_ncrs"]
		summary["open_inspections"] += row["open_inspections"]
		summary["failed_inspections"] += row["failed_inspections"]
		summary["active_itps"] += row["active_itps"]
		summary["projects"].append(row)

	penalty = summary["critical_ncrs"] * 8 + summary["open_ncrs"] * 3 + summary["failed_inspections"] * 5
	summary["quality_score"] = round(max(0.0, 100.0 - penalty), 1)
	return summary


def _project_quality(project_contract: str) -> dict:
	out = {
		"project_contract": project_contract,
		"open_ncrs": 0,
		"critical_ncrs": 0,
		"open_inspections": 0,
		"failed_inspections": 0,
		"active_itps": 0,
		"quality_score": 100.0
	}
	if frappe.db.exists("DocType", "Construction NCR"):
		out["open_ncrs"] = frappe.db.count(
			"Construction NCR",
			{"project_contract": project_contract, "status": ["in", ["Open", "Under Review"]]},
		)
		out["critical_ncrs"] = frappe.db.count(
			"Construction NCR",
			{"project_contract": project_contract, "severity": "Critical", "status": ["!=", "Closed"]},
		)
	if frappe.db.exists("DocType", "Construction Inspection Request"):
		out["open_inspections"] = frappe.db.count(
			"Construction Inspection Request",
			{
				"project_contract": project_contract,
				"status": ["in", ["Draft", "Scheduled", "In Progress"]]},
		)
		out["failed_inspections"] = frappe.db.count(
			"Construction Inspection Request",
			{"project_contract": project_contract, "status": "Failed"
	},
		)
	if frappe.db.exists("DocType", "Construction Inspection Test Plan"):
		out["active_itps"] = frappe.db.count(
			"Construction Inspection Test Plan",
			{"project_contract": project_contract, "status": "Active"
	},
		)
	penalty = out["critical_ncrs"] * 8 + out["open_ncrs"] * 3 + out["failed_inspections"] * 5
	out["quality_score"] = round(max(0.0, 100.0 - penalty), 1)
	return out


@frappe.whitelist()
def get_portfolio_quality_kpis(company: str, branch: str | None = None) -> dict:
	filters = {"company": company, "docstatus": ["<", 2]}
	if branch:
		filters["branch"] = branch
	contracts = frappe.get_all("Project Contract", filters=filters, pluck="name", limit_page_length=200)
	rows = [_project_quality(name) for name in contracts]
	agg = {
		"contract_count": len(rows),
		"open_ncrs": sum(r["open_ncrs"] for r in rows),
		"critical_ncrs": sum(r["critical_ncrs"] for r in rows),
		"open_inspections": sum(r["open_inspections"] for r in rows),
		"failed_inspections": sum(r["failed_inspections"] for r in rows),
		"active_itps": sum(r["active_itps"] for r in rows),
		"avg_quality_score": round(sum(r["quality_score"] for r in rows) / len(rows), 1) if rows else 100.0,
		"projects": rows
	}
	return agg
