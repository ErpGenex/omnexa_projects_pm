# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe


def execute():
	"""Align Workspace.name with /app/projects (was projects-pm). Update user default_workspace."""
	if frappe.db.exists("Workspace", "projects-pm"):
		if frappe.db.exists("Workspace", "projects"):
			frappe.delete_doc("Workspace", "projects", force=True, ignore_permissions=True)
		frappe.rename_doc("Workspace", "projects-pm", "projects", force=True)
	frappe.db.sql(
		"UPDATE `tabUser` SET `default_workspace` = %s WHERE IFNULL(`default_workspace`, '') IN (%s, %s)",
		("projects", "projects-pm", "Projects PM"),
	)
