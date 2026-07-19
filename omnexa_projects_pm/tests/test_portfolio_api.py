# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe
from frappe.tests.utils import FrappeTestCase

from omnexa_projects_pm.portfolio_api import get_portfolio_dashboard
from omnexa_projects_pm.pm_compliance import get_pm_compliance_score


class TestPortfolioApi(FrappeTestCase):
	def test_compliance_score(self):
		out = get_pm_compliance_score()
		self.assertIn("weighted_score", out)
		self.assertGreater(out["weighted_score"], 3.0)
		self.assertLessEqual(out["weighted_score"], 5.0)

	def test_portfolio_dashboard_keys(self):
		company = frappe.db.get_value("Company", {}, "name")
		if not company:
			self.skipTest("No company")
		out = get_portfolio_dashboard(company)
		for key in (
			"contract_count",
			"total_bac",
			"portfolio_spi",
			"contracts",
			"on_track_contracts",
		):
			self.assertIn(key, out)
