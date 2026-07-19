# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe import _
from frappe.model.document import Document


class PMProgram(Document):
	def validate(self):
		seen: set[str] = set()
		for row in self.projects or []:
			if not row.project_contract:
				continue
			if row.project_contract in seen:
				frappe.throw(
					_("Project {0} appears more than once in this program.").format(row.project_contract)
				)
			seen.add(row.project_contract)
