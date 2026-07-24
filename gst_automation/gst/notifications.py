from __future__ import unicode_literals

from datetime import date

import frappe
from frappe import _
from frappe.utils import getdate, flt, fmt_money


def send_due_date_reminders():
	"""Daily scheduled task: send in-app reminders for upcoming GST deadlines.

	Runs once every day and checks each company's GST Settings to see if
	today falls within the configured reminder window before the GSTR-3B
	(20th) and/or GSTR-1 (11th) due dates. Creates Notification Log
	entries for users with GST Manager / Tax Accountant roles.
	"""
	settings_list = frappe.get_all(
		"GST Settings",
		filters={"enable_in_app_notifications": 1},
		fields=[
			"name",
			"company",
			"in_app_notify_days",
			"notify_gstr3b_due",
			"notify_gstr1_due",
		],
	)

	today = getdate()

	for gs in settings_list:
		if not gs.company:
			continue

		notify_days = gs.in_app_notify_days or 2

		# ─── GSTR-3B reminder (due 20th of each month) ──────────
		if gs.notify_gstr3b_due:
			_deadline_handler(
				company=gs.company,
				deadline_day=20,
				return_type="GSTR-3B",
				notify_days=notify_days,
				today=today,
				doc_doctype="GSTR-3B Return",
				amount_field="total_tax_payable",
			)

		# ─── GSTR-1 reminder (due 11th of each month) ───────────
		if gs.notify_gstr1_due:
			_deadline_handler(
				company=gs.company,
				deadline_day=11,
				return_type="GSTR-1",
				notify_days=notify_days,
				today=today,
				doc_doctype="GSTR-1 Return",
				amount_field="total_tax_amount",
			)


# ─── Helpers ──────────────────────────────────────────────────────────


def _deadline_handler(
	company, deadline_day, return_type, notify_days, today, doc_doctype, amount_field
):
	"""Check if the deadline is approaching and send a reminder if so."""
	deadline_date = _get_next_deadline(deadline_day, today)
	days_until_deadline = (deadline_date - today).days

	if days_until_deadline != notify_days:
		return  # not the right day to notify

	# Determine which return period this deadline is for
	return_period = _get_return_period_for_deadline(deadline_date)

	# Find an existing return doc (if any) to pull the amount due
	existing_doc = frappe.db.get_value(
		doc_doctype,
		{"company": company, "return_period": return_period, "docstatus": ["!=", 2]},
		["name", amount_field, "filing_status"],
		as_dict=True,
	)

	if existing_doc and existing_doc.filing_status == "Filed":
		return  # already filed — no reminder needed

	amount_due = flt(existing_doc[amount_field]) if existing_doc else 0.0

	# Build the notification message
	currency = frappe.db.get_value("Company", company, "default_currency") or "INR"
	amount_formatted = fmt_money(amount_due, currency=currency) if amount_due else "To be determined"

	title = _("{0} Filing Due Reminder").format(return_type)
	subject = _("{0} return for period {1} is due on {2}").format(
		return_type, return_period, deadline_date.strftime("%d-%b-%Y")
	)

	message = _(
		"<p>Dear User,</p>"
		"<p>This is a reminder that the <strong>{0}</strong> return for <strong>{1}</strong> "
		"(period <strong>{2}</strong>) is due on <strong>{3}</strong>.</p>"
	).format(return_type, company, return_period, deadline_date.strftime("%d-%b-%Y"))

	if return_type == "GSTR-3B" and amount_due:
		message += _("<p>Estimated tax amount payable: <strong>{0}</strong></p>").format(
			amount_formatted
		)
		if existing_doc and existing_doc.name:
			message += _(
				'<p><a href="/app/gstr-3b-return/{0}">Click here</a> to review and file.</p>'
			).format(existing_doc.name)
	elif amount_due:
		message += _("<p>Total tax amount: <strong>{0}</strong></p>").format(amount_formatted)
	else:
		message += _("<p>Please create and file the return at the earliest.</p>")

	# Send in-app notification to all relevant users
	users = _get_notification_users()
	for user_email in users:
		_create_notification_log(
			for_user=user_email,
			subject=subject,
			message=message,
			type="Alert",
		)

	frappe.log_error(
		_("In-app {0} reminder sent to {1} users for {2} ({3})").format(
			return_type, len(users), company, return_period
		),
		_("GST Notification"),
	)


def _get_next_deadline(deadline_day, today):
	"""Return the nearest upcoming deadline date for a given day-of-month."""
	current = date(today.year, today.month, deadline_day)

	if today <= current:
		return current

	# Roll over to next month
	if today.month == 12:
		return date(today.year + 1, 1, deadline_day)
	else:
		return date(today.year, today.month + 1, deadline_day)


def _get_return_period_for_deadline(deadline_date):
	"""Return the MMYYYY return period that is due by the given deadline.

	Example: deadline 20-Apr-2026 → return_period 032026 (March 2026).
	"""
	if deadline_date.month == 1:
		prev_month = 12
		prev_year = deadline_date.year - 1
	else:
		prev_month = deadline_date.month - 1
		prev_year = deadline_date.year

	return "{:02d}{:04d}".format(prev_month, prev_year)


def _get_notification_users():
	"""Return deduplicated list of user emails with GST Manager or Tax Accountant roles."""
	users = set()
	for role in ("GST Manager", "Tax Accountant"):
		records = frappe.get_all(
			"Has Role",
			filters={"role": role, "parenttype": "User"},
			pluck="parent",
		)
		users.update(records)

	# Filter to only enabled / active users
	active = frappe.get_all("User", filters={"name": ("in", list(users)), "enabled": 1}, pluck="name")
	return active


def _create_notification_log(for_user, subject, message, type="Alert"):
	"""Create a Notification Log entry for an in-app notification."""
	try:
		doc = frappe.get_doc(
			{
				"doctype": "Notification Log",
				"subject": subject,
				"email_content": message,
				"for_user": for_user,
				"type": type,
				"document_type": None,
				"document_name": None,
			}
		)
		doc.flags.ignore_permissions = True
		doc.insert()
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			_("Failed to create Notification Log for {0}").format(for_user),
		)
