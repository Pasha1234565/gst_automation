from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import now_datetime

from gst_automation.api.client import require_authenticated_client


# ─── Public API (whitelisted) ────────────────────────────


@frappe.whitelist()
def save_gstr1(gstr1_name):
	"""Save GSTR-1 return data to the GST portal.

	Takes a GSTR-1 Return document, builds the JSON payload
	from its child tables (B2B invoices, HSN summary), and
	submits it to the GST portal's save endpoint.

	Args:
		gstr1_name: Name (ID) of the GSTR-1 Return document

	Returns:
		dict with success status, reference_id, and message
	"""
	doc = frappe.get_doc("GSTR-1 Return", gstr1_name)

	if doc.docstatus != 1:
		frappe.throw(_("Please submit the GSTR-1 Return before saving to the GST portal."))

	client = require_authenticated_client(doc.company)

	try:
		payload = _build_gstr1_payload(doc)

		response = client.post(
			"gstrs/gstr-1",
			data=payload,
		)

		reference_id = response.get("reference_id")
		if reference_id:
			doc.db_set("filing_status", "JSON Generated")
			doc.db_set("generation_date", now_datetime())

		return {
			"success": True,
			"reference_id": reference_id,
			"message": _("GSTR-1 data saved to GST portal."),
		}

	except Exception as e:
		frappe.log_error(
			title=_("GSTR-1 Save Failed"),
			message=f"Document: {gstr1_name}\nError: {str(e)}",
		)
		return {
			"success": False,
			"message": _("Failed to save GSTR-1: {0}").format(str(e)),
		}


@frappe.whitelist()
def file_gstr1(gstr1_name, otp=None):
	"""File (submit) GSTR-1 return on the GST portal.

	After data is saved via `save_gstr1()`, this endpoint
	formally files the return on the GST portal. An OTP
	may be required for confirmation.

	Args:
		gstr1_name: Name (ID) of the GSTR-1 Return document
		otp: Optional OTP for filing confirmation

	Returns:
		dict with success status, filing date, and message
	"""
	doc = frappe.get_doc("GSTR-1 Return", gstr1_name)
	client = require_authenticated_client(doc.company)

	try:
		payload = {
			"gstin": client.gstin,
			"ret_period": doc.return_period,
		}
		if otp:
			payload["otp"] = otp

		response = client.post(
			"gstrs/gstr-1/file",
			data=payload,
		)

		if response.get("status") == "FILED":
			doc.db_set("filing_status", "Filed")
			doc.db_set("filing_date", now_datetime().date())

		return {
			"success": True,
			"filing_date": str(now_datetime().date()),
			"message": _("GSTR-1 filed successfully."),
		}

	except Exception as e:
		frappe.log_error(
			title=_("GSTR-1 Filing Failed"),
			message=f"Document: {gstr1_name}\nError: {str(e)}",
		)
		return {
			"success": False,
			"message": _("Failed to file GSTR-1: {0}").format(str(e)),
		}


@frappe.whitelist()
def check_gstr1_status(return_period, company=None):
	"""Check the filing status of GSTR-1 for a given period.

	Args:
		return_period: Period in MMYYYY format
		company: Optional company name

	Returns:
		dict with status and details from GST portal
	"""
	client = require_authenticated_client(company)

	try:
		response = client.get(
			f"gstrs/gstr-1/{return_period}",
		)

		return {
			"success": True,
			"status": response.get("status"),
			"data": response,
		}

	except Exception as e:
		return {
			"success": False,
			"message": _("Failed to check GSTR-1 status: {0}").format(str(e)),
		}


# ─── Payload Builder ─────────────────────────────────────


def _build_gstr1_payload(doc):
	"""Build the GSTR-1 JSON payload from the document's child tables.

	This constructs the standard GSTN-compliant JSON structure
	for GSTR-1 return filing.
	"""
	payload = {
		"gstin": doc.company_gstin,
		"ret_period": doc.return_period,
		"b2b": _build_b2b_invoices(doc),
		"hsn": _build_hsn_summary(doc),
	}
	return payload


def _build_b2b_invoices(doc):
	"""Build B2B invoice section of GSTR-1 payload."""
	b2b_data = []
	if doc.get("b2b_invoices"):
		for inv in doc.b2b_invoices:
			b2b_data.append({
				"invoice_no": inv.sales_invoice,
				"invoice_date": str(inv.invoice_date) if inv.invoice_date else None,
				"customer_gstin": inv.customer_gstin,
				"taxable_value": inv.taxable_value or 0,
				"cgst": inv.cgst_amount or 0,
				"sgst": inv.sgst_amount or 0,
				"igst": inv.igst_amount or 0,
				"cess": inv.cess_amount or 0,
			})
	return b2b_data


def _build_hsn_summary(doc):
	"""Build HSN-wise summary section of GSTR-1 payload."""
	hsn_data = []
	if doc.get("hsn_summary"):
		for row in doc.hsn_summary:
			hsn_data.append({
				"hsn_code": row.hsn_code,
				"description": row.description,
				"uqc": row.uqc or "NOS",
				"quantity": row.total_quantity or 0,
				"taxable_value": row.taxable_value or 0,
				"cgst_rate": row.cgst_rate or 0,
				"sgst_rate": row.sgst_rate or 0,
				"igst_rate": row.igst_rate or 0,
			})
	return hsn_data
