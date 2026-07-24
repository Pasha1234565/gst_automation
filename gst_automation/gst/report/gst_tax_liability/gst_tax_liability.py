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
			"fieldname": "filing_status",
			"label": _("Filing Status"),
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"fieldname": "total_tax_payable",
			"label": _("Total Tax Payable"),
			"fieldtype": "Currency",
			"width": 160,
		},
		{
			"fieldname": "total_tax_paid",
			"label": _("Total Tax Paid"),
			"fieldtype": "Currency",
			"width": 150,
		},
	]


def get_data(filters):
	"""Fetch GSTR-3B return data for tax liability analysis."""
	filters = filters or {}

	cond = {"docstatus": ["!=", 2]}

	if filters.get("company"):
		cond["company"] = filters["company"]

	if filters.get("filing_status"):
		cond["filing_status"] = filters["filing_status"]

	if filters.get("return_period"):
		cond["return_period"] = filters["return_period"]

	records = frappe.get_all(
		"GSTR-3B Return",
		filters=cond,
		fields=[
			"name",
			"company",
			"return_period",
			"filing_status",
			"total_tax_payable",
			"total_tax_paid",
		],
		order_by="return_period asc",
	)

	return records


def get_chart(data):
	"""Build a line chart — tax payable & paid trend over return periods."""
	if not data:
		return None

	labels = []
	tax_payable = []
	tax_paid = []

	for row in data:
		labels.append(row["return_period"])
		tax_payable.append(row["total_tax_payable"] or 0)
		tax_paid.append(row["total_tax_paid"] or 0)

	return {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": "Tax Payable",
					"values": tax_payable,
				},
				{
					"name": "Tax Paid",
					"values": tax_paid,
				},
			],
		},
		"type": "line",
		"colors": ["#dc3545", "#28a745"],
	}
