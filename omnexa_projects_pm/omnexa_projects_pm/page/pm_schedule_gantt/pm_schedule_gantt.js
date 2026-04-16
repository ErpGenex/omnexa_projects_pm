// Copyright (c) 2026, Omnexa and contributors
// License: MIT

frappe.pages["pm_schedule_gantt"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("PM Schedule (Gantt)"),
		single_column: true,
	});

	const $body = $(page.body);
	const $toolbar = $(`<div class="pm-gantt-toolbar" style="margin-bottom:12px"></div>`).appendTo($body);
	const $chart = $(`<div class="pm-gantt-chart"></div>`).appendTo($body);

	const project_control = frappe.ui.form.make_control({
		parent: $toolbar,
		df: {
			fieldtype: "Link",
			options: "Project Contract",
			label: __("Project Contract"),
			fieldname: "project_filter",
			description: __("Leave empty to show all projects with schedule data."),
		},
		render_input: true,
	});
	project_control.$wrapper.appendTo($toolbar);
	project_control.refresh();

	page.set_primary_action(__("Load schedule"), () => load_schedule());

	function load_schedule() {
		const project = project_control.get_value();
		frappe.call({
			method: "omnexa_projects_pm.api.cpm_timeline_calendar",
			args: { project: project || "" },
			freeze: true,
			callback: (r) => {
				const items = (r.message && r.message.items) || [];
				render_gantt(items);
			},
		});
	}

	function render_gantt(items) {
		$chart.empty();
		if (!items.length) {
			$chart.append(
				`<p class="text-muted">${__(
					"No timeline rows returned. Ensure WBS tasks have planned dates and (optionally) PM Baseline Snapshot or earliest planned_start for the project."
				)}</p>`
			);
			return;
		}
		const valid = items.filter((i) => i.start_date && i.end_date);
		if (!valid.length) {
			$chart.append(
				`<p class="text-muted">${__(
					"Tasks have offsets but no calendar dates. Set baseline or planned_start on WBS tasks."
				)}</p>`
			);
			return;
		}

		let t0str = valid[0].start_date;
		let t1str = valid[0].end_date;
		valid.forEach((i) => {
			if (i.start_date < t0str) t0str = i.start_date;
			if (i.end_date > t1str) t1str = i.end_date;
		});
		const rangeDays = Math.max(1, frappe.datetime.get_diff(t1str, t0str) + 1);

		valid.sort((a, b) =>
			(a.project || "").localeCompare(b.project || "") ||
			a.start_date.localeCompare(b.start_date) ||
			(a.id || "").localeCompare(b.id || "")
		);

		const $hint = $(
			`<div class="text-muted small" style="margin-bottom:8px">${__(
				"Bars use CPM calendar API (critical path in red). Float (days): hover a bar."
			)}</div>`
		);
		$chart.append($hint);

		valid.forEach((item) => {
			const startOff = frappe.datetime.get_diff(item.start_date, t0str);
			const barDays = frappe.datetime.get_diff(item.end_date, item.start_date) + 1;
			const leftPct = (startOff / rangeDays) * 100;
			const widthPct = Math.max(0.4, (barDays / rangeDays) * 100);
			const sub = [item.project, item.float_days != null ? `F:${item.float_days}` : ""]
				.filter(Boolean)
				.join(" · ");
			const row = $(`<div class="pm-gantt-row"></div>`).css({
				display: "flex",
				"align-items": "center",
				margin: "6px 0",
				"border-bottom": "1px solid var(--border-color)",
			});
			row.append(
				$("<div></div>")
					.css({ width: "220px", "flex-shrink": 0, "padding-right": "10px" })
					.append(
						`<div><strong>${frappe.utils.escape_html(
							item.title || item.id || ""
						)}</strong></div><div class="small text-muted">${frappe.utils.escape_html(
							sub
						)}</div>`
					)
			);
			const track = $("<div></div>").css({
				flex: 1,
				position: "relative",
				height: "24px",
				background: "var(--control-bg)",
				"border-radius": "4px",
			});
			const color = item.is_critical ? "var(--red)" : "var(--blue-500)";
			const bar = $("<div></div>")
				.css({
					position: "absolute",
					left: leftPct + "%",
					width: widthPct + "%",
					height: "100%",
					background: color,
					opacity: 0.88,
					"border-radius": "3px",
				})
				.attr(
					"title",
					`${item.start_date} → ${item.end_date} · ${__("Float")}: ${item.float_days ?? "-"}`
				);
			track.append(bar);
			row.append(track);
			$chart.append(row);
		});
	}

	load_schedule();
};
