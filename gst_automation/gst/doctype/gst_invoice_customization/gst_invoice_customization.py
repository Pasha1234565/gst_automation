from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class GSTInvoiceCustomization(Document):
	"""Controller for GST Invoice Customization.

	Manages field mappings between Sales Invoice and GST returns,
	and deploys custom fields to the Sales Invoice doctype.
	"""

	def validate(self):
		self.validate_field_mappings()

	def validate_field_mappings(self):
		"""Validate field mapping entries."""
		if self.get("field_mappings"):
			seen = set()
			for mapping in self.field_mappings:
				if not mapping.source_fieldname:
					continue
				key = (mapping.source_fieldname, mapping.target_return)
				if key in seen:
					frappe.msgprint(
						_("Duplicate mapping for field '{0}' in return '{1}'").format(
							mapping.source_fieldname, mapping.target_return
						),
						alert=True,
					)
				seen.add(key)

	def deploy_custom_fields(self):
		"""Deploy custom fields to Sales Invoice based on active field mappings.

		Iterates through active field mappings with
		`deploy_as_custom_field` enabled and creates Custom Field
		records on the Sales Invoice doctype.
		"""
		log = []
		success_count = 0
		skip_count = 0

		if not self.get("field_mappings"):
			frappe.msgprint(_("No field mappings defined. Add mappings first."))
			return

		for mapping in self.field_mappings:
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
				log.append(f"✅ Created: {fieldname} ({mapping.source_label})")
				success_count += 1

			except frappe.DuplicateEntryError:
				log.append(f"ℹ️  Skipped: {fieldname} (already exists)")
				skip_count += 1

			except Exception as e:
				log.append(f"❌ Failed: {fieldname} - {str(e)}")

		# Update deployment log
		self.db_set("last_deployed", now_datetime())
		self.db_set("deployment_log", "\n".join(log))

		frappe.msgprint(
			_("Deployment complete: {0} created, {1} skipped").format(
				success_count, skip_count
			)
		)
		return log

	def reset_to_default_mappings(self):
		"""Reset field mappings to the default set.

		Replaces all current mappings with a standard set
		of GST-related Sales Invoice field mappings.
		"""
		self.set("field_mappings", [])
		defaults = get_default_field_mappings()
		for d in defaults:
			self.append("field_mappings", d)

		frappe.msgprint(_("Field mappings reset to defaults."))


def _create_custom_field(doctype, fieldname, label, fieldtype, **kwargs):
	"""Create a Custom Field if it doesn't already exist."""
	if frappe.db.exists("Custom Field", f"{doctype}-{fieldname}"):
		raise frappe.DuplicateEntryError(f"Custom Field {doctype}-{fieldname} already exists")

	custom_field = frappe.get_doc(
		{
			"doctype": "Custom Field",
			"dt": doctype,
			"fieldname": fieldname,
			"label": label,
			"fieldtype": fieldtype,
			"options": kwargs.get("options"),
			"default": kwargs.get("default"),
			"reqd": kwargs.get("reqd", 0),
			"insert_after": kwargs.get("insert_after", "taxes_and_charges"),
		}
	)
	custom_field.flags.ignore_permissions = True
	custom_field.flags.ignore_validate = True
	custom_field.insert()
	frappe.db.commit()
	return custom_field


def get_default_field_mappings():
	"""Return the default set of GST-related Sales Invoice field mappings."""
	return [
		{
			"source_fieldname": "custom_gst_category",
			"source_label": "GST Category",
			"fieldtype": "Select",
			"options": "Registered Regular\nRegistered Composition\nUnregistered\nSEZ\nOverseas\nDeemed Export",
			"default_value": "Registered Regular",
			"reqd": 1,
			"target_return": "Both",
			"target_section": "Invoice",
			"target_fieldname": "gst_category",
			"mapping_type": "Direct",
			"insert_after_field": "customer_gstin",
		},
		{
			"source_fieldname": "custom_place_of_supply",
			"source_label": "Place of Supply",
			"fieldtype": "Data",
			"reqd": 1,
			"target_return": "Both",
			"target_section": "Invoice",
			"target_fieldname": "place_of_supply",
			"mapping_type": "Direct",
			"insert_after_field": "custom_gst_category",
		},
		{
			"source_fieldname": "custom_invoice_type",
			"source_label": "Invoice Type",
			"fieldtype": "Select",
			"options": "Regular\nSEZ\nE-Commerce\nExport",
			"default_value": "Regular",
			"target_return": "GSTR-1",
			"target_section": "B2B",
			"target_fieldname": "invoice_type",
			"mapping_type": "Direct",
			"insert_after_field": "custom_place_of_supply",
		},
		{
			"source_fieldname": "custom_ecommerce_gstin",
			"source_label": "E-Commerce GSTIN",
			"fieldtype": "Data",
			"target_return": "GSTR-1",
			"target_section": "B2B",
			"target_fieldname": "ecommerce_gstin",
			"mapping_type": "Direct",
			"insert_after_field": "custom_invoice_type",
		},
		{
			"source_fieldname": "custom_reverse_charge",
			"source_label": "Reverse Charge",
			"fieldtype": "Check",
			"default_value": "0",
			"target_return": "Both",
			"target_section": "Invoice",
			"target_fieldname": "reverse_charge",
			"mapping_type": "Direct",
			"insert_after_field": "custom_ecommerce_gstin",
		},
		{
			"source_fieldname": "custom_port_code",
			"source_label": "Port Code",
			"fieldtype": "Data",
			"target_return": "GSTR-1",
			"target_section": "Export",
			"target_fieldname": "port_code",
			"mapping_type": "Direct",
			"insert_after_field": "custom_reverse_charge",
		},
		{
			"source_fieldname": "custom_shipping_bill_number",
			"source_label": "Shipping Bill Number",
			"fieldtype": "Data",
			"target_return": "GSTR-1",
			"target_section": "Export",
			"target_fieldname": "shipping_bill_no",
			"mapping_type": "Direct",
			"insert_after_field": "custom_port_code",
		},
		{
			"source_fieldname": "custom_shipping_bill_date",
			"source_label": "Shipping Bill Date",
			"fieldtype": "Date",
			"target_return": "GSTR-1",
			"target_section": "Export",
			"target_fieldname": "shipping_bill_date",
			"mapping_type": "Direct",
			"insert_after_field": "custom_shipping_bill_number",
		},
	]


# ─── Whitelisted Endpoints ──────────────────────────────


@frappe.whitelist()
def deploy_custom_fields():
	"""Deploy GST custom fields to Sales Invoice.

	Called via the 'Deploy Custom Fields' button on the
	GST Invoice Customization form.
	"""
	doc = frappe.get_single("GST Invoice Customization")
	return doc.deploy_custom_fields()


@frappe.whitelist()
def reset_mappings():
	"""Reset field mappings to defaults.

	Called via the 'Reset to Default Mappings' button.
	"""
	doc = frappe.get_single("GST Invoice Customization")
	doc.reset_to_default_mappings()
	doc.save()
	return {"success": True, "message": _("Mappings reset to defaults.")}
