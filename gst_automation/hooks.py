from __future__ import unicode_literals

app_name = "gst_automation"
app_title = "GST Automation"
app_publisher = "Your Company"
app_description = "GST Compliance, Invoicing & Filing Automation for ERPNext"
app_icon = "octicon octicon-file-text"
app_color = "green"
app_email = "info@example.com"
app_license = "MIT"

# Required Apps (installed automatically on site install)
# ------------------------------
required_apps = ["erpnext"]

# Fixtures
# ------------------------------
fixtures = [
	{"dt": "Workspace", "filters": [["module", "=", "GST"]]},
	{"dt": "DocType", "filters": [["module", "=", "GST"]]},
	{"dt": "Report", "filters": [["module", "=", "GST"]]},
	{"dt": "Role", "filters": [["name", "in", ["GST Manager", "Tax Accountant"]]]},
]

# Reports (auto-discovered from module directory)
# ------------------------------
reports = [
	"GST Filing Status",
	"GST Tax Liability",
]

# DocType Class
# ------------------------------
doctype_class = {
	"GSTR-1 Return": "gst_automation.gst.doctype.gstr_1_return.gstr_1_return.GSTR1Return",
	"GSTR-3B Return": "gst_automation.gst.doctype.gstr_3b_return.gstr_3b_return.GSTR3BReturn",
	"GST Invoice Customization": "gst_automation.gst.doctype.gst_invoice_customization.gst_invoice_customization.GSTInvoiceCustomization",
}

# Document Events
# ------------------------------
doc_events = {}

# Scheduled Tasks
# ------------------------------
scheduler_events = {}

# Permissions
# ------------------------------
# permission_query_conditions = {}

# Website
# ------------------------------
# website_route_rules = []

# Jinja
# ------------------------------
# jinja = {}

# Boot
# ------------------------------
# boot_session = boot_session

# After Migrate
# ------------------------------
after_migrate = [
	"gst_automation.patches.create_gst_workspace.execute",
	"gst_automation.patches.create_default_field_mappings.execute",
	"gst_automation.patches.deploy_gst_custom_fields.execute",
]


# Before Request
# ------------------------------
before_request = ["gst_automation.patches.fix_child_table_parent_columns.try_fix_once"]

# After Install
# ------------------------------
after_install = [
	"gst_automation.patches.create_gst_roles.execute",
]

