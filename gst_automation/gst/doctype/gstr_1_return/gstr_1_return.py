from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from gst_automation.api.gstr_1 import _build_gstr1_payload


class GSTR1Return(Document):
	def validate(self):
		self.validate_return_period_format()
		self.validate_duplicate_period()
		self.set_company_gstin()

	def set_company_gstin(self):
		"""Auto-populate company_gstin from GST Settings if not set."""
		if not self.company_gstin:
			try:
				gst_settings = frappe.get_single("GST Settings")
				if gst_settings.company_gstin:
					self.company_gstin = gst_settings.company_gstin
			except Exception as e:
				# GST Settings may not exist yet (before bench migrate)
				# or there may be another unexpected error.
				# Log it and continue so submission is not blocked.
				frappe.log_error(
					title="GST Settings Error (GSTR-1)",
					message=f"Document: {self.name}\nError: {str(e)}\n{frappe.get_traceback()}"
				)

	def before_submit(self):
		self.filing_status = "Filed"
		self.filing_date = now_datetime().date()

	def on_cancel(self):
		self.filing_status = "Not Filed"
		self.filing_date = None

	def validate_return_period_format(self):
		"""Validate return period is in MMYYYY format."""
		if not self.return_period or len(self.return_period) != 6:
			frappe.throw(
				frappe._("Return Period must be in MMYYYY format (e.g., 042026 for April 2026)")
			)

		month = self.return_period[:2]
		year = self.return_period[2:]

		try:
			m = int(month)
			y = int(year)
			if m < 1 or m > 12:
				raise ValueError
			if y < 2000 or y > 2100:
				raise ValueError
		except ValueError:
			frappe.throw(
				frappe._("Return Period must be a valid MMYYYY (month 01-12, year 2000-2100)")
			)

	def validate_duplicate_period(self):
		"""Prevent duplicate GSTR-1 for the same company and period."""
		if self.is_new():
			existing = frappe.db.exists(
				"GSTR-1 Return",
				{
					"company": self.company,
					"return_period": self.return_period,
					"docstatus": ["!=", 2],
				},
			)
			if existing:
				frappe.throw(
					frappe._(
						"GSTR-1 Return already exists for {0} period {1}"
					).format(self.company, self.return_period)
				)


# ─── Whitelisted Endpoints ──────────────────────────────


@frappe.whitelist()
def generate_gstr1_json(docname):
	"""Generate a GSTN-compliant JSON file for the GSTR-1 Return.

	Builds the JSON payload from the document's child tables (B2B
	invoices, HSN summary), creates a File attachment, and updates
	the json_file, filing_status and generation_date fields.

	Args:
	    docname: Name (ID) of the GSTR-1 Return document

	Returns:
	    str: Success message with file URL
	"""
	doc = frappe.get_doc("GSTR-1 Return", docname)

	payload = _build_gstr1_payload(doc)

	json_str = frappe.as_json(payload, indent=2)

	file_name = "GSTR1_{}_{}.json".format(doc.return_period, doc.company.replace(" ", "_"))

	_file = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": file_name,
			"attached_to_doctype": "GSTR-1 Return",
			"attached_to_name": doc.name,
			"content": json_str,
			"is_private": 0,
		}
	)
	_file.flags.ignore_permissions = True
	_file.insert()

	doc.db_set("json_file", _file.file_url)
	doc.db_set("filing_status", "JSON Generated")
	doc.db_set("generation_date", now_datetime())

	return _("JSON file attached: {0}").format(_file.file_url)
