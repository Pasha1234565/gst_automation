from __future__ import unicode_literals

import frappe

from gst_automation.patches import get_or_create_single


def execute():
	"""Create the GST Settings singleton record if it doesn't exist.

	GST Settings is a Single DocType. When "bench migrate" syncs the
	doctype, it creates the schema entry but does NOT insert the
	singleton record into the tabSingles table.  This means any
	call to frappe.get_single("GST Settings") will fail with a
	"GST Settings not found" error until the record is created.

	This patch creates that record so the doctype is usable from the
	UI, print formats, and server-side code.
	"""
	if frappe.db.exists("GST Settings", "GST Settings"):
		print("  ℹ️  GST Settings record already exists — skipping")
		return

	doc = get_or_create_single("GST Settings")
	print("  ✅ Created GST Settings singleton record")
