# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from omnexa_projects_pm.wbs_integration import validate_linked_pm_wbs_task


class PMResourceAssignment(Document):
	def validate(self):
		validate_linked_pm_wbs_task(self.project, self.pm_wbs_task)
		if self.from_date and self.to_date and self.to_date < self.from_date:
			frappe.throw(_("To Date cannot be before From Date."))
		if self.resource_type == "Human":
			if not self.user and not (self.resource_label or "").strip():
				frappe.throw(
					_("For Human resources, set User or Resource Name."),
					title=_("Resource"),
				)
		else:
			if not (self.resource_label or "").strip():
				frappe.throw(
					_("Set Resource Name for equipment, material, or other types."),
					title=_("Resource"),
				)
		if flt(self.planned_hours) < 0 or flt(self.actual_hours) < 0:
			frappe.throw(_("Hours cannot be negative."))
		if flt(self.planned_units) < 0 or flt(self.actual_units) < 0:
			frappe.throw(_("Units cannot be negative."))
