import frappe
from frappe.utils import nowdate

from omnexa_projects_pm.evm import compute_evm_for_project


def capture_daily_kpi_snapshot():
	"""Daily job: PM KPI Snapshot per active Project Contract (ISO 21500 performance measurement)."""
	if not frappe.db.exists("DocType", "Project Contract"):
		return
	projects = frappe.get_all(
		"Project Contract",
		filters={"status": ["in", ["Active", "Draft"]], "docstatus": ["<", 2]},
		fields=["name", "company", "branch"],
		limit_page_length=500,
	)
	today = nowdate()
	for p in projects:
		if frappe.db.exists("PM KPI Snapshot", {"project": p.name, "snapshot_date": today}):
			continue
		evm = compute_evm_for_project(p.name, today, sync_gl_ac=True)
		doc = frappe.new_doc("PM KPI Snapshot")
		doc.project = p.name
		doc.snapshot_date = today
		doc.company = p.company
		doc.branch = p.branch
		for key, value in evm.items():
			if hasattr(doc, key):
				setattr(doc, key, value)
		doc.insert(ignore_permissions=True)
