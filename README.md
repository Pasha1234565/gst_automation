# README

## GST Automation — GST Compliance, Invoicing & Filing for ERPNext

**App Name:** GST Automation (`gst_automation`)
**Module:** GST
**Domain:** GST Compliance, Invoicing & Return Filing (India)
**Required Apps:** ERPNext
**Repository:** https://github.com/Pasha1234565/gst_automation.git

---

## TABLE OF CONTENTS

1. [Application Overview](#1-application-overview)
2. [System Architecture](#2-system-architecture)
3. [Getting Started](#3-getting-started)
4. [The Day-to-Day Workflow, Step by Step](#4-the-day-to-day-workflow-step-by-step)
5. [GST Portal API Integration](#5-gst-portal-api-integration)
6. [GST Invoice Customization](#6-gst-invoice-customization)
7. [Reports](#7-reports)
8. [Workspace Navigation](#8-workspace-navigation)
9. [Scheduled Tasks & Automation](#9-scheduled-tasks--automation)
10. [Setup & Configuration (Fixtures)](#10-setup--configuration-fixtures)
11. [Demo Data](#11-demo-data)
12. [Troubleshooting](#12-troubleshooting)
13. [Appendix](#13-appendix)

---

## 1. APPLICATION OVERVIEW

### 1.1 Purpose
GST Automation is a Frappe/ERPNext application built for Indian businesses that need to manage their GST compliance end-to-end — from configuring GST settings and generating GST-compliant invoices through preparing, validating, and filing GSTR-1 and GSTR-3B returns directly from the ERP. It covers:

- **GST Configuration** — company GSTIN, filing frequency, HSN validation rules, reverse charge thresholds
- **GSTR-1 Return Management** — B2B invoice details, HSN-wise summary, JSON generation for GST portal upload
- **GSTR-3B Return Management** — outward supplies, ITC details, net tax liability, payment summary
- **GST Portal API Integration** — OTP-based authentication, save/filing of returns, status checking
- **GST Invoice Customization** — custom field mappings between Sales Invoice and GST returns, auto-deployment
- **In-App Notifications** — filing due date reminders for GSTR-1 (11th) and GSTR-3B (20th)
- **GST-Compliant Invoice Print Format** — standard GST tax invoice with HSN, tax breakup, and place of supply

### 1.2 Key Features
- **2 Submittable DocTypes** — GSTR-1 Return and GSTR-3B Return
- **10 DocTypes** — 2 Single configuration doctypes, 2 document doctypes, 5 child tables, 1 field mapping
- **2 Custom Roles** — GST Manager (full access), Tax Accountant (read-only)
- **1 Scheduled Task** — daily filing due-date reminder notifications
- **2 Script Reports** — GST Filing Status (combined GSTR-1 + GSTR-3B), GST Tax Liability (GSTR-3B trend)
- **2 Dashboard Charts** — Filing Compliance (donut), Tax Liability Trend (line)
- **GST Portal API** — OTP auth, save, file, and status check endpoints for both returns
- **Standard GST Invoice Print Format** — Jinja-based, GST-compliant layout
- **In-App Reminders** — configurable days-before-due notifications via Frappe's notification system

---

## 2. SYSTEM ARCHITECTURE

### 2.1 Technology Stack
- **Framework:** Frappe / ERPNext
- **Database:** MariaDB
- **Automated Tasks:** Frappe Scheduler (daily)
- **External Dependency:** `requests` library for GST Portal API calls; `cryptography` library for payload encryption
- **Optional:** Active GSTN credentials for portal API integration

### 2.2 DocType Structure

| # | DocType Name | Type | Section | Submittable |
|---|--------------|------|---------|:-----------:|
| 1 | GST Settings | Single (Configuration) | Configuration | ❌ |
| 2 | GST Invoice Customization | Single (Configuration) | Configuration | ❌ |
| 3 | GST Field Mapping | Child Table | — | ❌ |
| 4 | GSTR-1 Return | Document | Returns | ✅ |
| 5 | GSTR-1 B2B Invoice | Child Table | — | ❌ |
| 6 | GSTR-1 HSN Summary | Child Table | — | ❌ |
| 7 | GSTR-3B Return | Document | Returns | ✅ |
| 8 | GSTR-3B Outward Supply | Child Table | — | ❌ |
| 9 | GSTR-3B ITC Detail | Child Table | — | ❌ |
| 10 | GSTR-3B Net Liability | Child Table | — | ❌ |

### 2.3 Naming Series Convention

| DocType | Prefix | Format |
|---------|--------|--------|
| GSTR-1 Return | GSTR1 | `GSTR1-.YYYY.-.####` |
| GSTR-3B Return | GSTR3B | `GSTR3B-.YYYY.-.####` |
| GST Settings | — | Singleton (fixed name `GST Settings`) |
| GST Invoice Customization | — | Singleton (fixed name `GST Invoice Customization`) |

### 2.4 Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         GST COMPLIANCE WORKFLOW                            │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ⚙️ CONFIGURATION                                                         │
│  ┌──────────────┐    ┌────────────────────────┐                          │
│  │ GST Settings  │───▶│ GST Invoice Custom.   │                          │
│  │ (Company,     │    │ (Field mappings,      │                          │
│  │  GSTIN, API)  │    │  HSN rules, behavior) │                          │
│  └──────────────┘    └───────────┬────────────┘                          │
│                                  │ deploy_custom_fields()                 │
│                                  ▼                                        │
│                         ┌──────────────────┐                             │
│                         │ Sales Invoice    │                             │
│                         │ (+ custom fields)│                             │
│                         └────────┬─────────┘                             │
│                                  │                                        │
│  📄 RETURN PREPARATION           │                                        │
│  ┌──────────────────┐           │                                        │
│  │   GSTR-1 Return   │◄──────────┘ (B2B data from invoices)              │
│  │  (B2B invoices,   │                                                   │
│  │   HSN summary)    │                                                   │
│  └────────┬─────────┘                                                   │
│           │ generate_gstr1_json()                                        │
│           ▼                                                              │
│  ┌──────────────────┐                                                   │
│  │ GSTR-1 JSON File  │──▶ Manual upload to GST portal or API save       │
│  └──────────────────┘                                                   │
│                                                                           │
│  ┌──────────────────┐                                                   │
│  │  GSTR-3B Return   │                                                   │
│  │ (Outward supplies,│                                                   │
│  │  ITC details,     │                                                   │
│  │  Net liability)   │                                                   │
│  └────────┬─────────┘                                                   │
│           │ generate_gstr3b_json()                                       │
│           ▼                                                              │
│  ┌──────────────────┐                                                   │
│  │ GSTR-3B JSON File │──▶ Manual upload to GST portal or API save       │
│  └──────────────────┘                                                   │
│                                                                           │
│  🔗 GST PORTAL API (Optional)                                            │
│  request_otp() ──▶ authenticate() ──▶ save_gstr1/3b() ──▶ file_gstr1/3b()│
│                                         ──▶ check_gstr1/3b_status()     │
│                                                                           │
│  🔔 NOTIFICATIONS                                                        │
│  Daily scheduler ──▶ GSTR-3B due check (20th) ──▶ In-app reminder       │
│                   ──▶ GSTR-1 due check (11th)  ──▶ In-app reminder       │
│                                                                           │
│  📊 REPORTS & ANALYTICS                                                  │
│  GST Filing Status (GSTR-1 + GSTR-3B) ──▶ Stacked bar chart              │
│  GST Tax Liability (GSTR-3B trend)     ──▶ Line chart                    │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 3. GETTING STARTED

### 3.1 Installation
```bash
# From the bench directory
bench get-app https://github.com/Pasha1234565/gst_automation.git
bench --site your-site.com install-app gst_automation
bench --site your-site.com migrate
```

### 3.2 Role Setup
Two roles are created automatically on install (via the `create_gst_roles` patch):
1. **GST Manager** — Full operational access: create/write/submit/amend/cancel returns, full CRUD on GST Settings and Invoice Customization
2. **Tax Accountant** — Read-only access to returns and reports; no write/submit/delete rights

### 3.3 Initial Configuration
Before using the app, set up your master configuration:

1. **Open GST Settings** — Go to **GST → Configuration → GST Settings**
2. Select your **Company** and enter the **Company GSTIN**
3. Set the **Filing Frequency** (Monthly / Quarterly)
4. Configure **Defaults & Validation**:
   - Round Off GST Components
   - Validate HSN/SAC Codes
   - Default HSN Code Length (4/6/8 digits)
   - Reverse Charge Threshold
5. (Optional) Configure **GST Portal API** credentials for direct portal integration
6. (Optional) Configure **Notifications** for filing due-date reminders

### 3.4 Scheduler
Ensure the scheduler is enabled for due-date reminder notifications:
```bash
bench --site your-site.com scheduler enable
```

---

## 4. THE DAY-TO-DAY WORKFLOW, STEP BY STEP

### Step 1 — Create a GSTR-1 Return

1. Go to **GST → Returns → GSTR-1 Return**.
2. Click **+ Add GSTR-1 Return**.
3. Select the **Company** (GSTIN is auto-populated from GST Settings).
4. Enter the **Return Period** in MMYYYY format (e.g., `042026` for April 2026).
5. In the **B2B Invoices** table, add each B2B invoice with details:
   - Sales Invoice reference
   - Customer GSTIN
   - Invoice date and value
   - Taxable value, CGST, SGST, IGST, Cess amounts
6. In the **HSN-wise Summary** table, add HSN codes with:
   - HSN code and description
   - UQC (Unit Quantity Code), quantity
   - Taxable value
   - CGST/SGST/IGST rates
7. Click **Save** (creates a draft with "Not Filed" status).
8. Click **Generate JSON** to create a GSTN-compliant JSON file for manual upload.

### Step 2 — Submit a GSTR-1 Return

Once all data is verified:

1. Open the GSTR-1 Return document.
2. Click **Submit**. The filing status changes to **Filed** and the filing date is recorded.
3. The return is now ready for portal upload (manual or via API).

### Step 3 — Create and Submit a GSTR-3B Return

1. Go to **GST → Returns → GSTR-3B Return**.
2. Click **+ Add GSTR-3B Return**.
3. Select the **Company** and enter the **Return Period**.
4. Fill in the **Outward Taxable Supplies** (Table 3.1(a)):
   - Add rows for each supply type with taxable value, CGST, SGST, IGST, Cess
5. Fill in the **Outward Zero-Rated Supplies** (Table 3.1(b)):
   - Export supplies with IGST details
6. Fill in the **ITC Details** (Table 4):
   - Import of goods/services, ISD credit, etc.
   - ITC available, claimed, reversed, net ITC
7. Fill in the **Net Tax Liability** (Table 5):
   - Tax amounts for IGST, CGST, SGST/UTGST
   - Interest and late fees if applicable
8. Click **Save** → **Submit**.
9. Optionally click **Generate JSON** for manual upload.

### 4.1 Return Status Workflow

```
Draft (Not Filed)
    │
    ├──▶ Generate JSON ──▶ JSON Generated ──▶ (Manual upload)
    │
    └──▶ Submit ──▶ Filed
                    │
                    └──▶ Cancel ──▶ Not Filed (restored)
```

---

## 5. GST PORTAL API INTEGRATION

### 5.1 Overview
The app provides a built-in HTTP client for direct integration with the GSTN (GST portal) API. This allows OTP-based authentication, saving return data, filing returns, and checking filing status — all without leaving ERPNext.

### 5.2 Prerequisites
- **GST Settings** must be configured with:
  - `Enable GST Portal API Integration` checked
  - GST Portal Username entered
  - Company GSTIN set
- **Python packages:** `requests` and `cryptography` must be installed:
  ```bash
  pip install requests cryptography
  ```

### 5.3 Authentication Flow

```
Request OTP ──▶ Enter OTP ──▶ Authenticate ──▶ Session cached (5 hours)
```

1. Call **Request OTP** — sends OTP to registered mobile/email via GSTN
2. Enter the OTP received
3. Call **Authenticate** — exchanges OTP for auth token and secure key (SEK)
4. Session is cached in Frappe cache for 5 hours

### 5.4 Available API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `request_otp` | Whitelisted | Request OTP from GST portal |
| `authenticate` | Whitelisted | Authenticate with OTP |
| `save_gstr1` | Whitelisted | Save GSTR-1 data to GST portal |
| `file_gstr1` | Whitelisted | File GSTR-1 on GST portal |
| `check_gstr1_status` | Whitelisted | Check GSTR-1 filing status |
| `save_gstr3b` | Whitelisted | Save GSTR-3B data to GST portal |
| `file_gstr3b` | Whitelisted | File GSTR-3B on GST portal |
| `check_gstr3b_status` | Whitelisted | Check GSTR-3B filing status |
| `generate_gstr1_json` | Whitelisted | Generate GSTN-compliant JSON for GSTR-1 |
| `generate_gstr3b_json` | Whitelisted | Generate GSTN-compliant JSON for GSTR-3B |

### 5.5 API Payload Structure

The `_build_gstr1_payload()` and `_build_gstr3b_payload()` functions construct standard GSTN-compliant JSON structures from the document's child tables, ready for portal submission.

### 5.6 Encryption
The client uses RSA-OAEP encryption (SHA-256) to encrypt the app key with the GSTN public key during authentication, following the GSTN security specification.

---

## 6. GST INVOICE CUSTOMIZATION

### 6.1 Overview
`GST Invoice Customization` is a Single doctype that manages how Sales Invoice fields map to GSTR-1 and GSTR-3B return fields. It also controls invoice behavior settings and can deploy custom fields to the Sales Invoice doctype.

### 6.2 Configuration
1. Open **GST → Configuration → GST Invoice Customization**.
2. Configure **Invoice Behavior**:
   - Auto-fetch HSN Code from Item
   - Validate Customer GSTIN
   - Auto-set Place of Supply
   - Default HSN Code Length
   - Invoice Type Determination (Automatic / Manual)
   - Enable E-Invoice Fields
3. Manage **Field Mappings** — define how Sales Invoice fields map to GSTR return fields
4. Click **Deploy Custom Fields to Sales Invoice** to create the mapped custom fields on the Sales Invoice doctype
5. Click **Reset to Default Mappings** to restore the standard set of GST field mappings

### 6.3 Default Field Mappings
The app ships with these pre-defined field mappings:

| Source Field | Label | Target | Type |
|-------------|-------|--------|------|
| `custom_gst_category` | GST Category | Both | Select |
| `custom_place_of_supply` | Place of Supply | Both | Data |
| `custom_invoice_type` | Invoice Type | GSTR-1 | Select |
| `custom_ecommerce_gstin` | E-Commerce GSTIN | GSTR-1 | Data |
| `custom_reverse_charge` | Reverse Charge | Both | Check |
| `custom_port_code` | Port Code | GSTR-1 | Data |
| `custom_shipping_bill_number` | Shipping Bill Number | GSTR-1 | Data |
| `custom_shipping_bill_date` | Shipping Bill Date | GSTR-1 | Date |

### 6.4 GST Invoice Print Format
A standard GST-compliant **Print Format** (`GST Invoice`) is provided for the Sales Invoice doctype. It displays:
- Company details with GSTIN
- Customer name, address, and GSTIN
- Item table with HSN/SAC codes, UQC, quantity, rate, taxable value
- Tax summary with CGST/SGST/IGST breakdown
- Totals section with taxable value, tax, and grand total
- Amount in words
- Declaration and authorized signatory block

---

## 7. REPORTS

| Report | Type | Based On | Purpose |
|--------|------|----------|---------|
| GST Filing Status | Script Report | GSTR-1 Return / GSTR-3B Return | Combined filing status overview with stacked bar chart (Filed vs Pending) |
| GST Tax Liability | Script Report | GSTR-3B Return | Tax payable/paid trend over return periods with line chart |

### 7.1 GST Filing Status
- Combines GSTR-1 and GSTR-3B returns in a single view
- Filters: Company, Filing Status, Return Period
- Stacked bar chart showing filed vs pending returns by type
- Columns: Return Type, Period, Company, GSTIN, Status, Filing Date, Taxable Value, Tax Amount

### 7.2 GST Tax Liability
- Focuses on GSTR-3B tax liability data
- Filters: Company, Filing Status, Return Period
- Line chart showing tax payable vs tax paid trend across periods
- Columns: Period, Company, Status, Tax Payable, Tax Paid

### 7.3 Dashboard Charts
Two charts are auto-created in the GST workspace:
- **Filing Compliance** — Donut chart grouped by filing status
- **Tax Liability Trend** — Line chart of total tax payable over time

---

## 8. WORKSPACE NAVIGATION

The **GST** workspace is auto-created during migration with the following layout:

**Shortcuts (top row):**
- 📄 New GSTR-1
- 📄 New GSTR-3B
- ⚙️ GST Settings
- 📋 GSTR-1 List

**Key Metrics (number cards):**
- 📌 Pending GSTR-1 Filings
- 📌 Pending GSTR-3B Filings
- ✅ GSTR-1 Filed This Month
- 📊 Total GSTR-1 Filed

**Analytics (charts):**
- 📈 Filing Compliance — donut chart
- 📈 Tax Liability Trend — line chart

**Navigation Cards:**
- **Returns** — GSTR-1 Return, GSTR-3B Return
- **Configuration** — GST Settings, GST Invoice Customization, GST Field Mapping
- **Reports & Analytics** — GST Filing Status, GST Tax Liability

---

## 9. SCHEDULED TASKS & AUTOMATION

| Task | Frequency | What it does |
|------|-----------|--------------|
| `send_due_date_reminders` | Daily | Checks each company's GST Settings for in-app notification preferences. Sends reminders N days before GSTR-3B due date (20th) and GSTR-1 due date (11th). Includes estimated tax amount in GSTR-3B reminders |

> Make sure the scheduler is enabled: `bench --site your-site.com scheduler enable`

---

## 10. SETUP & CONFIGURATION (FIXTURES)

The following are set up automatically post-install/migrate:

- **Module Def** — "GST" module registered against the app
- **Roles** — GST Manager, Tax Accountant
- **GST Settings** — Singleton record for company configuration (auto-created)
- **GST Invoice Customization** — Singleton record for field mapping configuration (auto-created)
- **Workspace** — GST workspace with shortcuts, number cards, and charts
- **Dashboard Charts** — Filing Compliance (donut), Tax Liability Trend (line)
- **Default Field Mappings** — 8 standard field mappings for Sales Invoice → GST returns
- **Sales Invoice Custom Fields** — Custom fields deployed from active field mappings
- **Child Table Parent Columns** — Auto-fixed on first request via `before_request` hook

Standard Frappe fixtures (Workspace, DocType, Report, Role) are also exported for redeployment across sites.

---

## 11. DEMO DATA

Demo data is seeded automatically on first migration (via the `create_demo_doctypes` patch), and can be re-triggered manually:

```bash
bench --site your-site.com execute gst_automation.patches.create_demo_doctypes.execute
```

This creates sample **GSTR-1 Returns** and **GSTR-3B Returns** across 6 return periods (Jan–Jun 2026) with:
- Various filing statuses (Filed, JSON Generated, Not Filed)
- Realistic B2B invoice data with proper GST tax calculations
- HSN-wise summaries
- Outward supplies, ITC details, and net tax liability
- Staggered statuses for chart/analytics variety

---

## 12. TROUBLESHOOTING

| Issue | Cause | Solution |
|-------|-------|----------|
| "GST Settings not found" when submitting a return | GST Settings singleton record missing | Run `bench migrate` to apply the create_gst_settings patch; or open GST Settings page once to auto-create it |
| App not found during install | App not in apps list | `echo "gst_automation" >> sites/apps.txt` |
| `(1054, "Unknown column 'parent' in WHERE")` on a child table | Schema sync didn't create child-table columns | Handled automatically; to force it: `bench --site your-site.com execute gst_automation.patches.fix_child_table_parent_columns.execute` |
| GST workspace or charts missing | Workspace/chart patch didn't run | `bench --site your-site.com migrate` or run individual patches |
| Scheduled tasks not running | Scheduler disabled | `bench --site your-site.com scheduler enable` |
| Portal API authentication fails | Invalid credentials or network | Verify GST Settings credentials, check network connectivity to `https://api.gst.gov.in` |
| "The 'requests' library is required" | Missing dependency | `pip install requests` |
| "The 'cryptography' library is required" | Missing dependency | `pip install cryptography` |
| Generate JSON fails with no GSTIN | Company GSTIN not set | Set the GSTIN in GST Settings or directly on the return document |
| Return period validation error | Incorrect format | Use MMYYYY format (e.g., 042026 for April 2026) |
| Duplicate return period error | Return already exists for this company/period | Cancel or amend the existing return, or use a different period |

---

## 13. APPENDIX

### A. Role Permissions

| Role | GSTR-1 Return | GSTR-3B Return | GST Settings | GST Invoice Customization | Submit/Amend/Cancel |
|------|:-------------:|:--------------:|:------------:|:------------------------:|:-------------------:|
| System Manager | Full CRUD | Full CRUD | Full CRUD | Full CRUD | ✅ |
| GST Manager | Full CRUD | Full CRUD | Full CRUD | Full CRUD | ✅ |
| Tax Accountant | Read only | Read only | Read only | Read only | ❌ |

### B. Key DocType Field Reference

#### GSTR-1 Return
| Field | Type | Notes |
|-------|------|-------|
| Company | Link → Company | Required |
| Company GSTIN | Data | Auto-populated from GST Settings |
| Return Period | Data | MMYYYY format (e.g., 042026) |
| Filing Status | Select | Not Filed / JSON Generated / Uploaded / Filed |
| Filing Date | Date | Auto-set on submit |
| Generation Date | Datetime | Auto-set on JSON generation |
| B2B Invoices | Table → GSTR-1 B2B Invoice | B2B invoice line items |
| HSN Summary | Table → GSTR-1 HSN Summary | HSN-wise summary rows |
| JSON File | Attach | Generated JSON file for portal upload |

#### GSTR-3B Return
| Field | Type | Notes |
|-------|------|-------|
| Company | Link → Company | Required |
| Company GSTIN | Data | Auto-populated from GST Settings |
| Return Period | Data | MMYYYY format (e.g., 042026) |
| ITC Claim Period | Select | Current Period / Next Period |
| Filing Status | Select | Not Filed / JSON Generated / Uploaded / Filed |
| Filing Date | Date | Auto-set on submit |
| Outward Taxable Supplies | Table → GSTR-3B Outward Supply | Table 3.1(a) |
| Outward Zero-Rated Supplies | Table → GSTR-3B Outward Supply | Table 3.1(b) |
| ITC Details | Table → GSTR-3B ITC Detail | Table 4 |
| Net Liability | Table → GSTR-3B Net Liability | Table 5 |
| Total Tax Payable / Paid | Currency | Auto-calculated on submit |

#### GST Settings
| Field | Type | Notes |
|-------|------|-------|
| Company | Link → Company | Required |
| Company GSTIN | Data | Primary business GSTIN |
| Filing Frequency | Select | Monthly / Quarterly |
| Round Off GST | Check | Round off GST components |
| Validate HSN/SAC | Check | Validate HSN/SAC before invoice submit |
| Default HSN Length | Select | 4 / 6 / 8 digits |
| Reverse Charge Threshold | Currency | RCM applicability threshold |
| Enable API Integration | Check | Enable GST portal API |
| GST Username | Data | GST portal login username |
| GST API Endpoint | Data | Default: `https://api.gst.gov.in` |
| Notifications | Various | In-app and email reminder settings |

### C. Patches (Migration Order)

| # | Patch | Section | Purpose |
|---|-------|---------|---------|
| 1 | `create_gst_module` | `pre_model_sync` | Create "GST" Module Def |
| 2 | `fix_child_table_parent_columns` | `post_model_sync` | Fix missing parent columns on child tables |
| 3 | `create_gst_roles` | `post_model_sync` | Create GST Manager and Tax Accountant roles |
| 4 | `create_gst_settings` | `post_model_sync` | Create GST Settings singleton record |
| 5 | `create_gst_workspace` | `post_model_sync` | Create GST workspace with charts |
| 6 | `create_default_field_mappings` | `post_model_sync` | Seed default field mappings |
| 7 | `deploy_gst_custom_fields` | `post_model_sync` | Deploy active custom fields to Sales Invoice |
| 8 | `create_demo_doctypes` | `post_model_sync` | Create demo data across 6 return periods |

### D. API Payload Builders
The app uses two shared payload builder functions:
- `_build_gstr1_payload(doc)` — Constructs GSTN-compliant JSON for GSTR-1 (b2b, hsn sections)
- `_build_gstr3b_payload(doc)` — Constructs GSTN-compliant JSON for GSTR-3B (sup_details, itc_details, payment sections)

These are used by both the `generate_*_json` endpoints and the portal `save_*` API methods.

### E. Related Documents
- Frappe Framework Documentation: https://frappeframework.com/docs
- ERPNext Documentation: https://docs.erpnext.com
- GSTN API Specification: https://api.gst.gov.in
- Indian GST Portal: https://www.gst.gov.in

### F. Repository
- **Repository:** https://github.com/Pasha1234565/gst_automation.git

---

*End of README*
