from __future__ import unicode_literals
import frappe


def execute():
	"""Create Module Def for GST if it doesn't exist."""
	if not frappe.db.exists("Module Def", "GST"):
		module_def = frappe.get_doc(
			{
				"doctype": "Module Def",
				"module_name": "GST",
				"app_name": "gst_automation",
			}
		)
		module_def.insert()
		frappe.db.commit()
		print("Created 'GST' Module Def")
	else:
		print("'GST' Module Def already exists")
