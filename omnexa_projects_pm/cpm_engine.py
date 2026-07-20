from __future__ import annotations

from frappe.utils import date_diff, flt, getdate


def _task_duration_days(task) -> int:
	if getattr(task, "planned_start", None) and getattr(task, "planned_end", None):
		days = date_diff(getdate(task.planned_end), getdate(task.planned_start)) + 1
		return max(int(days), 1)
	return 1


def _topological_order(tasks: dict, preds: dict, succs: dict) -> list[str]:
	in_degree = {name: len(preds.get(name, [])) for name in tasks}
	queue = [name for name, deg in in_degree.items() if deg == 0]
	order: list[str] = []
	while queue:
		node = queue.pop(0)
		order.append(node)
		for succ, _dtype, _lag in succs.get(node, []):
			in_degree[succ] -= 1
			if in_degree[succ] == 0:
				queue.append(succ)
	if len(order) < len(tasks):
		order.extend(name for name in tasks if name not in order)
	return order


def _apply_forward_constraint(es: int, ef_pred: int, es_pred: int, duration: int, dtype: str, lag: int) -> int:
	dtype = (dtype or "FS").upper()
	if dtype == "FS":
		return max(es, ef_pred + lag)
	if dtype == "SS":
		return max(es, es_pred + lag)
	if dtype == "FF":
		return max(es, ef_pred + lag - duration)
	if dtype == "SF":
		return max(es, es_pred + lag - duration)
	return max(es, ef_pred + lag)


def _apply_backward_constraint(lf: int, ls_succ: int, lf_succ: int, es_succ: int, dtype: str, lag: int) -> int:
	dtype = (dtype or "FS").upper()
	if dtype == "FS":
		return min(lf, ls_succ - lag)
	if dtype == "SS":
		return min(lf, lf_succ - lag)
	if dtype == "FF":
		return min(lf, lf_succ - lag)
	if dtype == "SF":
		return min(lf, es_succ - lag)
	return min(lf, ls_succ - lag)


def _compute_cpm_for_project(project_tasks, project_deps, project_name: str) -> list[dict]:
	"""Forward/backward pass CPM for one project contract. Returns rows with ES/EF/LS/LF/float."""
	if not project_tasks:
		return []

	tasks = {t.name: t for t in project_tasks}
	duration = {name: _task_duration_days(t) for name, t in tasks.items()}
	preds: dict[str, list] = {name: [] for name in tasks}
	succs: dict[str, list] = {name: [] for name in tasks}

	for dep in project_deps or []:
		pred = dep.depends_on_task
		succ = dep.parent
		if pred not in tasks or succ not in tasks:
			continue
		lag = int(flt(dep.lag_days))
		dtype = dep.dependency_type or "FS"
		preds[succ].append((pred, dtype, lag))
		succs[pred].append((succ, dtype, lag))

	order = _topological_order(tasks, preds, succs)
	es: dict[str, int] = {name: 0 for name in tasks}
	ef: dict[str, int] = {}

	for name in order:
		dur = duration[name]
		start = es[name]
		for pred, dtype, lag in preds.get(name, []):
			start = _apply_forward_constraint(start, ef[pred], es[pred], dur, dtype, lag)
		es[name] = start
		ef[name] = start + dur

	project_end = max(ef.values()) if ef else 0
	rev_order = list(reversed(order))
	lf_map: dict[str, int] = {name: project_end for name in tasks}
	ls_map: dict[str, int] = {}

	for name in rev_order:
		dur = duration[name]
		finish = lf_map[name]
		if succs.get(name):
			for succ, dtype, lag in succs[name]:
				finish = _apply_backward_constraint(finish, ls_map[succ], lf_map[succ], es[succ], dtype, lag)
		lf_map[name] = finish
		ls_map[name] = finish - dur

	rows: list[dict] = []
	for task in project_tasks:
		name = task.name
		total_float = ls_map[name] - es[name]
		critical = total_float <= 0
		rows.append(
			{
				"name": name,
				"project": project_name,
				"task_name": task.task_name,
				"duration_days": duration[name],
				"es": es[name],
				"ef": ef[name],
				"ls": ls_map[name],
				"lf": lf_map[name],
				"total_float": total_float,
				"gantt_marker": "◆" if critical else "",
				"cpm_flag": "Critical" if critical else "Non-Critical"
	}
		)
	return rows
