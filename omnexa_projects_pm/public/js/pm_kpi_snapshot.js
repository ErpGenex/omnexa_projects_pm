// Copyright (c) 2026, Omnexa and contributors
// License: MIT

frappe.ui.form.on("PM KPI Snapshot", {
	refresh(frm) {
		if (frm.is_new() || frm.doc.__unsaved) {
			return;
		}
		frm.add_custom_button(
			__("Recalculate PV / EV / AC from WBS"),
			() => {
				frm.call("recalculate_evm_from_wbs")
					.then(() => {
						frappe.show_alert({
							message: __("EVM fields updated from WBS tasks."),
							indicator: "green",
						});
						frm.reload_doc();
					})
					.catch(() => {});
			},
			__("Actions")
		);
	},
});
