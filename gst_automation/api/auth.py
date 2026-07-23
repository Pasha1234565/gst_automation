from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import now_datetime, add_to_date

from gst_automation.api.client import GSTPortalClient


# ─── Public API (whitelisted) ────────────────────────────


@frappe.whitelist()
def request_otp(company=None):
	"""Request an OTP from the GST portal for authentication.

	This triggers an OTP SMS/email to the registered mobile/email
	of the GST practitioner. The OTP must be collected from the user
	and passed to `authenticate()`.

	Args:
		company: Optional company name. Uses default if omitted.

	Returns:
		dict with success status and message
	"""
	client = GSTPortalClient(company)

	if not client.is_enabled():
		frappe.throw(_(
			"GST API integration is not configured. "
			"Please enable it in GST Settings and provide your GST username."
		))

	try:
		# GSTN endpoint: POST /authenticate/request_otp
		response = client.post(
			"authenticate/request_otp",
			data={
				"gstin": client.gstin,
				"username": client.username,
			},
		)

		# Log the OTP request
		frappe.log_error(
			title=_("GST OTP Requested"),
			message=_("OTP requested for GSTIN: {0} at {1}").format(
				client.gstin, now_datetime()
			),
		)

		return {
			"success": True,
			"message": _("OTP has been sent to your registered mobile number and email."),
		}

	except Exception as e:
		frappe.log_error(
			title=_("GST OTP Request Failed"),
			message=f"GSTIN: {client.gstin}\nError: {str(e)}",
		)
		return {
			"success": False,
			"message": _("Failed to request OTP: {0}").format(str(e)),
		}


@frappe.whitelist()
def authenticate(otp, company=None):
	"""Authenticate with the GST portal using the OTP.

	Args:
		otp: The OTP received on registered mobile/email
		company: Optional company name

	Returns:
		dict with auth_token and session expiry info
	"""
	client = GSTPortalClient(company)

	if not client.is_enabled():
		frappe.throw(_("GST API integration is not configured."))

	if not otp or len(otp) < 4:
		frappe.throw(_("Please enter a valid OTP."))

	try:
		# Step 1: Get GSTN public key for encryption
		pub_key_resp = client.get("authenticate/publickey")
		public_key = pub_key_resp.get("publicKey")

		if not public_key:
			frappe.throw(_("Failed to retrieve GST portal public key."))

		# Step 2: Encrypt the app_key (username) with the public key
		encrypted_app_key = client.encrypt_app_key(public_key)

		# Step 3: Authenticate with OTP
		response = client.post(
			"authenticate",
			data={
				"gstin": client.gstin,
				"username": client.username,
				"app_key": encrypted_app_key,
				"otp": otp,
			},
		)

		# Step 4: Store session tokens
		client.auth_token = response.get("auth_token")
		client.sek = response.get("sek")

		if client.auth_token:
			_store_session(client)
			return {
				"success": True,
				"message": _("Authentication successful."),
				"auth_token": client.auth_token,
			}
		else:
			frappe.throw(_("Authentication failed: No auth token received from GST portal."))

	except Exception as e:
		frappe.log_error(
			title=_("GST Authentication Failed"),
			message=f"GSTIN: {client.gstin}\nError: {str(e)}",
		)
		return {
			"success": False,
			"message": _("Authentication failed: {0}").format(str(e)),
		}


# ─── Session Caching ─────────────────────────────────────


def _store_session(client):
	"""Cache the GST session tokens in Frappe cache.

	The GSTN auth token is typically valid for ~6 hours.
	We cache it for 5 hours to be safe.
	"""
	expires_at = add_to_date(now_datetime(), hours=5)

	frappe.cache().set(
		f"gst_session:{client.gstin}",
		{
			"auth_token": client.auth_token,
			"sek": client.sek,
			"expires_at": str(expires_at),
		},
	)
