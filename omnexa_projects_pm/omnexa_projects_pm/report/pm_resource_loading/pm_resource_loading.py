# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	filters = filters or {}
	project = filters.get("project")

	columns = [
		{"label": _("Project Contract"), "fieldname": "project", "fieldtype": "Link", "options": "Project Contract", "width": 140},
		{"label": _("WBS Task"), "fieldname": "pm_wbs_task", "fieldtype": "Link", "options": "PM WBS Task", "width": 130},
		{"label": _("Type"), "fieldname": "resource_type", "fieldtype": "Data", "width": 90},
		{"label": _("User"), "fieldname": "user", "fieldtype": "Link", "options": "User", "width": 120},
		{"label": _("Resource"), "fieldname": "resource_label", "fieldtype": "Data", "width": 160},
		{"label": _("From"), "fieldname": "from_date", "fieldtype": "Date", "width": 100},
		{"label": _("To"), "fieldname": "to_date", "fieldtype": "Date", "width": 100},
		{"label": _("Planned h"), "fieldname": "planned_hours", "fieldtype": "Float", "width": 90},
		{"label": _("Actual h"), "fieldname": "actual_hours", "fieldtype": "Float", "width": 90},
		{"label": _("Actual / Planned %"), "fieldname": "utilization_pct", "fieldtype": "Percent", "width": 110},
	]

	assignment_filters = {}
	if project:
		assignment_filters["project"] = project

	rows = frappe.get_all(
		"PM Resource Assignment",
		filters=assignment_filters,
		fields=[
			"name",
			"project",
			"pm_wbs_task",
			"resource_type",
			"user",
			"resource_label",
			"from_date",
			"to_date",
			"planned_hours",
			"actual_hours",
		],
		order_by="project asc, from_date asc, resource_type asc",
		limit_page_length=500,
	)

	for r in rows:
		ph = flt(r.get("planned_hours"))
		ah = flt(r.get("actual_hours"))
		r["utilization_pct"] = (ah / ph * 100.0) if ph else 0.0

	return columns, rows
