# Copyright (c) 2026, ErpGenEx
# Auto-generated Global Excellence report pack

import frappe
from frappe import _


def execute(filters=None):
	data = frappe.db.sql(
		"""
		SELECT `name`, `project`, `change_title`, `change_type`, `status`, `company`
		FROM `tabPM Change Request`
		ORDER BY modified DESC
		LIMIT 500
		""",
		as_dict=True,
	)
	columns = [
		{"label": _("Name"), "fieldname": "name", "fieldtype": "Link", "width": 140},
		{"label": _("Project Contract"), "fieldname": "project", "fieldtype": "Link", "width": 120},
		{"label": _("Change Title"), "fieldname": "change_title", "fieldtype": "Data", "width": 120},
		{"label": _("Change Type"), "fieldname": "change_type", "fieldtype": "Select", "width": 120},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Select", "width": 120},
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "width": 120}
	]
	return columns, data
