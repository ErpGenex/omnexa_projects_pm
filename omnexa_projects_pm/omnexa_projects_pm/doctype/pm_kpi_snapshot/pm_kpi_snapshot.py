import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate

from omnexa_projects_pm.evm import compute_evm_for_project, compute_evm_indices


class PMKPISnapshot(Document):
	def validate(self):
		self._apply_evm_indices()

	def _apply_evm_indices(self):
		indices = compute_evm_indices(
			bac=flt(self.bac),
			pv=flt(self.pv),
			ev=flt(self.ev),
			ac=flt(self.ac),
		)
		self.spi = indices["spi"]
		self.cpi = indices["cpi"]
		self.schedule_variance = indices["schedule_variance"]
		self.cost_variance = indices["cost_variance"]
		self.estimate_at_completion = indices["estimate_at_completion"]
		self.estimate_to_complete = indices["estimate_to_complete"]
		self.variance_at_completion = indices["variance_at_completion"]
		self.to_complete_performance_index = indices["to_complete_performance_index"]
		self.schedule_health_status = indices["schedule_health_status"]
		self.cost_health_status = indices["cost_health_status"]

	@frappe.whitelist()
	def recalculate_evm_from_wbs(self):
		"""Recompute all EVM fields from **PM WBS Task** roll-up."""
		as_of = self.snapshot_date or nowdate()
		evm = compute_evm_for_project(self.project, as_of)
		for key, value in evm.items():
			if hasattr(self, key):
				setattr(self, key, value)
		self.save()
		return evm
