import frappe
from frappe import _
from frappe.model.document import Document

from omnexa_projects_pm.wbs_integration import validate_linked_pm_wbs_task


class PMMilestone(Document):
	def validate(self):
		validate_linked_pm_wbs_task(self.project, self.related_wbs_task, label="Related WBS Task")
		self._validate_milestone_lifecycle_controls()

	def _validate_milestone_lifecycle_controls(self):
		if self.status == "Completed":
			if not self.actual_date:
				frappe.throw(_("Actual Date is mandatory when milestone is Completed."))
			if not self.acceptance_criteria:
				frappe.throw(_("Acceptance Criteria is mandatory when milestone is Completed."))

		if self.status == "Delayed" and not self.actual_date and not self.acceptance_criteria:
			frappe.throw(
				_("For delayed milestones, provide Actual Date or Acceptance Criteria note for traceability.")
			)

