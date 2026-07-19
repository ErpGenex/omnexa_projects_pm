# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Export PM global audit bundle to Docs."""

from __future__ import annotations

import json
import os
from typing import Any

import frappe
from frappe.utils import get_bench_path

from omnexa_projects_pm.pm_gap_register import get_gap_status
from omnexa_projects_pm.pm_global_benchmark import get_global_pm_score


def _audit_root() -> str:
	return os.path.join(
		get_bench_path(),
		"Docs",
		"2026-06-06_OMNEXA_PROJECTS_PM_GLOBAL_AUDIT",
	)


@frappe.whitelist()
def export_pm_global_audit() -> dict[str, Any]:
	root = _audit_root()
	os.makedirs(root, exist_ok=True)
	score = get_global_pm_score()
	gaps = get_gap_status()
	for name, data in (
		("PM_LIVE_SCORE.json", score),
		("PM_GAP_REGISTER.json", gaps),
	):
		with open(os.path.join(root, name), "w", encoding="utf-8") as fh:
			json.dump(data, fh, ensure_ascii=False, indent=2)
	return {"path": root, "weighted_score": score.get("weighted_score"), "gaps_open": gaps.get("gaps_open")}
