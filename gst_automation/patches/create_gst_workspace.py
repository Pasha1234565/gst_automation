from __future__ import unicode_literals

import json
import frappe


def execute():
	"""Create GST workspace directly in the database.

	This bypasses Frappe's workspace JSON sync mechanism to ensure
	a dedicated workspace is created without affecting other apps.
	"""
	workspace_name = "GST"

	if frappe.db.exists("Workspace", workspace_name):
		print(f"  ℹ️  Workspace '{workspace_name}' already exists")
		return

	workspace = frappe.new_doc("Workspace")
	workspace.name = workspace_name
	workspace.title = workspace_name
	workspace.workspace_name = workspace_name
	workspace.label = workspace_name
	workspace.module = "GST"
	workspace.is_standard = 1
	workspace.public = 1
	workspace.icon = "file-text"

	# Build content layout
	workspace.content = build_workspace_content()

	# Add shortcuts
	add_shortcuts(workspace)

	# Add number cards
	add_number_cards(workspace)

	try:
		workspace.flags.ignore_permissions = True
		workspace.flags.ignore_links = True
		workspace.insert()
		frappe.db.commit()
		print(f"  ✅ Created workspace: {workspace_name}")
	except Exception as e:
		frappe.db.rollback()
		print(f"  ❌ Failed to create workspace: {e}")
		raise


def build_workspace_content():
	"""Build workspace layout JSON content."""
	content = [
		{"type": "header", "data": {"text": "Shortcuts"}},
		{
			"type": "shortcut",
			"data": {
				"shortcut_name": "New GSTR-1",
				"type": "DocType",
				"link_to": "GSTR-1 Return",
				"doc_view": "New",
				"icon": "share",
				"onboard": 1,
			},
		},
		{
			"type": "shortcut",
			"data": {
				"shortcut_name": "New GSTR-3B",
				"type": "DocType",
				"link_to": "GSTR-3B Return",
				"doc_view": "New",
				"icon": "share",
				"onboard": 1,
			},
		},
		{
			"type": "shortcut",
			"data": {
				"shortcut_name": "GST Settings",
				"type": "DocType",
				"link_to": "GST Settings",
				"doc_view": "",
				"icon": "setting",
				"onboard": 1,
			},
		},
		{
			"type": "shortcut",
			"data": {
				"shortcut_name": "GSTR-1 List",
				"type": "DocType",
				"link_to": "GSTR-1 Return",
				"doc_view": "List",
				"icon": "list",
				"onboard": 1,
			},
		},
		{"type": "header", "data": {"text": "Key Metrics"}},
		{
			"type": "number_card",
			"data": {
				"number_card_name": "Pending GSTR-1 Filings",
				"label": "Pending GSTR-1",
			},
		},
		{
			"type": "number_card",
			"data": {
				"number_card_name": "Pending GSTR-3B Filings",
				"label": "Pending GSTR-3B",
			},
		},
		{"type": "header", "data": {"text": "Quick Access"}},
		{
			"type": "card",
			"data": {
				"card_name": "Returns",
				"col": 4,
				"items": [
					{
						"type": "DocType",
						"link_to": "GSTR-1 Return",
						"label": "GSTR-1",
						"description": "Outward supply return filing",
						"onboard": 1,
					},
					{
						"type": "DocType",
						"link_to": "GSTR-3B Return",
						"label": "GSTR-3B",
						"description": "Summary return filing",
						"onboard": 1,
					},
				],
			},
		},
		{
			"type": "card",
			"data": {
				"card_name": "Configuration",
				"col": 4,
				"items": [
					{
						"type": "DocType",
						"link_to": "GST Settings",
						"label": "GST Settings",
						"description": "Configure GST compliance and API settings",
						"onboard": 1,
					}
				],
			},
		},
	]
	return json.dumps(content)


def add_shortcuts(workspace):
	"""Add shortcuts to the workspace."""
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
	]
	for c in cards:
		workspace.append("number_cards", c)


def create_roles():
	"""Create GST-related roles on app install."""
	roles = ["GST Manager", "Tax Accountant"]
	for role in roles:
		if not frappe.db.exists("Role", role):
			r = frappe.get_doc({"doctype": "Role", "role_name": role, "home_page": ""})
			r.insert()
			print(f"  ✅ Created Role: {role}")
