import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from omnexa_projects_pm.wbs_integration import validate_linked_pm_wbs_task


class RiskRegister(Document):
	def validate(self):
		validate_linked_pm_wbs_task(self.project, self.related_wbs_task, label="Related WBS Task")
		self.risk_score = flt(self.probability) * flt(self.impact) / 100.0
		self._validate_risk_lifecycle_controls()

	def _validate_risk_lifecycle_controls(self):
		# Open/Mitigated risks require accountable owner and mitigation trail.
		if self.status in {"Open", "Mitigated"}:
			if not self.risk_owner:
				frappe.throw(_("Risk Owner is mandatory for open/mitigated risks."))
			if not self.mitigation_plan:
				frappe.throw(_("Mitigation Plan is mandatory for open/mitigated risks."))
			if not self.next_review_date:
				frappe.throw(_("Next Review Date is mandatory for open/mitigated risks."))

		# Closure gate: risks can close only after treatment evidence exists.
		if self.status == "Closed" and not self.mitigation_plan:
			frappe.throw(_("Mitigation Plan is mandatory before closing a risk."))

