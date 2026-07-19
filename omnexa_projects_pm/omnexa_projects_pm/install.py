import frappe


SUPPORTED_FRAPPE_MAJOR = 15


def enforce_supported_frappe_version():
	"""Fail fast when running on unsupported Frappe major versions."""
	version_text = (getattr(frappe, "__version__", "") or "").strip()
	if not version_text:
		return

	major_token = version_text.split(".", 1)[0]
	try:
		major = int(major_token)
	except ValueError:
		return

	if major != SUPPORTED_FRAPPE_MAJOR:
		frappe.throw(
			f"Unsupported Frappe version '{version_text}' for omnexa_projects_pm. "
			"Supported range is >=15.0,<16.0.",
			frappe.ValidationError,
		)


def after_migrate():
	try:
		from omnexa_projects_pm.workspace.projects_workspace import sync_projects_workspace_menu

		sync_projects_workspace_menu(save=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa Projects PM: workspace sync failed")
