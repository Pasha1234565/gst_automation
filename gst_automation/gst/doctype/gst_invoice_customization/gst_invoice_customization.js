frappe.ui.form.on("GST Invoice Customization", {
	refresh: function (frm) {
		// Deploy Custom Fields button
		frm.add_custom_button(
			__("Deploy Custom Fields"),
			function () {
				frappe.call({
					method:
						"gst_automation.gst.doctype.gst_invoice_customization.gst_invoice_customization.deploy_custom_fields",
					callback: function (r) {
						if (r.message) {
							frappe.msgprint({
								title: __("Deployment Log"),
								message: r.message.join
									? r.message.join("<br>")
									: r.message,
								indicator: "green",
							});
							frm.reload_doc();
						}
					},
				});
			},
			__("Actions")
		);

		// Reset to Default Mappings button
		frm.add_custom_button(
			__("Reset to Default Mappings"),
			function () {
				frappe.confirm(
					__(
						"This will replace all current field mappings with the default set. Continue?"
					),
					function () {
						frappe.call({
							method:
								"gst_automation.gst.doctype.gst_invoice_customization.gst_invoice_customization.reset_mappings",
							callback: function (r) {
								if (r.message && r.message.success) {
									frappe.msgprint({
										title: __("Mappings Reset"),
										message: __(
											"Field mappings have been reset to defaults."
										),
										indicator: "green",
									});
									frm.reload_doc();
								}
							},
						});
					}
				);
			},
			__("Actions")
		);
	},
});
