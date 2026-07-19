from frappe.tests.utils import FrappeTestCase

from omnexa_projects_pm import hooks


class TestProjectsPmLicenseSmoke(FrappeTestCase):
	def test_projects_pm_has_no_license_gate_hook(self):
		self.assertFalse(hasattr(hooks, "before_request"))
