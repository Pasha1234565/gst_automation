from __future__ import unicode_literals

import frappe
from frappe import _


class GSTPortalClient:
	"""Base HTTP client for GSTN (GST portal) API communication.

	This client handles:
	- Loading credentials from GST Settings
	- Session/token management (auth_token, sek)
	- Encryption/decryption helpers for GSTN payloads
	- HTTP request building with proper headers
	"""

	def __init__(self, company=None):
		"""Initialize client from GST Settings for the given company."""
		self.settings = self._load_settings()
		self.base_url = self.settings.get("gst_api_endpoint") or "https://api.gst.gov.in"
		self.auth_token = None
		self.sek = None  # Secure Exchange Key for payload encryption
		self.gstin = self.settings.get("company_gstin")
		self.username = self.settings.get("gst_username")

	# ─── Settings ──────────────────────────────────────────

	def _load_settings(self):
		"""Load GST Settings singleton from the database.

		Note: GST Settings is a Single DocType, so we use
		frappe.get_single() to fetch it.
		"""
		try:
			settings = frappe.get_single("GST Settings")
			return settings.as_dict()
		except Exception:
			return {
				"company": None,
				"company_gstin": None,
				"gst_username": None,
				"gst_api_endpoint": "https://api.gst.gov.in",
				"enable_api_integration": 0,
			}

	def is_enabled(self):
		"""Check if GST portal API integration is configured and enabled."""
		return (
			self.settings.get("enable_api_integration")
			and self.settings.get("gst_username")
			and self.settings.get("company_gstin")
		)

	# ─── HTTP Helpers ──────────────────────────────────────

	def post(self, endpoint, data=None, headers=None):
		"""Send a POST request to the GST portal endpoint."""
		url = f"{self.base_url}/{endpoint.lstrip('/')}"
		return self._request("POST", url, data, headers)

	def get(self, endpoint, params=None, headers=None):
		"""Send a GET request to the GST portal endpoint."""
		url = f"{self.base_url}/{endpoint.lstrip('/')}"
		return self._request("GET", url, params, headers)

	def put(self, endpoint, data=None, headers=None):
		"""Send a PUT request to the GST portal endpoint."""
		url = f"{self.base_url}/{endpoint.lstrip('/')}"
		return self._request("PUT", url, data, headers)

	def _request(self, method, url, data=None, extra_headers=None):
		"""Execute an HTTP request with GSTN-standard headers."""
		headers = {
			"Content-Type": "application/json",
			"Accept": "application/json",
			"gstin": self.gstin or "",
			"state-cd": self._get_state_code(),
		}

		if self.auth_token:
			headers["auth-token"] = self.auth_token

		if extra_headers:
			headers.update(extra_headers)

		try:
			import requests

			if method == "GET":
				response = requests.get(url, params=data, headers=headers, timeout=30)
			elif method == "PUT":
				response = requests.put(url, json=data, headers=headers, timeout=30)
			else:
				response = requests.post(url, json=data, headers=headers, timeout=30)

			response.raise_for_status()
			return response.json()

		except ImportError:
			frappe.throw(_("The 'requests' library is required. Install it with: pip install requests"))
		except requests.exceptions.RequestException as e:
			frappe.log_error(
				title=_("GST Portal API Request Failed"),
				message=f"URL: {url}\nMethod: {method}\nError: {str(e)}",
			)
			frappe.throw(_("GST Portal API request failed: {0}").format(str(e)))

	# ─── Encryption Helpers ────────────────────────────────

	def encrypt_app_key(self, public_key):
		"""Encrypt the app key using RSA public key from GSTN.

		Args:
			public_key: RSA public key string from GSTN

		Returns:
			Base64-encoded encrypted app key
		"""
		try:
			from cryptography.hazmat.primitives import serialization, hashes
			from cryptography.hazmat.primitives.asymmetric import padding
			from cryptography.hazmat.backends import default_backend
			import base64

			pub_key = serialization.load_pem_public_key(
				public_key.encode() if isinstance(public_key, str) else public_key,
				backend=default_backend(),
			)

			encrypted = pub_key.encrypt(
				self.username.encode(),
				padding.OAEP(
					mgf=padding.MGF1(algorithm=hashes.SHA256()),
					algorithm=hashes.SHA256(),
					label=None,
				),
			)

			return base64.b64encode(encrypted).decode()

		except ImportError:
			frappe.throw(
				_("The 'cryptography' library is required for GST API encryption. "
				  "Install it with: pip install cryptography")
			)
		except Exception as e:
			frappe.log_error(
				title=_("GST Encryption Failed"),
				message=str(e),
			)
			frappe.throw(_("Failed to encrypt data for GST portal: {0}").format(str(e)))

	def _get_state_code(self):
		"""Extract state code from GSTIN (first 2 digits)."""
		if self.gstin and len(self.gstin) >= 2:
			return self.gstin[:2]
		return ""

	# ─── Session Management ────────────────────────────────

	def has_valid_session(self):
		"""Check if we have a valid auth token."""
		return bool(self.auth_token)

	def clear_session(self):
		"""Clear the current auth session."""
		self.auth_token = None
		self.sek = None


# ─── Shared Helpers ──────────────────────────────────────


def get_gst_client(company=None):
	"""Get a cached GST client with valid session, or create a new one.

	Args:
		company: Company name (optional)

	Returns:
		GSTPortalClient instance
	"""
	client = GSTPortalClient(company)

	if client.gstin:
		# Try to restore cached session
		session = frappe.cache().get(f"gst_session:{client.gstin}")
		if session:
			client.auth_token = session.get("auth_token")
			client.sek = session.get("sek")

	return client


def require_authenticated_client(company=None):
	"""Get a GST client that must have a valid session.

	If no valid session exists, shows a message and throws.

	Args:
		company: Company name (optional)

	Returns:
		GSTPortalClient with valid auth session
	"""
	client = get_gst_client(company)

	if not client.is_enabled():
		frappe.msgprint(_("GST API integration is not enabled in GST Settings."))
		frappe.throw(_("GST API integration is not configured."))

	if not client.has_valid_session():
		frappe.msgprint(
			_("Please authenticate with the GST portal first using 'Request OTP'.")
		)
		frappe.throw(_("GST Portal session expired. Please authenticate again."))

	return client
