from __future__ import unicode_literals
import frappe

from gst_automation.gst.doctype.gst_invoice_customization.gst_invoice_customization import (
	_create_custom_field,
)


def execute():
	"""Deploy all active GST custom fields to Sales Invoice.

	Reads the field mappings from GST Invoice Customization
	and creates Custom Field records on the Sales Invoice
	doctype for any active mapping with deploy_as_custom_field enabled.
	Reuses the shared _create_custom_field helper from the controller.
	"""
	try:
		doc = frappe.get_single("GST Invoice Customization")

		if not doc.get("field_mappings"):
			print("  ℹ️  No field mappings found, nothing to deploy")
			return

		success = 0
		skipped = 0
		failed = 0

		for mapping in doc.field_mappings:
			if not mapping.is_active or not mapping.deploy_as_custom_field:
				continue

			fieldname = mapping.source_fieldname.strip()
			if not fieldname:
				continue

			try:
				_create_custom_field(
					doctype="Sales Invoice",
					fieldname=fieldname,
					label=mapping.source_label or fieldname,
					fieldtype=mapping.fieldtype or "Data",
					options=mapping.options,
					default=mapping.default_value,
					reqd=mapping.reqd or 0,
					insert_after=mapping.insert_after_field or "taxes_and_charges",
				)
				success += 1
				print(f"  ✅ Deployed: {fieldname}")

			except frappe.DuplicateEntryError:
				skipped += 1
				print(f"  ℹ️  Skipped: {fieldname} (already exists)")

			except Exception as e:
				failed += 1
				print(f"  ❌ Failed: {fieldname} - {e}")

		print(
			f"  ✅ Deployment complete: {success} created, "
			f"{skipped} skipped, {failed} failed"
		)

	except Exception as e:
		print(f"  ❌ Deployment patch failed: {e}")
