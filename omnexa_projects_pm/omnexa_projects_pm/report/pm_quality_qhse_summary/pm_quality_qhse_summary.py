# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe import _

from omnexa_core.omnexa_core.utils.report_charts import auto_chart_for_columns

from omnexa_projects_pm.qhse_quality_bridge import _project_quality


def execute(filters=None):
	filters = filters or {}
	company = filters.get("company")
	if not company:
		frappe.throw(_("Company is required"))

	contract_filters = {"company": company, "docstatus": ["<", 2]}
	if filters.get("branch"):
		contract_filters["branch"] = filters.get("branch")
	if filters.get("project_contract"):
		contract_filters["name"] = filters.get("project_contract")

	contracts = frappe.get_all(
		"Project Contract",
		filters=contract_filters,
		fields=["name", "contract_title"],
		limit_page_length=500,
	)
	columns = [
		{"label": _("Project Contract"), "fieldname": "project_contract", "fieldtype": "Link", "options": "Project Contract", "width": 140
	},
		{"label": _("Title"), "fieldname": "contract_title", "fieldtype": "Data", "width": 180
	},
		{"label": _("Open NCRs"), "fieldname": "open_ncrs", "fieldtype": "Int", "width": 90
	},
		{"label": _("Critical NCRs"), "fieldname": "critical_ncrs", "fieldtype": "Int", "width": 100
	},
		{"label": _("Open Inspections"), "fieldname": "open_inspections", "fieldtype": "Int", "width": 120
	},
		{"label": _("Failed Inspections"), "fieldname": "failed_inspections", "fieldtype": "Int", "width": 120
	},
		{"label": _("Active ITPs"), "fieldname": "active_itps", "fieldtype": "Int", "width": 90
	},
		{"label": _("Quality Score"), "fieldname": "quality_score", "fieldtype": "Float", "width": 100
	},
	]
	data = []
	for row in contracts:
		q = _project_quality(row.name)
		data.append(
			{
				"project_contract": row.name,
				"contract_title": row.contract_title,
				**q}
		)
	chart = auto_chart_for_columns(data, columns)
	return columns, data, None, chart