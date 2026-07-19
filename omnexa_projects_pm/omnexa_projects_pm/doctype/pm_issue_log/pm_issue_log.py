import frappe
from frappe import _
from frappe.model.document import Document

from omnexa_projects_pm.wbs_integration import validate_linked_pm_wbs_task


class PMIssueLog(Document):
	def validate(self):
		validate_linked_pm_wbs_task(self.project, self.related_wbs_task, label="Related WBS Task")
		self._validate_lifecycle_checkpoints()

	def _validate_lifecycle_checkpoints(self):
		# World-class control: escalated/open issues must have ownership and due date.
		if self.status in {"Open", "In Progress", "Escalated"}:
			if not self.owner_user:
				frappe.throw(_("Owner is mandatory while issue is not closed."))
			if not self.due_date:
				frappe.throw(_("Due Date is mandatory while issue is not closed."))

		# Closure gate: no issue can be closed without accountability and narrative.
		if self.status == "Closed":
			if not self.owner_user:
				frappe.throw(_("Owner is mandatory before closing an issue."))
			if not self.description:
				frappe.throw(_("Description is mandatory before closing an issue."))

