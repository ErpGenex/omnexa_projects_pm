# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from omnexa_core.omnexa_core.branch_access import get_allowed_branches


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.get("company"):
		frappe.throw(_("Company is required."), title=_("Filters"))

	conditions = ["i.company = %(company)s"]
	if filters.get("branch"):
		conditions.append("i.branch = %(branch)s")
	if filters.get("project"):
		conditions.append("i.project = %(project)s")

	allowed = get_allowed_branches(company=filters.company)
	if allowed is not None:
		if not allowed:
			return _columns(), []
		filters.allowed_branches = tuple(allowed)
		conditions.append("i.branch in %(allowed_branches)s")

	data = frappe.db.sql(
		f"""
		SELECT
			i.project,
			i.branch,
			i.severity,
			i.status,
			COUNT(*) AS issue_count
		FROM `tabPM Issue Log` i
		WHERE {' AND '.join(conditions)}
		GROUP BY i.project, i.branch, i.severity, i.status
		ORDER BY i.project, i.severity, i.status
		""",
		filters,
		as_dict=True,
	)

	return _columns(), data


def _columns():
	return [
		{"label": _("Project Contract"), "fieldname": "project", "fieldtype": "Link", "options": "Project Contract", "width": 170},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 130},
		{"label": _("Severity"), "fieldname": "severity", "fieldtype": "Data", "width": 100},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 110},
		{"label": _("Issues"), "fieldname": "issue_count", "fieldtype": "Int", "width": 90},
	]
