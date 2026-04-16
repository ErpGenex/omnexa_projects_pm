from frappe.model.document import Document
from frappe.utils import flt

from omnexa_projects_pm.wbs_integration import validate_linked_pm_wbs_task


class RiskRegister(Document):
	def validate(self):
		validate_linked_pm_wbs_task(self.project, self.related_wbs_task, label="Related WBS Task")
		self.risk_score = flt(self.probability) * flt(self.impact) / 100.0

