from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, flt


class GSTR3BReturn(Document):
	def validate(self):
		self.validate_return_period_format()
		self.validate_duplicate_period()
		self.set_company_gstin()

	def set_company_gstin(self):
		"""Auto-populate company_gstin from GST Settings if not set."""
		if not self.company_gstin:
			gst_settings = frappe.get_single("GST Settings")
			if gst_settings.company_gstin:
				self.company_gstin = gst_settings.company_gstin

	def before_submit(self):
		self.filing_status = "Filed"
		self.filing_date = now_datetime().date()
		self.calculate_totals()

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
		"""Prevent duplicate GSTR-3B for the same company and period."""
		if self.is_new():
			existing = frappe.db.exists(
				"GSTR-3B Return",
				{
					"company": self.company,
					"return_period": self.return_period,
					"docstatus": ["!=", 2],
				},
			)
			if existing:
				frappe.throw(
					frappe._(
						"GSTR-3B Return already exists for {0} period {1}"
					).format(self.company, self.return_period)
				)

	def calculate_totals(self):
		"""Calculate total tax payable and paid from child tables."""
		total_payable = 0.0
		if self.get("net_liability"):
			for row in self.net_liability:
				total_payable += flt(row.total)

		self.total_tax_payable = total_payable
		self.total_tax_paid = total_payable  # Default: assume full payment on filing
