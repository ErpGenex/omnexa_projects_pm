# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from omnexa_core.omnexa_core.utils.report_charts import auto_chart_for_columns

from omnexa_core.omnexa_core.report_print.report_query_filters import (
	get_all_filters,
	policy_version_filters,
	prepare_filters,
	sql_conditions,
)



def execute(filters=None):
	filters = prepare_filters(filters)
	filters_dict = get_all_filters(filters, "PM Resource Assignment", date_field="creation", company=True, branch=True, extra_links={})
	data = frappe.get_all(
		"PM Resource Assignment",
		fields=['name', 'project', 'pm_wbs_task', 'resource_type', 'user', 'resource_label', 'from_date', 'to_date', 'planned_hours', 'actual_hours'],
		filters=filters_dict,
		limit_page_length=5000,
	)

	return [
		{"label": _("Project Contract"), "fieldname": "project", "fieldtype": "Link", "options": "Project Contract", "width": 140
	},
		{"label": _("WBS Task"), "fieldname": "pm_wbs_task", "fieldtype": "Link", "options": "PM WBS Task", "width": 130
	},
		{"label": _("Type"), "fieldname": "resource_type", "fieldtype": "Data", "width": 90
	},
		{"label": _("User"), "fieldname": "user", "fieldtype": "Link", "options": "User", "width": 120
	},
		{"label": _("Resource"), "fieldname": "resource_label", "fieldtype": "Data", "width": 160
	},
		{"label": _("From"), "fieldname": "from_date", "fieldtype": "Date", "width": 100
	},
		{"label": _("To"), "fieldname": "to_date", "fieldtype": "Date", "width": 100
	},
		{"label": _("Planned h"), "fieldname": "planned_hours", "fieldtype": "Float", "width": 90
	},
		{"label": _("Actual h"), "fieldname": "actual_hours", "fieldtype": "Float", "width": 90
	},
		{"label": _("Actual / Planned %"), "fieldname": "utilization_pct", "fieldtype": "Percent", "width": 110
	},
	], data
