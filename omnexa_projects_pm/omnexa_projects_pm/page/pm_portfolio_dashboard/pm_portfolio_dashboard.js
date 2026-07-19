frappe.pages["pm-portfolio-dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("PM Portfolio Dashboard"),
		single_column: true,
	});

	const $root = $(`
		<div class="pm-portfolio-page">
			<div class="row mb-3">
				<div class="col-md-4 company-field"></div>
				<div class="col-md-4 branch-field"></div>
				<div class="col-md-4"><button class="btn btn-primary btn-refresh">${__("Refresh")}</button></div>
			</div>
			<div class="kpi-row row mb-4"></div>
			<div class="compliance-row mb-3"></div>
			<div class="contracts-table"></div>
		</div>
	`).appendTo(page.main);

	const company = frappe.ui.form.make_control({
		parent: $root.find(".company-field"),
		df: { fieldtype: "Link", options: "Company", label: __("Company"), reqd: 1 },
		render_input: true,
	});
	const branch = frappe.ui.form.make_control({
		parent: $root.find(".branch-field"),
		df: { fieldtype: "Link", options: "Branch", label: __("Branch") },
		render_input: true,
	});

	frappe.db.get_value("Company", { is_group: 0 }, "name").then((r) => {
		if (r?.message?.name) {
			company.set_value(r.message.name);
			load();
		}
	});

	function load() {
		const c = company.get_value();
		if (!c) return;
		frappe.call({
			method: "omnexa_projects_pm.portfolio_api.get_portfolio_dashboard",
			args: { company: c, branch: branch.get_value() },
			freeze: true,
			callback(r) {
				render(r.message || {});
			},
		});
		frappe.call({
			method: "omnexa_projects_pm.pm_compliance.get_pm_compliance_score",
			callback(r) {
				const d = r.message || {};
				$root.find(".compliance-row").html(
					`<p class="text-muted">${__("PM Compliance (ISO 21500 / PMBOK)")}: <b>${d.weighted_score || 0} / 5.00</b></p>`
				);
			},
		});
	}

	function render(data) {
		const cards = [
			[data.contract_count, __("Projects"), "primary"],
			[data.portfolio_spi, __("Portfolio SPI"), "success"],
			[data.on_track_contracts, __("On Track"), "info"],
			[data.at_risk_contracts, __("At Risk"), "warning"],
			[data.delayed_contracts, __("Delayed"), "danger"],
			[data.open_change_requests, __("Open Changes"), "secondary"],
		];
		let html = "";
		cards.forEach(([val, label, color]) => {
			html += `<div class="col-md-2"><div class="card bg-${color} text-white p-3 text-center"><h4>${val ?? 0}</h4><small>${label}</small></div></div>`;
		});
		$root.find(".kpi-row").html(html);

		const rows = data.contracts || [];
		let tbl = `<table class="table table-bordered table-sm"><thead><tr>
			<th>${__("Project")}</th><th>${__("Status")}</th><th>${__("BAC")}</th>
			<th>SPI</th><th>CPI</th><th>${__("Schedule")}</th><th>${__("Cost")}</th></tr></thead><tbody>`;
		rows.forEach((row) => {
			tbl += `<tr>
				<td><a href="/app/project-contract/${row.name}">${frappe.utils.escape_html(row.title || row.name)}</a></td>
				<td>${row.status || ""}</td>
				<td>${frappe.format(row.bac || 0, { fieldtype: "Currency" })}</td>
				<td>${row.spi ?? ""}</td>
				<td>${row.cpi ?? ""}</td>
				<td>${row.schedule_health || ""}</td>
				<td>${row.cost_health || ""}</td>
			</tr>`;
		});
		tbl += "</tbody></table>";
		$root.find(".contracts-table").html(tbl);
	}

	$root.find(".btn-refresh").on("click", load);
	company.$input.on("change", load);
	branch.$input.on("change", load);
};
