from frappe.model.document import Document

from omnexa_projects_pm.wbs_integration import validate_linked_pm_wbs_task


class PMIssueLog(Document):
	def validate(self):
		validate_linked_pm_wbs_task(self.project, self.related_wbs_task, label="Related WBS Task")

