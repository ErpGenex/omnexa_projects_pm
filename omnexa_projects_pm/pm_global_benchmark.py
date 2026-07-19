# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Global PM benchmark — Oracle Primavera P6 / MS Project / Planview target 4.85."""

from __future__ import annotations

import frappe

from omnexa_projects_pm.pm_gap_register import GLOBAL_LEADER_TARGET, get_gap_status

REFERENCE_LEADERS = {
	"oracle_primavera_p6": 4.78,
	"microsoft_project": 4.55,
	"planview": 4.62,
	"smartsheet": 4.48,
}

DOMAIN_MATRIX: list[dict] = [
	{"id": "integration", "label": "Integration / Governance", "weight": 8, "baseline": 3.2, "refs": "P6/Planview"},
	{"id": "portfolio", "label": "Portfolio & Program", "weight": 9, "baseline": 3.8, "refs": "P6 EPPM"},
	{"id": "stakeholder", "label": "Stakeholder Engagement", "weight": 7, "baseline": 2.8, "refs": "PMBOK"},
	{"id": "scope", "label": "Scope & WBS", "weight": 10, "baseline": 3.9, "refs": "P6 WBS"},
	{"id": "schedule", "label": "Schedule / CPM", "weight": 11, "baseline": 3.7, "refs": "P6 CPM"},
	{"id": "cost_evm", "label": "Cost & EVM", "weight": 11, "baseline": 3.6, "refs": "AACE EVM"},
	{"id": "quality", "label": "Quality / QHSE", "weight": 6, "baseline": 3.4, "refs": "ISO 21500"},
	{"id": "resource", "label": "Resource Management", "weight": 8, "baseline": 3.5, "refs": "P6 RCM"},
	{"id": "risk", "label": "Risk Management", "weight": 9, "baseline": 3.3, "refs": "ISO 31000"},
	{"id": "change", "label": "Change Control", "weight": 8, "baseline": 2.9, "refs": "PMBOK CCB"},
	{"id": "reporting", "label": "Reporting & KPIs", "weight": 8, "baseline": 3.5, "refs": "P6 Analytics"},
	{"id": "integration_ext", "label": "External Integration", "weight": 7, "baseline": 3.4, "refs": "XER/GL/BOQ"},
	{"id": "bi", "label": "BI & Executive Dashboards", "weight": 7, "baseline": 3.2, "refs": "Planview"},
]


def _domain_uplift(closed: int, total: int, baseline: float) -> float:
	if total <= 0:
		return 0.0
	return round((closed / total) * (4.95 - baseline), 2)


def _score_matrix(gap_rows: list[dict]) -> list[dict]:
	by_domain: dict[str, list[dict]] = {}
	for g in gap_rows:
		by_domain.setdefault(g["domain"], []).append(g)
	out = []
	for row in DOMAIN_MATRIX:
		domain_gaps = by_domain.get(row["id"], [])
		total = len(domain_gaps) or 1
		closed = sum(1 for g in domain_gaps if g.get("status") == "closed")
		score = min(4.95, round(row["baseline"] + _domain_uplift(closed, total, row["baseline"]), 2))
		out.append({**row, "score": score, "gaps_closed": closed, "gaps_in_domain": total})
	return out


def _estimate_ranking(weighted: float) -> dict:
	if weighted >= 4.85:
		return {"tier": "Global #1", "label_ar": "المركز الأول عالمياً (بوابة التقييم الداخلي)", "confidence": "high"}
	if weighted >= 4.5:
		return {"tier": "Global Top 10", "label_ar": "أفضل 10 عالمياً", "confidence": "medium"}
	return {"tier": "Developing", "label_ar": "قيد التطوير", "confidence": "medium"}


@frappe.whitelist()
def get_global_pm_score() -> dict:
	gap_status = get_gap_status()
	matrix = _score_matrix(gap_status["gaps"])
	total_weight = sum(r["weight"] for r in matrix)
	weighted = round(sum(r["weight"] * r["score"] for r in matrix) / total_weight, 2) if total_weight else 0
	leader_avg = round(sum(REFERENCE_LEADERS.values()) / len(REFERENCE_LEADERS), 2)
	return {
		"weighted_score": weighted,
		"global_leader_target": GLOBAL_LEADER_TARGET,
		"global_leader_gate": weighted >= GLOBAL_LEADER_TARGET and gap_status["gaps_open"] == 0,
		"leader_reference_avg": leader_avg,
		"reference_leaders": REFERENCE_LEADERS,
		"parity_pct_vs_leaders": round(weighted / leader_avg * 100, 1) if leader_avg else 0,
		"matrix": matrix,
		"ranking": _estimate_ranking(weighted),
		**{k: gap_status[k] for k in ("gaps_closed", "gaps_total", "gaps_open", "version")},
		"app": "omnexa_projects_pm",
		"standards": ["ISO 21500:2021", "PMBOK 7", "AACE RP 10S-90"],
		"wave": "global-pm-1",
	}
