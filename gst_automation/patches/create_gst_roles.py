from __future__ import unicode_literals
import frappe


def execute():
	"""Create GST-related roles on app install or migrate."""
	roles = ["GST Manager", "Tax Accountant"]
	for role in roles:
		if not frappe.db.exists("Role", role):
			r = frappe.get_doc({"doctype": "Role", "role_name": role, "home_page": ""})
			r.insert()
			print(f"  ✅ Created Role: {role}")
		else:
			print(f"  ℹ️  Role '{role}' already exists")
