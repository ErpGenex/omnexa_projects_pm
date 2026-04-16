import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class PMKPISnapshot(Document):
	def validate(self):
		self.spi = flt(self.ev) / flt(self.pv) if flt(self.pv) else 0
		self.cpi = flt(self.ev) / flt(self.ac) if flt(self.ac) else 0

	@frappe.whitelist()
	def recalculate_evm_from_wbs(self):
		"""Recompute PV, EV, AC from **PM WBS Task** roll-up (same rules as daily snapshot job)."""
		from omnexa_projects_pm.evm import compute_evm_for_project

		as_of = self.snapshot_date or nowdate()
		evm = compute_evm_for_project(self.project, as_of)
		self.pv = evm["pv"]
		self.ev = evm["ev"]
		self.ac = evm["ac"]
		self.save()
		return {"pv": self.pv, "ev": self.ev, "ac": self.ac, "spi": self.spi, "cpi": self.cpi}

