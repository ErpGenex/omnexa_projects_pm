# Copyright (c) 2026, Omnexa

import frappe


def execute() -> None:
	if not frappe.db.exists("Workspace", "projects"):
		return
	from omnexa_projects_pm.workspace.projects_workspace import sync_projects_workspace_menu

	sync_projects_workspace_menu(save=True, rebuild=True)
