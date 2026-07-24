from __future__ import unicode_literals

import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart(data)
	return columns, data, None, chart


def get_columns():
	return [
		{
			"fieldname": "return_type",
			"label": _("Return Type"),
			"fieldtype": "Data",
			"width": 110,
		},
		{
			"fieldname": "return_period",
			"label": _("Return Period"),
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"fieldname": "company",
			"label": _("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"width": 200,
		},
		{
			"fieldname": "company_gstin",
			"label": _("Company GSTIN"),
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"fieldname": "filing_status",
			"label": _("Filing Status"),
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"fieldname": "filing_date",
			"label": _("Filing Date"),
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"fieldname": "total_taxable_value",
			"label": _("Total Taxable Value"),
			"fieldtype": "Currency",
			"width": 160,
		},
		{
			"fieldname": "total_tax_amount",
			"label": _("Total Tax Amount"),
			"fieldtype": "Currency",
			"width": 150,
		},
	]


def get_data(filters):
	"""Fetch combined GSTR-1 and GSTR-3B return data."""
	filters = filters or {}

	data = []

	# ── GSTR-1 Returns ──────────────────────────────────
	gstr1_list = frappe.get_all(
		"GSTR-1 Return",
		filters=get_filters("GSTR-1 Return", filters),
		fields=[
			"name",
			"company",
			"company_gstin",
			"return_period",
			"filing_status",
			"filing_date",
			"total_taxable_value",
			"total_tax_amount",
		],
		order_by="return_period desc",
	)

	for d in gstr1_list:
		data.append(
			{
				"return_type": "GSTR-1",
				"return_period": d.return_period,
				"company": d.company,
				"company_gstin": d.company_gstin,
				"filing_status": d.filing_status,
				"filing_date": d.filing_date,
				"total_taxable_value": d.total_taxable_value,
				"total_tax_amount": d.total_tax_amount,
			}
		)

	# ── GSTR-3B Returns ─────────────────────────────────
	gstr3b_list = frappe.get_all(
		"GSTR-3B Return",
		filters=get_filters("GSTR-3B Return", filters),
		fields=[
			"name",
			"company",
			"company_gstin",
			"return_period",
			"filing_status",
			"filing_date",
			"total_tax_payable",
			"total_tax_paid",
		],
		order_by="return_period desc",
	)

	for d in gstr3b_list:
		data.append(
			{
				"return_type": "GSTR-3B",
				"return_period": d.return_period,
				"company": d.company,
				"company_gstin": d.company_gstin,
				"filing_status": d.filing_status,
				"filing_date": d.filing_date,
				"total_taxable_value": d.total_tax_payable,
				"total_tax_amount": d.total_tax_paid,
			}
		)

	return data


def get_filters(doctype, filters):
	"""Build filters dict from report filters, defaulting to non-cancelled."""
	cond = {"docstatus": ["!=", 2]}

	if filters.get("company"):
		cond["company"] = filters["company"]

	if filters.get("filing_status"):
		cond["filing_status"] = filters["filing_status"]

	if filters.get("return_period"):
		cond["return_period"] = filters["return_period"]

	return cond


def get_chart(data):
	"""Build a stacked bar chart — filed vs pending per return type."""
	filed_count = {"GSTR-1": 0, "GSTR-3B": 0}
	pending_count = {"GSTR-1": 0, "GSTR-3B": 0}

	for row in data:
		rt = row["return_type"]
		if row["filing_status"] == "Filed":
			filed_count[rt] += 1
		else:
			pending_count[rt] += 1

	return {
		"data": {
			"labels": ["GSTR-1", "GSTR-3B"],
			"datasets": [
				{
					"name": "Filed",
					"values": [filed_count["GSTR-1"], filed_count["GSTR-3B"]],
				},
				{
					"name": "Pending / In Progress",
					"values": [pending_count["GSTR-1"], pending_count["GSTR-3B"]],
				},
			],
		},
		"type": "bar",
		"colors": ["#28a745", "#dc3545"],
		"bar_options": {"stacked": True},
	}
