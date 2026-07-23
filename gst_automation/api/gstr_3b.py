from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import now_datetime

from gst_automation.api.client import require_authenticated_client


# ─── Public API (whitelisted) ────────────────────────────


@frappe.whitelist()
def save_gstr3b(gstr3b_name):
	"""Save GSTR-3B return data to the GST portal.

	Takes a GSTR-3B Return document, builds the JSON payload
	from its child tables (outward supplies, ITC details, net
	liability), and submits it to the GST portal's save endpoint.

	Args:
		gstr3b_name: Name (ID) of the GSTR-3B Return document

	Returns:
		dict with success status, reference_id, and message
	"""
	doc = frappe.get_doc("GSTR-3B Return", gstr3b_name)

	if doc.docstatus != 1:
		frappe.throw(_("Please submit the GSTR-3B Return before saving to the GST portal."))

	client = require_authenticated_client(doc.company)

	try:
		payload = _build_gstr3b_payload(doc)

		response = client.post(
			"gstrs/gstr-3b",
			data=payload,
		)

		reference_id = response.get("reference_id")
		if reference_id:
			doc.db_set("filing_status", "JSON Generated")
			doc.db_set("generation_date", now_datetime())

		return {
			"success": True,
			"reference_id": reference_id,
			"message": _("GSTR-3B data saved to GST portal."),
		}

	except Exception as e:
		frappe.log_error(
			title=_("GSTR-3B Save Failed"),
			message=f"Document: {gstr3b_name}\nError: {str(e)}",
		)
		return {
			"success": False,
			"message": _("Failed to save GSTR-3B: {0}").format(str(e)),
		}


@frappe.whitelist()
def file_gstr3b(gstr3b_name, otp=None):
	"""File (submit) GSTR-3B return on the GST portal.

	After data is saved via `save_gstr3b()`, this endpoint
	formally files the return. An OTP may be required.

	Args:
		gstr3b_name: Name (ID) of the GSTR-3B Return document
		otp: Optional OTP for filing confirmation

	Returns:
		dict with success status, filing date, and message
	"""
	doc = frappe.get_doc("GSTR-3B Return", gstr3b_name)
	client = require_authenticated_client(doc.company)

	try:
		payload = {
			"gstin": client.gstin,
			"ret_period": doc.return_period,
		}
		if otp:
			payload["otp"] = otp

		response = client.post(
			"gstrs/gstr-3b/file",
			data=payload,
		)

		if response.get("status") == "FILED":
			doc.db_set("filing_status", "Filed")
			doc.db_set("filing_date", now_datetime().date())

		return {
			"success": True,
			"filing_date": str(now_datetime().date()),
			"message": _("GSTR-3B filed successfully."),
		}

	except Exception as e:
		frappe.log_error(
			title=_("GSTR-3B Filing Failed"),
			message=f"Document: {gstr3b_name}\nError: {str(e)}",
		)
		return {
			"success": False,
			"message": _("Failed to file GSTR-3B: {0}").format(str(e)),
		}


@frappe.whitelist()
def check_gstr3b_status(return_period, company=None):
	"""Check the filing status of GSTR-3B for a given period.

	Args:
		return_period: Period in MMYYYY format
		company: Optional company name

	Returns:
		dict with status and details from GST portal
	"""
	client = require_authenticated_client(company)

	try:
		response = client.get(
			f"gstrs/gstr-3b/{return_period}",
		)

		return {
			"success": True,
			"status": response.get("status"),
			"data": response,
		}

	except Exception as e:
		return {
			"success": False,
			"message": _("Failed to check GSTR-3B status: {0}").format(str(e)),
		}


# ─── Payload Builder ─────────────────────────────────────


def _build_gstr3b_payload(doc):
	"""Build the GSTR-3B JSON payload from the document's child tables.

	Constructs the standard GSTN-compliant JSON structure
	for GSTR-3B summary return filing.
	"""
	payload = {
		"gstin": doc.company_gstin,
		"ret_period": doc.return_period,
		"sup_details": _build_outward_supplies(doc),
		"itc_details": _build_itc_details(doc),
		"payment": _build_net_liability(doc),
	}
	return payload


def _build_outward_supplies(doc):
	"""Build outward supply details section."""
	supplies = {}

	# 3.1(a) Outward taxable supplies
	if doc.get("outward_taxable_supplies"):
		for row in doc.outward_taxable_supplies:
			supplies[row.description] = {
				"taxable_value": row.taxable_value or 0,
				"cgst": row.cgst or 0,
				"sgst": row.sgst or 0,
				"igst": row.igst or 0,
				"cess": row.cess or 0,
			}

	# 3.1(b) Zero rated supplies
	if doc.get("outward_zero_rated_supplies"):
		for row in doc.outward_zero_rated_supplies:
			supplies[row.description] = {
				"taxable_value": row.taxable_value or 0,
				"cgst": row.cgst or 0,
				"sgst": row.sgst or 0,
				"igst": row.igst or 0,
				"cess": row.cess or 0,
			}

	return supplies


def _build_itc_details(doc):
	"""Build ITC details section (Table 4)."""
	itc_data = {}
	if doc.get("itc_details"):
		for row in doc.itc_details:
			itc_data[row.description] = {
				"itc_available": row.itc_available or 0,
				"itc_claimed": row.itc_claimed or 0,
				"itc_reversed": row.itc_reversed or 0,
				"net_itc": row.net_itc or 0,
			}
	return itc_data


def _build_net_liability(doc):
	"""Build payment / net liability section."""
	payment_data = {}
	if doc.get("net_liability"):
		for row in doc.net_liability:
			payment_data[row.description] = {
				"tax": row.tax_amount or 0,
				"interest": row.interest or 0,
				"late_fee": row.late_fee or 0,
				"total": row.total or 0,
			}
	return payment_data
