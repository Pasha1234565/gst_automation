// Copyright (c) 2026, Your Company and contributors
// For license information, please see license.txt

frappe.ui.form.on('GSTR-1 Return', {
	generate_json_button: function(frm) {
		if (frm.doc.docstatus === 0 && !frm.doc.__islocal) {
			frappe.confirm(
				__('Generate JSON will save a draft JSON file for manual upload to the GST portal. Continue?'),
				function() {
					frm.call({
						method: 'gst_automation.gst.doctype.gstr_1_return.gstr_1_return.generate_gstr1_json',
						args: {
							'docname': frm.doc.name
						},
						btn: frm.savesubmit_btn,
						callback: function(r) {
							if (!r.exc) {
								frm.refresh_field('json_file');
								frm.refresh_field('filing_status');
								frm.refresh_field('generation_date');
								frappe.msgprint({
									title: __('JSON Generated'),
									indicator: 'green',
									message: r.message
								});
							}
						}
					});
				}
			);
		} else {
			frappe.msgprint(__('Save the document first before generating JSON.'));
		}
	}
});
