from __future__ import unicode_literals

import json
import uuid
import frappe


def execute():
	"""Create or update GST workspace with charts, reports, and rich layout."""
	workspace_name = "GST"

	if frappe.db.exists("Workspace", workspace_name):
		print(f"  ℹ️  Workspace '{workspace_name}' already exists — updating")
		workspace = frappe.get_doc("Workspace", workspace_name)
	else:
		workspace = frappe.new_doc("Workspace")
		workspace.name = workspace_name
		workspace.title = workspace_name
		workspace.workspace_name = workspace_name
		workspace.label = workspace_name
		workspace.module = "GST"
		workspace.is_standard = 1
		workspace.public = 1
		workspace.icon = "file-text"
		workspace.sequence_id = 2.0

	# Clear previous dynamic children so we rebuild fresh
	workspace.set("shortcuts", [])
	workspace.set("number_cards", [])
	workspace.set("charts", [])
	workspace.set("links", [])
	workspace.set("custom_blocks", [])

	# Build content layout
	workspace.content = build_workspace_content()

	# Add shortcuts
	add_shortcuts(workspace)

	# Add number cards
	add_number_cards(workspace)

	# Create Dashboard Chart records
	created_charts = create_dashboard_charts()

	# Add charts to workspace (only those that were successfully created)
	add_charts(workspace, created_charts)

	# Add links (card breaks with doc links & report links)
	add_links(workspace)

	try:
		workspace.flags.ignore_permissions = True
		workspace.flags.ignore_links = True
		workspace.save()
		frappe.db.commit()
		print(f"  ✅ Updated workspace: {workspace_name}")
	except Exception as e:
		frappe.db.rollback()
		print(f"  ❌ Failed to update workspace: {e}")
		raise


# ── Layout Content ─────────────────────────────────────


def _uid():
	"""Generate a short unique ID for content blocks."""
	return uuid.uuid4().hex[:12]


def build_workspace_content():
	"""Build workspace layout JSON content with proper block IDs."""
	content = [
		# ── Row 1: Quick Actions ──
		{
			"id": _uid(),
			"type": "header",
			"data": {"text": "Quick Actions", "level": 4, "col": 12},
		},
		{
			"id": _uid(),
			"type": "shortcut",
			"data": {"shortcut_name": "New GSTR-1", "col": 3},
		},
		{
			"id": _uid(),
			"type": "shortcut",
			"data": {"shortcut_name": "New GSTR-3B", "col": 3},
		},
		{
			"id": _uid(),
			"type": "shortcut",
			"data": {"shortcut_name": "GST Settings", "col": 3},
		},
		{
			"id": _uid(),
			"type": "shortcut",
			"data": {"shortcut_name": "GSTR-1 List", "col": 3},
		},
		{"id": _uid(), "type": "spacer", "data": {"col": 12}},
		# ── Row 2: Key Metrics ──
		{
			"id": _uid(),
			"type": "header",
			"data": {"text": "Key Metrics", "level": 4, "col": 12},
		},
		{
			"id": _uid(),
			"type": "number_card",
			"data": {"number_card_name": "Pending GSTR-1 Filings", "col": 3},
		},
		{
			"id": _uid(),
			"type": "number_card",
			"data": {"number_card_name": "Pending GSTR-3B Filings", "col": 3},
		},
		{
			"id": _uid(),
			"type": "number_card",
			"data": {"number_card_name": "GSTR-1 Filed This Month", "col": 3},
		},
		{
			"id": _uid(),
			"type": "number_card",
			"data": {"number_card_name": "Total GSTR-1 Filed", "col": 3},
		},
		{"id": _uid(), "type": "spacer", "data": {"col": 12}},
		# ── Row 3: Charts ──
		{
			"id": _uid(),
			"type": "header",
			"data": {"text": "Analytics", "level": 4, "col": 12},
		},
		{
			"id": _uid(),
			"type": "chart",
			"data": {"chart_name": "Filing Compliance", "col": 6},
		},
		{
			"id": _uid(),
			"type": "chart",
			"data": {"chart_name": "Tax Liability Trend", "col": 6},
		},
		{"id": _uid(), "type": "spacer", "data": {"col": 12}},
		# ── Row 4: Navigation Cards ──
		{
			"id": _uid(),
			"type": "header",
			"data": {"text": "GST Operations", "level": 4, "col": 12},
		},
		{
			"id": _uid(),
			"type": "card",
			"data": {"card_name": "Returns", "col": 4},
		},
		{
			"id": _uid(),
			"type": "card",
			"data": {"card_name": "Configuration", "col": 4},
		},
		{
			"id": _uid(),
			"type": "card",
			"data": {"card_name": "Reports & Analytics", "col": 4},
		},
	]
	return json.dumps(content)


# ── Shortcuts ──────────────────────────────────────────


def add_shortcuts(workspace):
	"""Add shortcut tiles to the workspace."""
	shortcuts = [
		{
			"label": "New GSTR-1",
			"type": "DocType",
			"link_to": "GSTR-1 Return",
			"doc_view": "New",
			"icon": "share",
			"kanban_board": "",
			"dependencies": "",
			"onboard": 1,
		},
		{
			"label": "New GSTR-3B",
			"type": "DocType",
			"link_to": "GSTR-3B Return",
			"doc_view": "New",
			"icon": "share",
			"kanban_board": "",
			"dependencies": "",
			"onboard": 1,
		},
		{
			"label": "GST Settings",
			"type": "DocType",
			"link_to": "GST Settings",
			"doc_view": "",
			"icon": "setting",
			"kanban_board": "",
			"dependencies": "",
			"onboard": 1,
		},
		{
			"label": "GSTR-1 List",
			"type": "DocType",
			"link_to": "GSTR-1 Return",
			"doc_view": "List",
			"icon": "list",
			"kanban_board": "",
			"dependencies": "",
			"onboard": 1,
		},
	]
	for s in shortcuts:
		workspace.append("shortcuts", s)


# ── Number Cards ───────────────────────────────────────


def add_number_cards(workspace):
	"""Add number cards to the workspace."""
	cards = [
		{
			"number_card_name": "Pending GSTR-1 Filings",
			"label": "Pending GSTR-1",
			"type": "Document Type",
			"document_type": "GSTR-1 Return",
			"function": "Count",
			"filter_operator": "=",
			"filter_field": "filing_status",
			"filter_value": "Not Filed",
			"color": "#ff6b6b",
			"show_trend": 1,
		},
		{
			"number_card_name": "Pending GSTR-3B Filings",
			"label": "Pending GSTR-3B",
			"type": "Document Type",
			"document_type": "GSTR-3B Return",
			"function": "Count",
			"filter_operator": "=",
			"filter_field": "filing_status",
			"filter_value": "Not Filed",
			"color": "#ffc107",
			"show_trend": 1,
		},
		{
			"number_card_name": "GSTR-1 Filed This Month",
			"label": "GSTR-1 Filed (Month)",
			"type": "Document Type",
			"document_type": "GSTR-1 Return",
			"function": "Count",
			"filter_operator": "Timespan",
			"filter_field": "filing_date",
			"filter_value": "This Month",
			"color": "#28a745",
			"show_trend": 1,
		},
		{
			"number_card_name": "Total GSTR-1 Filed",
			"label": "Total GSTR-1 Filed",
			"type": "Document Type",
			"document_type": "GSTR-1 Return",
			"function": "Count",
			"filter_operator": "=",
			"filter_field": "filing_status",
			"filter_value": "Filed",
			"color": "#007bff",
			"show_trend": 0,
		},
	]
	for c in cards:
		workspace.append("number_cards", c)


# ── Charts ─────────────────────────────────────────────


def create_dashboard_charts():
	"""Create Dashboard Chart doctype records for the workspace.

	Returns:
	    set: Names of charts that were successfully created or already exist.
	"""
	ready = set()

	charts = [
		{
			"chart_name": "Filing Compliance",
			"chart_type": "Group By",
			"document_type": "GSTR-1 Return",
			"based_on": "filing_status",
			"group_by_type": "Count",
			"type": "Donut",
			"color": "#28a745",
		},
		{
			"chart_name": "Tax Liability Trend",
			"chart_type": "Sum",
			"document_type": "GSTR-3B Return",
			"timeseries_based_on": "filing_date",
			"aggregate_function_based_on": "total_tax_payable",
			"type": "Line",
			"timespan": "Last Year",
			"time_interval": "Monthly",
			"color": "#dc3545",
		},
	]

	for chart_def in charts:
		chart_name = chart_def["chart_name"]

		if frappe.db.exists("Dashboard Chart", chart_name):
			print(f"  ℹ️  Dashboard Chart '{chart_name}' already exists")
			ready.add(chart_name)
			continue

		try:
			# Build the document via dict to ensure all fields are set atomically
			doc_dict = {
				"doctype": "Dashboard Chart",
				"chart_name": chart_name,
				"chart_type": chart_def["chart_type"],
				"document_type": chart_def.get("document_type", ""),
				"based_on": chart_def.get("based_on", ""),
				"group_by_type": chart_def.get("group_by_type", ""),
				"type": chart_def["type"],
				"timespan": chart_def.get("timespan", ""),
				"time_interval": chart_def.get("time_interval", ""),
				"timeseries_based_on": chart_def.get("timeseries_based_on", ""),
				"aggregate_function_based_on": chart_def.get("aggregate_function_based_on", ""),
				"color": chart_def.get("color", "#007bff"),
			}

			# For Sum/Average charts with timeseries, we need the y_axis child table
			if chart_def["chart_type"] in ("Sum", "Average") and chart_def.get("aggregate_function_based_on"):
				doc_dict["y_axis"] = [
					{
						"doctype": "Dashboard Chart Field",
						"parent": chart_name,
						"parentfield": "y_axis",
						"parenttype": "Dashboard Chart",
						"value_based_on": chart_def["aggregate_function_based_on"],
					}
				]

			doc = frappe.get_doc(doc_dict)
			doc.flags.ignore_permissions = True
			doc.flags.ignore_mandatory = True
			doc.insert()
			print(f"  📊 Created Dashboard Chart: {chart_name}")
			ready.add(chart_name)

		except Exception as e:
			# Log but DON'T rollback — the final commit in execute() handles it
			print(f"  ⚠️  Could not create chart '{chart_name}': {e}")

	return ready


def add_charts(workspace, ready_charts):
	"""Add dashboard chart entries to the workspace for charts that exist."""
	chart_entries = []

	if "Filing Compliance" in ready_charts:
		chart_entries.append(
			{
				"chart_name": "Filing Compliance",
				"label": "Filing Compliance",
				"chart_type": "Dashboard Chart",
				"width": "Half",
			}
		)

	if "Tax Liability Trend" in ready_charts:
		chart_entries.append(
			{
				"chart_name": "Tax Liability Trend",
				"label": "Tax Liability Trend",
				"chart_type": "Dashboard Chart",
				"width": "Half",
			}
		)

	for c in chart_entries:
		workspace.append("charts", c)

	if not chart_entries:
		print("  ⚠️  No Dashboard Chart records were available — charts will not render")


# ── Links (Sidebar Navigation) ─────────────────────────


def add_links(workspace):
	"""Add sidebar links organized by card break sections."""
	links = [
		# ── Returns ──
		{
			"type": "Card Break",
			"label": "Returns",
			"hidden": 0,
			"is_query_report": 0,
			"onboard": 1,
		},
		{
			"label": "GSTR-1 Return",
			"type": "Link",
			"link_type": "DocType",
			"link_to": "GSTR-1 Return",
			"dependencies": "",
			"hidden": 0,
			"is_query_report": 0,
			"onboard": 1,
		},
		{
			"label": "GSTR-3B Return",
			"type": "Link",
			"link_type": "DocType",
			"link_to": "GSTR-3B Return",
			"dependencies": "",
			"hidden": 0,
			"is_query_report": 0,
			"onboard": 1,
		},
		# ── Configuration ──
		{
			"type": "Card Break",
			"label": "Configuration",
			"hidden": 0,
			"is_query_report": 0,
			"onboard": 1,
		},
		{
			"label": "GST Settings",
			"type": "Link",
			"link_type": "DocType",
			"link_to": "GST Settings",
			"dependencies": "",
			"hidden": 0,
			"is_query_report": 0,
			"onboard": 1,
		},
		{
			"label": "GST Invoice Customization",
			"type": "Link",
			"link_type": "DocType",
			"link_to": "GST Invoice Customization",
			"dependencies": "",
			"hidden": 0,
			"is_query_report": 0,
			"onboard": 1,
		},
		{
			"label": "GST Field Mapping",
			"type": "Link",
			"link_type": "DocType",
			"link_to": "GST Field Mapping",
			"dependencies": "",
			"hidden": 0,
			"is_query_report": 0,
			"onboard": 1,
		},
		# ── Reports & Analytics ──
		{
			"type": "Card Break",
			"label": "Reports & Analytics",
			"hidden": 0,
			"is_query_report": 0,
			"onboard": 1,
		},
		{
			"label": "GST Filing Status",
			"type": "Link",
			"link_type": "Report",
			"link_to": "GST Filing Status",
			"dependencies": "",
			"hidden": 0,
			"is_query_report": 1,
			"onboard": 1,
		},
		{
			"label": "GST Tax Liability",
			"type": "Link",
			"link_type": "Report",
			"link_to": "GST Tax Liability",
			"dependencies": "",
			"hidden": 0,
			"is_query_report": 1,
			"onboard": 1,
		},
	]
	for link in links:
		workspace.append("links", link)
