# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""Earned value / KPI snapshot rollup — PMBOK EVM control account visibility."""

import frappe
from frappe import _
from frappe.utils import flt
from omnexa_core.omnexa_core.branch_access import get_allowed_branches


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.get("company"):
		frappe.throw(_("Company is required."), title=_("Filters"))

	conditions = ["k.company = %(company)s"]
	if filters.get("branch"):
		conditions.append("k.branch = %(branch)s")
	if filters.get("project"):
		conditions.append("k.project = %(project)s")

	allowed = get_allowed_branches(company=filters.company)
	if allowed is not None:
		if not allowed:
			return _columns(), []
		filters.allowed_branches = tuple(allowed)
		conditions.append("k.branch in %(allowed_branches)s")

	data = frappe.db.sql(
		f"""
		SELECT
			k.project,
			k.branch,
			COUNT(*) AS snapshot_count,
			COALESCE(AVG(k.spi), 0) AS avg_spi,
			COALESCE(AVG(k.cpi), 0) AS avg_cpi,
			COALESCE(SUM(k.pv), 0) AS sum_pv,
			COALESCE(SUM(k.ev), 0) AS sum_ev,
			COALESCE(SUM(k.ac), 0) AS sum_ac
		FROM `tabPM KPI Snapshot` k
		WHERE {' AND '.join(conditions)}
		GROUP BY k.project, k.branch
		ORDER BY k.project
		""",
		filters,
		as_dict=True,
	)
	for row in data:
		row["avg_spi"] = flt(row.avg_spi, 3)
		row["avg_cpi"] = flt(row.avg_cpi, 3)
		row["sum_pv"] = flt(row.sum_pv, 2)
		row["sum_ev"] = flt(row.sum_ev, 2)
		row["sum_ac"] = flt(row.sum_ac, 2)

	return _columns(), data


def _columns():
	return [
		{"label": _("Project Contract"), "fieldname": "project", "fieldtype": "Link", "options": "Project Contract", "width": 170},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 130},
		{"label": _("Snapshots"), "fieldname": "snapshot_count", "fieldtype": "Int", "width": 90},
		{"label": _("Avg SPI"), "fieldname": "avg_spi", "fieldtype": "Float", "width": 90},
		{"label": _("Avg CPI"), "fieldname": "avg_cpi", "fieldtype": "Float", "width": 90},
		{"label": _("Σ PV"), "fieldname": "sum_pv", "fieldtype": "Currency", "width": 110},
		{"label": _("Σ EV"), "fieldname": "sum_ev", "fieldtype": "Currency", "width": 110},
		{"label": _("Σ AC"), "fieldname": "sum_ac", "fieldtype": "Currency", "width": 110},
	]
