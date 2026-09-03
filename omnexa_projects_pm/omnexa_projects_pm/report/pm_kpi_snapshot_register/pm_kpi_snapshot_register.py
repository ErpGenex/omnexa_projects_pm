# Copyright (c) 2026, ErpGenEx
# Auto-generated Global Excellence report pack

import frappe
from frappe import _


def execute(filters=None):
	data = frappe.db.sql(
		"""
		SELECT `name`, `project`, `snapshot_date`, `schedule_health_status`, `company`, `branch`
		FROM `tabPM KPI Snapshot`
		ORDER BY modified DESC
		LIMIT 500
		""",
		as_dict=True,
	)
	columns = [
		{"label": _("Name"), "fieldname": "name", "fieldtype": "Link", "width": 140},
		{"label": _("Project Contract"), "fieldname": "project", "fieldtype": "Link", "width": 120},
		{"label": _("Snapshot Date"), "fieldname": "snapshot_date", "fieldtype": "Date", "width": 120},
		{"label": _("Schedule Health"), "fieldname": "schedule_health_status", "fieldtype": "Select", "width": 120},
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "width": 120},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "width": 120}
	]
	return columns, data
