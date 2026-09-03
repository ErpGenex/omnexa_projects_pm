# Copyright (c) 2026, ErpGenEx
# Auto-generated Global Excellence report pack

import frappe
from frappe import _


def execute(filters=None):
	data = frappe.db.sql(
		"""
		SELECT `name`, `project`, `resource_type`, `from_date`, `to_date`, `company`
		FROM `tabPM Resource Assignment`
		ORDER BY modified DESC
		LIMIT 500
		""",
		as_dict=True,
	)
	columns = [
		{"label": _("Name"), "fieldname": "name", "fieldtype": "Link", "width": 140},
		{"label": _("Project Contract"), "fieldname": "project", "fieldtype": "Link", "width": 120},
		{"label": _("Resource Type"), "fieldname": "resource_type", "fieldtype": "Select", "width": 120},
		{"label": _("From Date"), "fieldname": "from_date", "fieldtype": "Date", "width": 120},
		{"label": _("To Date"), "fieldname": "to_date", "fieldtype": "Date", "width": 120},
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "width": 120}
	]
	return columns, data
