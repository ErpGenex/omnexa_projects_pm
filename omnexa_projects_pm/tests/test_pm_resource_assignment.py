# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

class TestPmResourceAssignment(FrappeTestCase):
	def test_human_requires_user_or_label(self):
		doc = frappe.get_doc(
			{
				"doctype": "PM Resource Assignment",
				"project": "TEST-PROJECT",
				"resource_type": "Human",
				"company": "_Test Company",
				"branch": "_Test Branch",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.validate()

	def test_equipment_requires_label(self):
		doc = frappe.get_doc(
			{
				"doctype": "PM Resource Assignment",
				"project": "TEST-PROJECT",
				"resource_type": "Equipment",
				"company": "_Test Company",
				"branch": "_Test Branch",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.validate()

	def test_negative_units_rejected(self):
		doc = frappe.get_doc(
			{
				"doctype": "PM Resource Assignment",
				"project": "TEST-PROJECT",
				"resource_type": "Material",
				"resource_label": "Cement",
				"planned_units": -1,
				"company": "_Test Company",
				"branch": "_Test Branch",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.validate()

	@patch("omnexa_projects_pm.wbs_integration.frappe.db.get_value", return_value="OTHER-PROJECT")
	def test_wbs_must_match_project(self, _mock_get_value):
		doc = frappe.get_doc(
			{
				"doctype": "PM Resource Assignment",
				"project": "MY-PROJECT",
				"pm_wbs_task": "WBS-001",
				"resource_type": "Other",
				"resource_label": "Vendor",
				"company": "_Test Company",
				"branch": "_Test Branch",
			}
		)
		with self.assertRaises(frappe.ValidationError):
			doc.validate()

	def test_validate_passes_minimal_other_resource(self):
		doc = frappe.get_doc(
			{
				"doctype": "PM Resource Assignment",
				"project": "MY-PROJECT",
				"resource_type": "Other",
				"resource_label": "Vendor",
				"company": "_Test Company",
				"branch": "_Test Branch",
			}
		)
		doc.validate()
