# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""PM gap register — 48 items vs Oracle Primavera P6 / MS Project / Planview."""

from __future__ import annotations

import os

import frappe
from frappe.utils import get_bench_path

GLOBAL_LEADER_TARGET = 4.85
GAPS_TOTAL = 48
APP = "omnexa_projects_pm"

GAP_DEFINITIONS: list[dict] = [
	{"id": "PM-001", "domain": "integration", "title": "Global PM benchmark module", "wave": 1, "detect": "module:pm_global_benchmark"},
	{"id": "PM-002", "domain": "integration", "title": "PM gap register", "wave": 1, "detect": "module:pm_gap_register"},
	{"id": "PM-003", "domain": "integration", "title": "Full workspace sync module", "wave": 1, "detect": "module:workspace.projects_workspace"},
	{"id": "PM-004", "domain": "portfolio", "title": "Project Contract master", "wave": 1, "detect": "doctype:Project Contract"},
	{"id": "PM-005", "domain": "portfolio", "title": "PM Program entity", "wave": 1, "detect": "doctype:PM Program"},
	{"id": "PM-006", "domain": "portfolio", "title": "PM Program Project child", "wave": 1, "detect": "doctype:PM Program Project"},
	{"id": "PM-007", "domain": "portfolio", "title": "Portfolio dashboard API", "wave": 1, "detect": "api:omnexa_projects_pm.portfolio_api.get_portfolio_dashboard"},
	{"id": "PM-008", "domain": "portfolio", "title": "Program portfolio API", "wave": 1, "detect": "api:omnexa_projects_pm.program_api.get_program_portfolio"},
	{"id": "PM-009", "domain": "portfolio", "title": "Portfolio prioritize API", "wave": 1, "detect": "api:omnexa_projects_pm.program_api.prioritize_portfolio"},
	{"id": "PM-010", "domain": "portfolio", "title": "Portfolio dashboard page", "wave": 1, "detect": "page:pm-portfolio-dashboard"},
	{"id": "PM-011", "domain": "stakeholder", "title": "Stakeholder register DocType", "wave": 1, "detect": "doctype:PM Stakeholder Register"},
	{"id": "PM-012", "domain": "stakeholder", "title": "Stakeholder engagement index API", "wave": 2, "detect": "api:omnexa_projects_pm.pm_global_extensions.compute_stakeholder_engagement_index"},
	{"id": "PM-013", "domain": "scope", "title": "PM WBS Task", "wave": 1, "detect": "doctype:PM WBS Task"},
	{"id": "PM-014", "domain": "scope", "title": "PM Task Dependency", "wave": 1, "detect": "doctype:PM Task Dependency"},
	{"id": "PM-015", "domain": "scope", "title": "WBS schedule integration", "wave": 1, "detect": "module:wbs_schedule"},
	{"id": "PM-016", "domain": "scope", "title": "WBS integration bridge", "wave": 1, "detect": "module:wbs_integration"},
	{"id": "PM-017", "domain": "schedule", "title": "CPM engine", "wave": 1, "detect": "module:cpm_engine"},
	{"id": "PM-018", "domain": "schedule", "title": "CPM timeline API", "wave": 1, "detect": "api:omnexa_projects_pm.api.cpm_timeline"},
	{"id": "PM-019", "domain": "schedule", "title": "Gantt desk page", "wave": 1, "detect": "page:pm_schedule_gantt"},
	{"id": "PM-020", "domain": "schedule", "title": "Schedule ↔ WBS bridge", "wave": 1, "detect": "module:schedule_wbs_bridge"},
	{"id": "PM-021", "domain": "schedule", "title": "PM Milestone", "wave": 1, "detect": "doctype:PM Milestone"},
	{"id": "PM-022", "domain": "cost_evm", "title": "EVM compute module", "wave": 1, "detect": "module:evm"},
	{"id": "PM-023", "domain": "cost_evm", "title": "GL cost bridge", "wave": 1, "detect": "module:gl_cost_bridge"},
	{"id": "PM-024", "domain": "cost_evm", "title": "Sync GL actual to WBS", "wave": 1, "detect": "api:omnexa_projects_pm.gl_cost_bridge.sync_gl_actual_cost_to_wbs"},
	{"id": "PM-025", "domain": "cost_evm", "title": "PM Baseline Snapshot", "wave": 1, "detect": "doctype:PM Baseline Snapshot"},
	{"id": "PM-026", "domain": "quality", "title": "QHSE quality bridge", "wave": 1, "detect": "module:qhse_quality_bridge"},
	{"id": "PM-027", "domain": "quality", "title": "Quality QHSE summary report", "wave": 1, "detect": "report:PM Quality QHSE Summary"},
	{"id": "PM-028", "domain": "resource", "title": "PM Resource Assignment", "wave": 1, "detect": "doctype:PM Resource Assignment"},
	{"id": "PM-029", "domain": "resource", "title": "Resource overload detection", "wave": 1, "detect": "api:omnexa_projects_pm.resource_leveling.detect_resource_overloads"},
	{"id": "PM-030", "domain": "resource", "title": "Resource leveling apply", "wave": 1, "detect": "api:omnexa_projects_pm.resource_leveling.apply_resource_leveling"},
	{"id": "PM-031", "domain": "risk", "title": "Risk Register DocType", "wave": 1, "detect": "doctype:Risk Register"},
	{"id": "PM-032", "domain": "risk", "title": "Monte Carlo schedule risk API", "wave": 2, "detect": "api:omnexa_projects_pm.pm_global_extensions.run_monte_carlo_schedule_risk"},
	{"id": "PM-033", "domain": "change", "title": "PM Change Request", "wave": 1, "detect": "doctype:PM Change Request"},
	{"id": "PM-034", "domain": "change", "title": "Change control board status API", "wave": 2, "detect": "api:omnexa_projects_pm.pm_global_extensions.get_change_control_board_status"},
	{"id": "PM-035", "domain": "reporting", "title": "PM KPI Snapshot", "wave": 1, "detect": "doctype:PM KPI Snapshot"},
	{"id": "PM-036", "domain": "reporting", "title": "Daily KPI scheduler", "wave": 1, "detect": "module:tasks"},
	{"id": "PM-037", "domain": "reporting", "title": "CPM Groundwork report", "wave": 1, "detect": "report:PM CPM Groundwork"},
	{"id": "PM-038", "domain": "reporting", "title": "Resource Loading report", "wave": 1, "detect": "report:PM Resource Loading"},
	{"id": "PM-039", "domain": "reporting", "title": "KPI Snapshot Summary report", "wave": 1, "detect": "report:PM KPI Snapshot Summary"},
	{"id": "PM-040", "domain": "reporting", "title": "Risk Register Summary report", "wave": 1, "detect": "report:PM Risk Register Summary"},
	{"id": "PM-041", "domain": "reporting", "title": "Issue Log Summary report", "wave": 1, "detect": "report:PM Issue Log Summary"},
	{"id": "PM-042", "domain": "reporting", "title": "Milestone Summary report", "wave": 1, "detect": "report:PM Milestone Summary"},
	{"id": "PM-043", "domain": "integration_ext", "title": "P6 XER import preview API", "wave": 2, "detect": "api:omnexa_projects_pm.pm_global_extensions.preview_p6_xer_import"},
	{"id": "PM-044", "domain": "integration_ext", "title": "Construction schedule baseline link", "wave": 2, "detect": "doctype:Construction Schedule Baseline"},
	{"id": "PM-045", "domain": "integration_ext", "title": "BOQ Item integration", "wave": 2, "detect": "doctype:BOQ Item"},
	{"id": "PM-046", "domain": "bi", "title": "PM Issue Log execution", "wave": 1, "detect": "doctype:PM Issue Log"},
	{"id": "PM-047", "domain": "bi", "title": "Sector KPI preview bridge", "wave": 1, "detect": "api:omnexa_projects_pm.api.preview_sector_kpi"},
	{"id": "PM-048", "domain": "bi", "title": "PM assessment export module", "wave": 1, "detect": "module:pm_assessment"},
]


def _detect_gap(gap: dict) -> bool:
	detect = gap.get("detect")
	if not detect:
		return False
	try:
		if detect.startswith("doctype:"):
			return bool(frappe.db.exists("DocType", detect.split(":", 1)[1]))
		if detect.startswith("page:"):
			return bool(frappe.db.exists("Page", detect.split(":", 1)[1]))
		if detect.startswith("report:"):
			return bool(frappe.db.exists("Report", detect.split(":", 1)[1]))
		if detect.startswith("api:"):
			return bool(frappe.get_attr(detect.split(":", 1)[1]))
		if detect.startswith("module:"):
			return bool(frappe.get_module(f"{APP}.{detect.split(':', 1)[1]}"))
		if detect.startswith("file:"):
			rel = detect.split(":", 1)[1]
			root = os.path.join(get_bench_path(), "apps", APP, APP)
			return os.path.isfile(os.path.join(root, rel))
	except Exception:
		return False
	return False


def get_gap_status() -> dict:
	rows = []
	closed = 0
	for gap in GAP_DEFINITIONS:
		is_closed = _detect_gap(gap)
		if is_closed:
			closed += 1
		rows.append({**gap, "status": "closed" if is_closed else "open"})
	return {
		"version": "2026.06.06",
		"target_score": GLOBAL_LEADER_TARGET,
		"gaps_total": GAPS_TOTAL,
		"gaps_closed": closed,
		"gaps_open": GAPS_TOTAL - closed,
		"global_leader_gate": closed >= GAPS_TOTAL,
		"gaps": rows,
	}
