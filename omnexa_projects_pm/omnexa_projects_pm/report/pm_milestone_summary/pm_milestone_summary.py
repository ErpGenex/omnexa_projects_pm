# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.utils import flt
from omnexa_core.omnexa_core.branch_access import get_allowed_branches


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.get("company"):
		frappe.throw(_("Company is required."), title=_("Filters"))

	conditions = ["m.company = %(company)s"]
	if filters.get("branch"):
		conditions.append("m.branch = %(branch)s")
	if filters.get("project"):
		conditions.append("m.project = %(project)s")

	allowed = get_allowed_branches(company=filters.company)
	if allowed is not None:
		if not allowed:
			return _columns(), []
		filters.allowed_branches = tuple(allowed)
		conditions.append("m.branch in %(allowed_branches)s")

	data = frappe.db.sql(
		f"""
		SELECT
			m.project,
			m.branch,
			m.status,
			COUNT(*) AS milestone_count,
			COALESCE(AVG(m.weight_percent), 0) AS avg_weight_pct
		FROM `tabPM Milestone` m
		WHERE {' AND '.join(conditions)}
		GROUP BY m.project, m.branch, m.status
		ORDER BY m.project, m.status
		""",
		filters,
		as_dict=True,
	)
	for row in data:
		row["avg_weight_pct"] = flt(row.avg_weight_pct, 2)

	return _columns(), data


def _columns():
	return [
		{"label": _("Project Contract"), "fieldname": "project", "fieldtype": "Link", "options": "Project Contract", "width": 170},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 130},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
		{"label": _("Milestones"), "fieldname": "milestone_count", "fieldtype": "Int", "width": 100},
		{"label": _("Avg weight %"), "fieldname": "avg_weight_pct", "fieldtype": "Float", "width": 110},
	]
