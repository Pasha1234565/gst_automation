from __future__ import unicode_literals

import json
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

	# Add charts
	add_charts(workspace)

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


def build_workspace_content():
	"""Build workspace layout JSON content."""
	content = [
		# ── Row 1: Quick Actions ──
		{"type": "header", "data": {"text": "Quick Actions", "level": 4, "col": 12}},
		{
			"type": "shortcut",
			"data": {
				"shortcut_name": "New GSTR-1",
				"col": 3,
			},
		},
		{
			"type": "shortcut",
			"data": {
				"shortcut_name": "New GSTR-3B",
				"col": 3,
			},
		},
		{
			"type": "shortcut",
			"data": {
				"shortcut_name": "GST Settings",
				"col": 3,
			},
		},
		{
			"type": "shortcut",
			"data": {
				"shortcut_name": "GSTR-1 List",
				"col": 3,
			},
		},
		{"type": "spacer", "data": {"col": 12}},
		# ── Row 2: Key Metrics ──
		{"type": "header", "data": {"text": "Key Metrics", "level": 4, "col": 12}},
		{
			"type": "number_card",
			"data": {
				"number_card_name": "Pending GSTR-1 Filings",
				"col": 3,
			},
		},
		{
			"type": "number_card",
			"data": {
				"number_card_name": "Pending GSTR-3B Filings",
				"col": 3,
			},
		},
	{
		"type": "number_card",
		"data": {
			"number_card_name": "GSTR-1 Filed This Month",
			"col": 3,
		},
	},
	{
		"type": "number_card",
		"data": {
			"number_card_name": "Total GSTR-1 Filed",
			"col": 3,
		},
	},
		{"type": "spacer", "data": {"col": 12}},
		# ── Row 3: Charts ──
		{"type": "header", "data": {"text": "Analytics", "level": 4, "col": 12}},
		{
			"type": "chart",
			"data": {
				"chart_name": "Filing Compliance",
				"col": 6,
			},
		},
		{
			"type": "chart",
			"data": {
				"chart_name": "Tax Liability Trend",
				"col": 6,
			},
		},
		{"type": "spacer", "data": {"col": 12}},
		# ── Row 4: Navigation Cards ──
		{"type": "header", "data": {"text": "GST Operations", "level": 4, "col": 12}},
		{
			"type": "card",
			"data": {
				"card_name": "Returns",
				"col": 4,
			},
		},
		{
			"type": "card",
			"data": {
				"card_name": "Configuration",
				"col": 4,
			},
		},
		{
			"type": "card",
			"data": {
				"card_name": "Reports & Analytics",
				"col": 4,
			},
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


def add_charts(workspace):
	"""Add dashboard charts to the workspace."""
	charts = [
		{
			"chart_name": "Filing Compliance",
			"label": "Filing Compliance",
			"chart_type": "Report",
			"report_name": "GST Filing Status",
			"width": "Half",
		},
		{
			"chart_name": "Tax Liability Trend",
			"label": "Tax Liability Trend",
			"chart_type": "Report",
			"report_name": "GST Tax Liability",
			"width": "Half",
		},
	]
	for c in charts:
		workspace.append("charts", c)


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



