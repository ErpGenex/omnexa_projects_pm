# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""Aggregate risk register — ISO 31000 / programme risk visibility."""

import frappe
from frappe import _
from omnexa_core.omnexa_core.branch_access import get_allowed_branches


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.get("company"):
		frappe.throw(_("Company is required."), title=_("Filters"))

	conditions = ["r.company = %(company)s"]
	if filters.get("branch"):
		conditions.append("r.branch = %(branch)s")
	if filters.get("project"):
		conditions.append("r.project = %(project)s")

	allowed = get_allowed_branches(company=filters.company)
	if allowed is not None:
		if not allowed:
			return _columns(), []
		filters.allowed_branches = tuple(allowed)
		conditions.append("r.branch in %(allowed_branches)s")

	data = frappe.db.sql(
		f"""
		SELECT
			r.project,
			r.branch,
			r.status,
			r.category,
			COUNT(*) AS risk_count,
			COALESCE(AVG(r.risk_score), 0) AS avg_risk_score
		FROM `tabRisk Register` r
		WHERE {' AND '.join(conditions)}
		GROUP BY r.project, r.branch, r.status, r.category
		ORDER BY r.project, r.status, r.category
		""",
		filters,
		as_dict=True,
	)
	for row in data:
		row["avg_risk_score"] = round(float(row.avg_risk_score or 0), 2)

	return _columns(), data


def _columns():
	return [
		{"label": _("Project Contract"), "fieldname": "project", "fieldtype": "Link", "options": "Project Contract", "width": 170},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 130},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
		{"label": _("Category"), "fieldname": "category", "fieldtype": "Data", "width": 120},
		{"label": _("Risks"), "fieldname": "risk_count", "fieldtype": "Int", "width": 80},
		{"label": _("Avg risk score"), "fieldname": "avg_risk_score", "fieldtype": "Float", "width": 110},
	]
