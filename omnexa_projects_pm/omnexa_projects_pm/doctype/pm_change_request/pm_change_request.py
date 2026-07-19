import frappe
from frappe.model.document import Document
from frappe.utils import nowdate


class PMChangeRequest(Document):
	def validate(self):
		if self.status == "Approved" and not self.approved_by:
			self.approved_by = frappe.session.user
			self.approval_date = self.approval_date or nowdate()

	def on_update(self):
		if self.status == "Rejected":
			self.approved_by = None
			self.approval_date = None
