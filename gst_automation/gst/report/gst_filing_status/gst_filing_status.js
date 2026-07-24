// Copyright (c) 2026, Your Company and contributors
// For license information, please see license.txt

frappe.query_reports["GST Filing Status"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 0,
		},
		{
			"fieldname": "filing_status",
			"label": __("Filing Status"),
			"fieldtype": "Select",
			"options": [
				"",
				"Not Filed",
				"JSON Generated",
				"Uploaded",
				"Filed",
			],
		},
		{
			"fieldname": "return_period",
			"label": __("Return Period (MMYYYY)"),
			"fieldtype": "Data",
			"length": 6,
		},
	],
};
