# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe


def execute():
	"""Remove legacy Workspace named \"Projects\" (/app/projects) — duplicate of omnexa_projects_pm workspace; often empty on sites without ERPNext Project."""
	if not frappe.db.exists("Workspace", "Projects"):
		return
	frappe.db.sql(
		"UPDATE `tabUser` SET `default_workspace` = %s WHERE IFNULL(`default_workspace`, '') = %s",
		("projects-pm", "Projects"),
	)
	frappe.delete_doc("Workspace", "Projects", force=True, ignore_permissions=True)
