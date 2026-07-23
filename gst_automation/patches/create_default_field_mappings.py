from __future__ import unicode_literals
import frappe

from gst_automation.gst.doctype.gst_invoice_customization.gst_invoice_customization import (
	get_default_field_mappings,
)
from gst_automation.patches import get_or_create_single


def execute():
	"""Seed default field mappings into GST Invoice Customization.

	Inserts child table rows directly into the GST Field Mapping
	table, bypassing doc.save() which triggers check_if_latest() and
	causes SQL errors on Single DocTypes with Link fields.
	"""
	try:
		doc = get_or_create_single("GST Invoice Customization")

		# Check if mappings already exist via direct DB query
		existing = frappe.db.count(
			"GST Field Mapping",
			{"parent": doc.name, "parenttype": "GST Invoice Customization"},
		)
		if existing > 0:
			print(f"  ℹ️  {existing} field mappings already exist, skipping")
			return

		defaults = get_default_field_mappings()
		for i, mapping in enumerate(defaults):
			child = frappe.get_doc(
				{
					"doctype": "GST Field Mapping",
					"parent": doc.name,
					"parenttype": "GST Invoice Customization",
					"parentfield": "field_mappings",
					"idx": i + 1,
					"source_fieldname": mapping["source_fieldname"],
					"source_label": mapping.get("source_label"),
					"fieldtype": mapping.get("fieldtype", "Data"),
					"options": mapping.get("options"),
					"default_value": mapping.get("default_value"),
					"reqd": mapping.get("reqd", 0),
					"target_return": mapping.get("target_return", "Both"),
					"target_section": mapping.get("target_section"),
					"target_fieldname": mapping.get("target_fieldname"),
					"mapping_type": mapping.get("mapping_type", "Direct"),
					"deploy_as_custom_field": 1,
					"insert_after_field": mapping.get("insert_after_field"),
					"is_active": 1,
				}
			)
			child.flags.ignore_permissions = True
			child.flags.ignore_validate = True
			child.insert()

		frappe.db.commit()
		print(f"  ✅ Seeded {len(defaults)} default field mappings")

	except Exception as e:
		frappe.db.rollback()
		print(f"  ❌ Failed to seed field mappings: {e}")
		raise
