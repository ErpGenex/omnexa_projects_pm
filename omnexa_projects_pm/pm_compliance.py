# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""PM compliance matrix vs ISO 21500 / PMI PMBOK (self-assessment)."""

from __future__ import annotations

import frappe

# Weighted capability matrix (0–5). Updated 2026-06-06.
PM_COMPLIANCE_MATRIX: list[dict] = [
	{"id": "integration", "label": "Integration / Governance", "standard": "ISO 21500 §4.4", "weight": 8, "score": 3.5},
	{"id": "portfolio", "label": "Portfolio & Program", "standard": "ISO 21500 §4.3", "weight": 9, "score": 4.4},
	{"id": "stakeholder", "label": "Stakeholder Engagement", "standard": "PMBOK Stakeholder", "weight": 7, "score": 3.2},
	{"id": "scope", "label": "Scope & WBS", "standard": "ISO 21500 §4.4.8", "weight": 10, "score": 4.5},
	{"id": "schedule", "label": "Schedule / CPM", "standard": "PMBOK Schedule", "weight": 11, "score": 4.6},
	{"id": "cost_evm", "label": "Cost & EVM", "standard": "PMBOK EVM / AACE", "weight": 11, "score": 4.5},
	{"id": "quality", "label": "Quality", "standard": "ISO 21500 §4.4.10", "weight": 6, "score": 4.0},
	{"id": "resource", "label": "Resource Management", "standard": "ISO 21500 §4.4.9", "weight": 8, "score": 4.2},
	{"id": "risk", "label": "Risk Management", "standard": "ISO 31000 / PMBOK", "weight": 9, "score": 4.0},
	{"id": "change", "label": "Change Control", "standard": "PMBOK Change", "weight": 8, "score": 3.4},
	{"id": "reporting", "label": "Reporting & KPIs", "standard": "ISO 21500 performance", "weight": 8, "score": 4.1},
	{"id": "integration_ext", "label": "External Integration (P6/BOQ/GL)", "standard": "Enterprise PM", "weight": 7, "score": 4.3},
]


@frappe.whitelist()
def get_pm_compliance_score() -> dict:
	"""Return weighted PM compliance score and matrix."""
	total_weight = sum(row["weight"] for row in PM_COMPLIANCE_MATRIX)
	weighted = sum(row["weight"] * row["score"] for row in PM_COMPLIANCE_MATRIX)
	score = round(weighted / total_weight, 2) if total_weight else 0
	return {
		"weighted_score": score,
		"max_score": 5.0,
		"matrix": PM_COMPLIANCE_MATRIX,
		"standards": ["ISO 21500:2021", "PMBOK 7", "AACE RP 10S-90"],
		"app": "omnexa_projects_pm",
	}
