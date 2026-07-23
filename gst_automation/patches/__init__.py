import frappe


def get_or_create_single(doctype):
	"""Get a Single DocType, creating the DB record if it doesn't exist.

	During after_migrate, a Single DocType's schema may be synced
	but its tabSingles record won't exist yet, causing
	frappe.get_single() to fail with DoesNotExistError.

	Args:
		doctype: Name of the Single DocType

	Returns:
		Document object for the Single DocType
	"""
	try:
		return frappe.get_single(doctype)
	except frappe.DoesNotExistError:
		doc = frappe.new_doc(doctype)
		doc.flags.ignore_permissions = True
		doc.flags.ignore_mandatory = True
		doc.flags.ignore_validate = True
		doc.insert()
		frappe.db.commit()
		return doc
