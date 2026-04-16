from frappe.model.document import Document
from frappe.utils import flt


class PMBaselineSnapshot(Document):
	def validate(self):
		self.schedule_variance_days = (self.actual_duration_days or 0) - (self.planned_duration_days or 0)
		self.cost_variance = flt(self.actual_cost) - flt(self.planned_budget)

