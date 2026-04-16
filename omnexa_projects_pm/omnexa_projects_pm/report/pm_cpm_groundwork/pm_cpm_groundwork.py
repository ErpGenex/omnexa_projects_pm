import frappe
from frappe.utils import cint, date_diff, getdate


def _row_get(row, key, default=None):
	"""Works for dict rows and frappe _dict from get_all."""
	if hasattr(row, "get"):
		return row.get(key, default)
	return getattr(row, key, default)


def execute(filters=None):
	columns = [
		{"label": "Task", "fieldname": "name", "fieldtype": "Link", "options": "PM WBS Task", "width": 180},
		{"label": "Project Contract", "fieldname": "project", "fieldtype": "Link", "options": "Project Contract", "width": 180},
		{"label": "Task Name", "fieldname": "task_name", "fieldtype": "Data", "width": 220},
		{"label": "Duration (Days)", "fieldname": "duration_days", "fieldtype": "Int", "width": 120},
		{"label": "ES", "fieldname": "es", "fieldtype": "Int", "width": 70},
		{"label": "EF", "fieldname": "ef", "fieldtype": "Int", "width": 70},
		{"label": "LS", "fieldname": "ls", "fieldtype": "Int", "width": 70},
		{"label": "LF", "fieldname": "lf", "fieldtype": "Int", "width": 70},
		{"label": "Total Float", "fieldname": "total_float", "fieldtype": "Int", "width": 90},
		{"label": "Gantt Marker", "fieldname": "gantt_marker", "fieldtype": "Data", "width": 100},
		{"label": "CPM Flag", "fieldname": "cpm_flag", "fieldtype": "Data", "width": 100},
	]

	tasks = frappe.get_all(
		"PM WBS Task",
		fields=["name", "project", "task_name", "planned_start", "planned_end", "status"],
		filters={"docstatus": ["<", 2]},
		limit_page_length=2000,
	)
	if not tasks:
		return columns, []

	by_project = {}
	for t in tasks:
		by_project.setdefault(t.project, []).append(t)

	dependencies = frappe.get_all(
		"PM Task Dependency",
		fields=["parent", "depends_on_task", "dependency_type", "lag_days"],
		limit_page_length=10000,
	)

	data = []
	for project_name, project_tasks in by_project.items():
		task_names = {t.name for t in project_tasks}
		project_deps = [
			d for d in dependencies if _row_get(d, "parent") in task_names and _row_get(d, "depends_on_task") in task_names
		]
		data.extend(_compute_cpm_for_project(project_tasks, project_deps, project_name))

	return columns, sorted(data, key=lambda d: (d["project"] or "", d["cpm_flag"] != "Critical", d["es"], d["name"]))


def _duration_days(start, end):
	if not (start and end):
		return 1
	return max(0, date_diff(getdate(end), getdate(start)) + 1)


def _compute_cpm_for_project(tasks, deps, project_name):
	task_map = {
		t.name: {
			"name": t.name,
			"project": project_name,
			"task_name": t.task_name,
			"duration_days": _duration_days(t.planned_start, t.planned_end),
			"pred": set(),
			"succ": set(),
			"es": 0,
			"ef": 0,
			"ls": 0,
			"lf": 0,
			"total_float": 0,
			"gantt_marker": "",
			"cpm_flag": "Normal",
		}
		for t in tasks
	}
	for d in deps:
		par = _row_get(d, "parent")
		pred_name = _row_get(d, "depends_on_task")
		task_map[par]["pred"].add(pred_name)
		task_map[pred_name]["succ"].add(par)

	in_degree = {name: len(task_map[name]["pred"]) for name in task_map}
	queue = [name for name, deg in in_degree.items() if deg == 0]
	order = []
	while queue:
		n = queue.pop(0)
		order.append(n)
		for succ_name in task_map[n]["succ"]:
			in_degree[succ_name] -= 1
			if in_degree[succ_name] == 0:
				queue.append(succ_name)

	# If there is a cycle, fall back to stable deterministic order.
	if len(order) != len(task_map):
		order = sorted(task_map.keys())

	for name in order:
		node = task_map[name]
		if node["pred"]:
			node["es"] = max(
				_forward_start_bound(task_map, d) for d in deps if _row_get(d, "parent") == name
			)
		node["ef"] = node["es"] + node["duration_days"]

	project_finish = max(task_map[n]["ef"] for n in task_map) if task_map else 0

	for name in reversed(order):
		node = task_map[name]
		if node["succ"]:
			ls_cap = []
			lf_cap = []
			for d in deps:
				pred_n = _row_get(d, "depends_on_task")
				if pred_n != name:
					continue
				ls_bound, lf_bound = _backward_caps(task_map, d)
				if ls_bound is not None:
					ls_cap.append(ls_bound)
				if lf_bound is not None:
					lf_cap.append(lf_bound)
			lf_from_lf_caps = min(lf_cap) if lf_cap else project_finish
			ls_from_lf_caps = lf_from_lf_caps - node["duration_days"]
			ls_from_ls_caps = min(ls_cap) if ls_cap else ls_from_lf_caps
			node["ls"] = min(ls_from_lf_caps, ls_from_ls_caps)
			node["lf"] = node["ls"] + node["duration_days"]
		else:
			node["lf"] = project_finish
			node["ls"] = node["lf"] - node["duration_days"]
		node["total_float"] = node["ls"] - node["es"]
		node["cpm_flag"] = "Critical" if node["total_float"] == 0 else "Normal"
		node["gantt_marker"] = "CRITICAL" if node["cpm_flag"] == "Critical" else ""

	return [
		{
			"name": n["name"],
			"project": n["project"],
			"task_name": n["task_name"],
			"duration_days": n["duration_days"],
			"es": n["es"],
			"ef": n["ef"],
			"ls": n["ls"],
			"lf": n["lf"],
			"total_float": n["total_float"],
			"gantt_marker": n["gantt_marker"],
			"cpm_flag": n["cpm_flag"],
		}
		for n in task_map.values()
	]


def _dep_lag(dep) -> int:
	return cint(_row_get(dep, "lag_days") or 0)


def _forward_start_bound(task_map, dep):
	pred = task_map[_row_get(dep, "depends_on_task")]
	succ = task_map[_row_get(dep, "parent")]
	rel = _row_get(dep, "dependency_type") or "FS"
	lag = _dep_lag(dep)
	if rel == "SS":
		return pred["es"] + lag
	if rel == "FF":
		return pred["ef"] + lag - succ["duration_days"]
	if rel == "SF":
		return pred["es"] + lag - succ["duration_days"]
	return pred["ef"] + lag  # FS


def _backward_caps(task_map, dep):
	succ = task_map[_row_get(dep, "parent")]
	rel = _row_get(dep, "dependency_type") or "FS"
	# Returns (ls_cap, lf_cap) for predecessor.
	if rel == "SS":
		return succ["ls"], None
	if rel == "FF":
		return None, succ["lf"]
	if rel == "SF":
		return succ["lf"], None
	return None, succ["ls"]  # FS

