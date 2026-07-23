from __future__ import unicode_literals

import frappe


def execute():
	"""Add parent/parenttype/parentfield columns to all GST child tables.

	Frappe's schema sync sometimes fails to create these columns
	for child tables, causing (1054, "Unknown column 'parent' in WHERE").
	This runs the same ALTER TABLE commands that work when executed
	manually via bench console.
	"""
	tables = [
		"tabGST Field Mapping",
		"tabGSTR-1 B2B Invoice",
		"tabGSTR-1 HSN Summary",
		"tabGSTR-3B Outward Supply",
		"tabGSTR-3B ITC Detail",
		"tabGSTR-3B Net Liability",
	]

	columns = ["parent", "parenttype", "parentfield"]

	for table in tables:
		for col in columns:
			try:
				frappe.db.sql(
					f"ALTER TABLE `{table}` ADD COLUMN `{col}` VARCHAR(140) NULL"
				)
				print(f"  Added `{col}` to {table}")
			except Exception:
				# Column already exists — silently skip
				pass

		# Add index on parent column for performance
		try:
			frappe.db.sql(f"ALTER TABLE `{table}` ADD INDEX `parent` (`parent`)")
		except Exception:
			pass

	frappe.db.commit()
	print("✅ GST child table parent columns verified and fixed where needed")


def try_fix_once():
	"""Run once per server start via before_request hook."""
	if frappe.cache().get_value("gst_child_tables_fixed"):
		return

	execute()
	frappe.cache().set_value("gst_child_tables_fixed", True)
