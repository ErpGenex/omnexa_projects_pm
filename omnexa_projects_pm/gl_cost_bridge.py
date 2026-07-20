# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""GL actual cost bridge for EVM (Journal Entry / Purchase Invoice → PM WBS)."""

from __future__ import annotations

import frappe
from frappe.utils import flt, getdate, today


def get_gl_actual_cost(project_contract: str, as_of_date: str | None = None) -> dict:
	"""Project-level actual cost from accounting GL sources."""
	if not project_contract:
		return {"total": 0.0, "source": "none", "by_cost_code": {}
	}

	as_of = getdate(as_of_date or today())
	company = frappe.db.get_value("Project Contract", project_contract, "company")
	total = 0.0
	source = "none"
	by_cost_code: dict[str, float] = {}

	je_total = _journal_entry_expense_total(project_contract, company, as_of)
	if je_total:
		total = je_total
		source = "journal_entry"

	pi_total = _purchase_invoice_total(project_contract, as_of)
	if pi_total:
		total += pi_total
		source = "journal_entry+purchase_invoice" if source == "journal_entry" else "purchase_invoice"

	try:
		from omnexa_construction.wip_gl import _gl_totals_if_available

		gl_cost, _income = _gl_totals_if_available(project_contract, company, as_of)
		if gl_cost > total:
			total = gl_cost
			source = "construction_gl_bridge"
	except Exception:
		pass

	by_cost_code = _boq_actual_by_cost_code(project_contract)
	if by_cost_code and not total:
		total = sum(by_cost_code.values())
		source = "boq_actual"

	return {
		"total": round(total, 2),
		"source": source,
		"by_cost_code": {k: round(v, 2) for k, v in by_cost_code.items()},
		"as_of": str(as_of)
	}


def resolve_project_actual_cost(project_contract: str, as_of_date: str | None = None) -> tuple[float, str]:
	"""Return (AC, source) preferring GL when posted amounts exist."""
	gl = get_gl_actual_cost(project_contract, as_of_date)
	wbs_total = flt(
		frappe.db.sql(
			"""
			SELECT COALESCE(SUM(actual_cost), 0)
			FROM `tabPM WBS Task`
			WHERE project = %s AND docstatus < 2
			""",
			project_contract,
		)[0][0]
	)
	if gl["total"] > 0:
		return gl["total"], gl["source"]
	if wbs_total > 0:
		return wbs_total, "wbs_manual"
	return 0.0, "none"


@frappe.whitelist()
def sync_gl_actual_cost_to_wbs(project_contract: str, as_of_date: str | None = None) -> dict:
	"""Allocate GL/BOQ actual cost to PM WBS tasks by cost_code or planned_cost ratio."""
	if not project_contract or not frappe.db.exists("Project Contract", project_contract):
		frappe.throw(frappe._("Project Contract is required"))

	gl = get_gl_actual_cost(project_contract, as_of_date)
	total_ac = flt(gl.get("total"))
	by_cost_code = gl.get("by_cost_code") or {}

	tasks = frappe.get_all(
		"PM WBS Task",
		filters={"project": project_contract, "docstatus": ["<", 2]},
		fields=["name", "cost_code", "boq_item", "planned_cost", "actual_cost"],
		limit_page_length=5000,
	)
	if not tasks:
		return {"updated": 0, "total_ac": total_ac, "source": gl.get("source")
	}

	updated = 0
	if by_cost_code:
		for task in tasks:
			code = (task.cost_code or "").strip()
			if not code and task.boq_item:
				code = (frappe.db.get_value("BOQ Item", task.boq_item, "cost_code") or "").strip()
			amount = flt(by_cost_code.get(code)) if code else 0.0
			if amount and flt(task.actual_cost) != amount:
				frappe.db.set_value("PM WBS Task", task.name, "actual_cost", amount, update_modified=False)
				updated += 1
	elif total_ac:
		planned_sum = sum(flt(t.planned_cost) for t in tasks)
		for task in tasks:
			weight = flt(task.planned_cost) / planned_sum if planned_sum else 1.0 / len(tasks)
			amount = round(total_ac * weight, 2)
			if flt(task.actual_cost) != amount:
				frappe.db.set_value("PM WBS Task", task.name, "actual_cost", amount, update_modified=False)
				updated += 1

	return {"updated": updated, "total_ac": total_ac, "source": gl.get("source")
	}


def _journal_entry_expense_total(project_contract: str, company: str | None, as_of) -> float:
	if not frappe.db.exists("DocType", "Journal Entry"):
		return 0.0
	meta = frappe.get_meta("Journal Entry")
	if not meta.has_field("project_contract"):
		return 0.0
	if not company:
		return 0.0
	cost_accounts = frappe.get_all(
		"Account",
		filters={"company": company, "root_type": "Expense", "is_group": 0
	},
		pluck="name",
		limit=200,
	)
	if not cost_accounts:
		return 0.0
	return flt(
		frappe.db.sql(
			"""
			SELECT COALESCE(SUM(jea.debit - jea.credit), 0)
			FROM `tabJournal Entry Account` jea
			INNER JOIN `tabJournal Entry` je ON je.name = jea.parent
			WHERE je.docstatus = 1
				AND je.project_contract = %s
				AND je.posting_date <= %s
				AND jea.account IN ({})
			""".format(", ".join(["%s"] * len(cost_accounts))),
			[project_contract, as_of, *cost_accounts],
		)[0][0]
	)


def _purchase_invoice_total(project_contract: str, as_of) -> float:
	if not frappe.db.exists("DocType", "Purchase Invoice"):
		return 0.0
	meta = frappe.get_meta("Purchase Invoice")
	if not meta.has_field("project_contract"):
		return 0.0
	amount_field = "grand_total" if meta.has_field("grand_total") else "total"
	return flt(
		frappe.db.sql(
			f"""
			SELECT COALESCE(SUM(`{amount_field}`), 0)
			FROM `tabPurchase Invoice`
			WHERE docstatus = 1
				AND project_contract = %s
				AND posting_date <= %s
			""",
			(project_contract, as_of),
		)[0][0]
	)


def _boq_actual_by_cost_code(project_contract: str) -> dict[str, float]:
	if not frappe.db.exists("DocType", "BOQ Item"):
		return {}
	rows = frappe.get_all(
		"BOQ Item",
		filters={"project_contract": project_contract, "is_group": 0, "docstatus": ["<", 2]},
		fields=["cost_code", "actual_cost"],
		limit_page_length=5000,
	)
	out: dict[str, float] = {}
	for row in rows:
		code = (row.cost_code or "UNALLOCATED").strip()
		out[code] = out.get(code, 0.0) + flt(row.actual_cost)
	return out
