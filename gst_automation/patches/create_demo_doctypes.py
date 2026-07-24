from __future__ import unicode_literals

import frappe
from frappe.utils import getdate, add_months, now_datetime, today


def execute():
	"""Seed comprehensive demo data for GST DocTypes.

	Creates sample GSTR-1 and GSTR-3B returns across 6 return periods
	with various filing statuses, populated child tables, and realistic
	amounts — so that workspace charts and reports have data to display.
	"""

	if frappe.db.count("GSTR-1 Return") > 0 or frappe.db.count("GSTR-3B Return") > 0:
		print("  ℹ️  Demo data already exists — skipping")
		return

	company = get_or_create_demo_company()

	print("  🏢 Using company: {}".format(company))

	# ── Generate data for 6 return periods ──────────────
	periods = [
		"012026",  # Jan 2026
		"022026",  # Feb 2026
		"032026",  # Mar 2026
		"042026",  # Apr 2026
		"052026",  # May 2026
		"062026",  # Jun 2026
	]

	# Staggered filing statuses so the dashboard shows variety
	status_map = {
		"012026": {"gstr1": "Filed", "gstr3b": "Filed"},
		"022026": {"gstr1": "Filed", "gstr3b": "Filed"},
		"032026": {"gstr1": "Filed", "gstr3b": "JSON Generated"},
		"042026": {"gstr1": "JSON Generated", "gstr3b": "Not Filed"},
		"052026": {"gstr1": "Not Filed", "gstr3b": "Not Filed"},
		"062026": {"gstr1": "Not Filed", "gstr3b": "Not Filed"},
	}

	for period in periods:
		statuses = status_map[period]
		create_gstr1_return(company, period, statuses["gstr1"])
		create_gstr3b_return(company, period, statuses["gstr3b"])

	print("  ✅ Demo data created: 6 GSTR-1 + 6 GSTR-3B returns")


# ── Helpers ─────────────────────────────────────────────


def get_or_create_demo_company():
	"""Return an existing company name or create a minimal demo company."""
	company = frappe.db.get_value("Company", {"country": "India"}, "name")
	if company:
		return company

	# Create a fallback demo company
	if not frappe.db.exists("Company", "Demo GST Company"):
		doc = frappe.new_doc("Company")
		doc.company_name = "Demo GST Company"
		doc.country = "India"
		doc.default_currency = "INR"
		doc.flags.ignore_mandatory = True
		doc.flags.ignore_permissions = True
		doc.insert()
		frappe.db.commit()
		print("  ✅ Created demo company: Demo GST Company")
	return "Demo GST Company"


def get_company_gstin(company):
	"""Get GSTIN for a company from GST Settings or generate a demo one."""
	gstin = frappe.db.get_value(
		"GST Settings", "GST Settings", "company_gstin"
	)
	if gstin:
		return gstin
	# Generate a dummy GSTIN based on company name hash
	return "29AAAAA0000A1Z5"  # Standard demo GSTIN for India


def build_filing_date(period, status):
	"""Return a realistic filing date for filed returns."""
	if status == "Filed":
		month = int(period[:2])
		year = int("20" + period[2:])
		# Assume filed by 20th of the following month
		filing_month = month + 1
		filing_year = year
		if filing_month > 12:
			filing_month = 1
			filing_year += 1
		date_str = "{:04d}-{:02d}-{:02d}".format(filing_year, filing_month, 20)
		return getdate(date_str)
	return None


# ── GSTR-1 Data ────────────────────────────────────────


def create_gstr1_return(company, period, filing_status):
	"""Create a GSTR-1 Return with child tables and summary values."""

	gstin = get_company_gstin(company)

	# Amounts that grow over the fiscal year (simulating business growth)
	base_value = {
		"012026": 1250000,
		"022026": 1180000,
		"032026": 1420000,
		"042026": 1350000,
		"052026": 1510000,
		"062026": 1480000,
	}[period]

	tax_5 = round(base_value * 0.30, 2)
	tax_12 = round(base_value * 0.40, 2)
	tax_18 = round(base_value * 0.25, 2)
	tax_28 = round(base_value * 0.05, 2)

	total_taxable = tax_5 + tax_12 + tax_18 + tax_28
	total_tax = round(
		tax_5 * 0.025 * 2   # 5% = 2.5% CGST + 2.5% SGST
		+ tax_12 * 0.06 * 2  # 12% = 6% CGST + 6% SGST
		+ tax_18 * 0.09 * 2  # 18% = 9% CGST + 9% SGST
		+ tax_28 * 0.14 * 2,  # 28% = 14% CGST + 14% SGST
		2,
	)

	doc = frappe.new_doc("GSTR-1 Return")
	doc.company = company
	doc.company_gstin = gstin
	doc.return_period = period
	doc.filing_status = filing_status
	doc.filing_date = build_filing_date(period, filing_status)
	doc.total_b2b_invoices = 4
	doc.total_b2c_invoices = 0
	doc.total_credit_notes = 0
	doc.total_taxable_value = total_taxable
	doc.total_tax_amount = total_tax

	# ── B2B Invoice child rows ──
	b2b_data = [
		{
			"customer_name": "Tech Solutions Pvt Ltd",
			"customer_gstin": "27AABCT1234A1Z5",
			"invoice_date": getdate(get_invoice_date(period, 5)),
			"invoice_value": round(tax_5 + tax_5 * 0.05, 2),
			"taxable_value": tax_5,
			"cgst_amount": round(tax_5 * 0.025, 2),
			"sgst_amount": round(tax_5 * 0.025, 2),
			"igst_amount": 0,
			"cess_amount": 0,
			"total_tax": round(tax_5 * 0.05, 2),
		},
		{
			"customer_name": "Modern Retailers India",
			"customer_gstin": "29AADFM5678A1Z1",
			"invoice_date": getdate(get_invoice_date(period, 12)),
			"invoice_value": round(tax_12 + tax_12 * 0.12, 2),
			"taxable_value": tax_12,
			"cgst_amount": round(tax_12 * 0.06, 2),
			"sgst_amount": round(tax_12 * 0.06, 2),
			"igst_amount": 0,
			"cess_amount": 0,
			"total_tax": round(tax_12 * 0.12, 2),
		},
		{
			"customer_name": "Industrial Goods Corp",
			"customer_gstin": "07AAACI9012A1Z3",
			"invoice_date": getdate(get_invoice_date(period, 18)),
			"invoice_value": round(tax_18 + tax_18 * 0.18, 2),
			"taxable_value": tax_18,
			"cgst_amount": round(tax_18 * 0.09, 2),
			"sgst_amount": round(tax_18 * 0.09, 2),
			"igst_amount": 0,
			"cess_amount": 0,
			"total_tax": round(tax_18 * 0.18, 2),
		},
		{
			"customer_name": "Luxury Goods Trading",
			"customer_gstin": "33AACCL3456A1Z7",
			"invoice_date": getdate(get_invoice_date(period, 22)),
			"invoice_value": round(tax_28 + tax_28 * 0.28, 2),
			"taxable_value": tax_28,
			"cgst_amount": round(tax_28 * 0.14, 2),
			"sgst_amount": round(tax_28 * 0.14, 2),
			"igst_amount": 0,
			"cess_amount": 0,
			"total_tax": round(tax_28 * 0.28, 2),
		},
	]

	for row in b2b_data:
		doc.append("b2b_invoices", row)

	# ── HSN Summary child rows ──
	hsn_data = [
		{
			"hsn_code": "8471",
			"description": "Computer parts & accessories (5%)",
			"uqc": "NOS",
			"total_quantity": 150,
			"taxable_value": tax_5,
			"cgst_rate": 2.5,
			"sgst_rate": 2.5,
			"igst_rate": 0,
			"total_tax": round(tax_5 * 0.05, 2),
		},
		{
			"hsn_code": "7323",
			"description": "Household steel utensils (12%)",
			"uqc": "PCS",
			"total_quantity": 500,
			"taxable_value": tax_12,
			"cgst_rate": 6,
			"sgst_rate": 6,
			"igst_rate": 0,
			"total_tax": round(tax_12 * 0.12, 2),
		},
		{
			"hsn_code": "9403",
			"description": "Furniture items (18%)",
			"uqc": "NOS",
			"total_quantity": 80,
			"taxable_value": tax_18,
			"cgst_rate": 9,
			"sgst_rate": 9,
			"igst_rate": 0,
			"total_tax": round(tax_18 * 0.18, 2),
		},
		{
			"hsn_code": "9503",
			"description": "Video game consoles (28%)",
			"uqc": "NOS",
			"total_quantity": 30,
			"taxable_value": tax_28,
			"cgst_rate": 14,
			"sgst_rate": 14,
			"igst_rate": 0,
			"total_tax": round(tax_28 * 0.28, 2),
		},
	]

	for row in hsn_data:
		doc.append("hsn_summary", row)

	doc.flags.ignore_permissions = True
	doc.flags.ignore_links = True
	doc.flags.ignore_mandatory = True
	doc.insert()
	frappe.db.commit()
	print("  📄 GSTR-1 ({}) → {}".format(period, filing_status))
	return doc


# ── GSTR-3B Data ───────────────────────────────────────


def create_gstr3b_return(company, period, filing_status):
	"""Create a GSTR-3B Return with child tables and summary values."""

	gstin = get_company_gstin(company)

	# Mirrors the GSTR-1 taxable value for the same period
	base_value = {
		"012026": 1250000,
		"022026": 1180000,
		"032026": 1420000,
		"042026": 1350000,
		"052026": 1510000,
		"062026": 1480000,
	}[period]

	taxable_outward = round(base_value * 0.85, 2)
	taxable_zero_rated = round(base_value * 0.05, 2)
	cgst_on_outward = round(taxable_outward * 0.09, 2)
	sgst_on_outward = round(taxable_outward * 0.09, 2)
	igst_on_zero = round(taxable_zero_rated * 0.05, 2)

	total_payable = round(cgst_on_outward + sgst_on_outward + igst_on_zero, 2)

	doc = frappe.new_doc("GSTR-3B Return")
	doc.company = company
	doc.company_gstin = gstin
	doc.return_period = period
	doc.itc_claim_period = "Current Period"
	doc.filing_status = filing_status
	doc.filing_date = build_filing_date(period, filing_status)
	doc.total_tax_payable = total_payable
	doc.total_tax_paid = total_payable if filing_status == "Filed" else 0

	# ── Outward Taxable Supplies ──
	doc.append(
		"outward_taxable_supplies",
		{
			"description": "3.1(a) Outward taxable supplies (other than zero rated, nil rated, and exempted)",
			"taxable_value": taxable_outward,
			"cgst": cgst_on_outward,
			"sgst": sgst_on_outward,
			"igst": 0,
			"cess": 0,
			"total_tax": round(cgst_on_outward + sgst_on_outward, 2),
		},
	)

	# ── Outward Zero-Rated Supplies ──
	doc.append(
		"outward_zero_rated_supplies",
		{
			"description": "3.1(b) Zero rated supply (export) on payment of IGST",
			"taxable_value": taxable_zero_rated,
			"cgst": 0,
			"sgst": 0,
			"igst": igst_on_zero,
			"cess": 0,
			"total_tax": igst_on_zero,
		},
	)

	# ── ITC Details ──
	itc_available = round(taxable_outward * 0.06, 2)
	doc.append(
		"itc_details",
		{
			"description": "4(A)(1) Import of goods",
			"itc_available": round(itc_available * 0.40, 2),
			"itc_claimed": round(itc_available * 0.35, 2),
			"itc_reversed": round(itc_available * 0.05, 2),
			"net_itc": round(itc_available * 0.35, 2),
		},
	)
	doc.append(
		"itc_details",
		{
			"description": "4(D) ITC from ISD",
			"itc_available": round(itc_available * 0.20, 2),
			"itc_claimed": round(itc_available * 0.20, 2),
			"itc_reversed": 0,
			"net_itc": round(itc_available * 0.20, 2),
		},
	)
	doc.append(
		"itc_details",
		{
			"description": "4(B) Import of services",
			"itc_available": round(itc_available * 0.40, 2),
			"itc_claimed": round(itc_available * 0.30, 2),
			"itc_reversed": round(itc_available * 0.10, 2),
			"net_itc": round(itc_available * 0.20, 2),
		},
	)

	# ── Net Tax Liability ──
	doc.append(
		"net_liability",
		{
			"description": "Integrated Tax",
			"tax_amount": igst_on_zero,
			"interest": 0,
			"late_fee": 0,
			"total": round(igst_on_zero, 2),
		},
	)
	doc.append(
		"net_liability",
		{
			"description": "Central Tax",
			"tax_amount": cgst_on_outward,
			"interest": round(cgst_on_outward * 0.01, 2) if filing_status != "Filed" else 0,
			"late_fee": 0,
			"total": round(cgst_on_outward, 2),
		},
	)
	doc.append(
		"net_liability",
		{
			"description": "State/UT Tax",
			"tax_amount": sgst_on_outward,
			"interest": round(sgst_on_outward * 0.01, 2) if filing_status != "Filed" else 0,
			"late_fee": 0,
			"total": round(sgst_on_outward, 2),
		},
	)

	doc.flags.ignore_permissions = True
	doc.flags.ignore_links = True
	doc.insert()
	frappe.db.commit()
	print("  📄 GSTR-3B ({}) → {}".format(period, filing_status))
	return doc


# ── Utility ─────────────────────────────────────────────


def get_invoice_date(period, day):
	"""Build an invoice date string for the given period and day."""
	month = int(period[:2])
	year = int("20" + period[2:])
	return "{:04d}-{:02d}-{:02d}".format(year, month, day)
