from __future__ import unicode_literals
import frappe

from gst_automation.gst.doctype.gst_invoice_customization.gst_invoice_customization import (
	get_default_field_mappings,
)
from gst_automation.patches import get_or_create_single


def execute():
	"""Seed default field mappings into GST Invoice Customization.

	This runs once to populate the initial set of GST-related
	Sales Invoice field mappings with their GSTR-1/GSTR-3B
	target mappings.
	"""
	try:
		doc = get_or_create_single("GST Invoice Customization")

		# Skip if mappings already exist
		if doc.get("field_mappings") and len(doc.field_mappings) > 0:
			print("  ℹ️  Field mappings already exist, skipping")
			return

		defaults = get_default_field_mappings()
		for mapping in defaults:
			doc.append("field_mappings", mapping)

		doc.flags.ignore_permissions = True
		doc.flags.ignore_validate = True
		doc.save()
		frappe.db.commit()
		print(f"  ✅ Seeded {len(defaults)} default field mappings")

	except Exception as e:
		frappe.db.rollback()
		print(f"  ❌ Failed to seed field mappings: {e}")
		raise



