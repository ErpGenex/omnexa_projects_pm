from omnexa_core.omnexa_core.branch_access import (
	enforce_branch_access,
	permission_query_conditions_for_branch_field,
)
from omnexa_core.omnexa_core.user_context import apply_company_branch_defaults


def enforce_branch_access_for_doc(doc, method=None):
	enforce_branch_access(doc)


def populate_company_branch_from_user_context(doc, method=None):
	apply_company_branch_defaults(doc)


def risk_register_query_conditions(user=None):
	return permission_query_conditions_for_branch_field("Risk Register", user)


def pm_issue_log_query_conditions(user=None):
	return permission_query_conditions_for_branch_field("PM Issue Log", user)


def pm_kpi_snapshot_query_conditions(user=None):
	return permission_query_conditions_for_branch_field("PM KPI Snapshot", user)


def pm_wbs_task_query_conditions(user=None):
	return permission_query_conditions_for_branch_field("PM WBS Task", user)


def pm_baseline_snapshot_query_conditions(user=None):
	return permission_query_conditions_for_branch_field("PM Baseline Snapshot", user)


def pm_milestone_query_conditions(user=None):
	return permission_query_conditions_for_branch_field("PM Milestone", user)


def pm_resource_assignment_query_conditions(user=None):
	return permission_query_conditions_for_branch_field("PM Resource Assignment", user)
