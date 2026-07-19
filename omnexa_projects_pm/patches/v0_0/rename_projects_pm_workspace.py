# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe


def execute():
	"""Legacy: rename \"Projects PM\" -> projects-pm. Final route /app/projects applied by rename_workspace_projects_pm_route_to_projects."""
	if frappe.db.exists("Workspace", "projects-pm"):
		return
	if not frappe.db.exists("Workspace", "Projects PM"):
		return
	frappe.rename_doc("Workspace", "Projects PM", "projects-pm", force=True)
	frappe.db.sql(
		"UPDATE `tabUser` SET `default_workspace` = %s WHERE IFNULL(`default_workspace`, '') = %s",
		("projects-pm", "Projects PM"),
	)
