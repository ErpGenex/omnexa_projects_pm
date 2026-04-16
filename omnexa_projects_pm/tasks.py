import frappe
from frappe.utils import nowdate

from omnexa_projects_pm.evm import compute_evm_for_project


def capture_daily_kpi_snapshot():
	projects = frappe.get_all("Project Contract", fields=["name", "company", "branch"], limit_page_length=200)
	today = nowdate()
	for p in projects:
		if frappe.db.exists("PM KPI Snapshot", {"project": p.name, "snapshot_date": today}):
			continue
		evm = compute_evm_for_project(p.name, today)
		doc = frappe.new_doc("PM KPI Snapshot")
		doc.project = p.name
		doc.snapshot_date = today
		doc.pv = evm["pv"]
		doc.ev = evm["ev"]
		doc.ac = evm["ac"]
		doc.company = p.company
		doc.branch = p.branch
		doc.insert(ignore_permissions=True)

