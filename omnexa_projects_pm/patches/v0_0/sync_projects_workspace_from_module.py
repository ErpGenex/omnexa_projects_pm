# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import json
from pathlib import Path

import frappe


def execute():
	"""Refresh Workspace `projects` label, title, content, and links from module JSON (one-way sync)."""
	if not frappe.db.exists("Workspace", "projects"):
		return
	base = Path(frappe.get_app_path("omnexa_projects_pm"))
	ws_path = base / "omnexa_projects_pm" / "workspace" / "projects" / "projects.json"
	if not ws_path.is_file():
		return
	data = json.loads(ws_path.read_text(encoding="utf-8"))
	if data.get("name") != "projects":
		return
	doc = frappe.get_doc("Workspace", "projects")
	doc.label = data.get("label") or doc.label
	doc.title = data.get("title") or doc.title
	if data.get("content"):
		doc.content = data["content"]
	doc.links = []
	for row in data.get("links") or []:
		doc.append("links", row)
	doc.flags.ignore_links = True
	doc.save(ignore_permissions=True)
