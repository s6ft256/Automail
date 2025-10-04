Automail MVP - Automated Email Replies (Microsoft Graph)
=======================================================

This is a minimal, cross-platform script that replies to unread emails in your Outlook/Exchange Online mailbox using the Microsoft Graph API and Device Code authentication.

What it does
------------
- Authenticates with Microsoft Graph using delegated user auth (device code flow)
- Fetches unread emails from Inbox
- Generates an HTML reply from `reply_template.html` using Jinja2 placeholders like `{{name}}`
- Attaches all files found in `attachments/`
- Sends the reply as a threaded reply and categorizes the original message as `AutoReplied`
- Supports dry-run mode (prints instead of sending)
- Can run once or on a schedule (interval)
- Logs to `autoreply.log`

Requirements
------------
- Python 3.8+
- Azure AD App Registration with delegated permissions: `Mail.ReadWrite`, `Mail.Send`
- Dependencies: `msal`, `requests`, `jinja2`

Install dependencies
--------------------
```bash
pip install msal requests jinja2
```

Configure Microsoft Graph
-------------------------
1. In Azure Portal: Azure Active Directory > App registrations > New registration
	- Name: Automail (or anything)
	- Supported account types: Single tenant (or as needed)
	- Redirect URI: not required for device code flow
	- After creating, copy:
	  - Application (client) ID
	  - Directory (tenant) ID
2. API Permissions:
	- Add delegated permissions: `Mail.ReadWrite`, `Mail.Send`
	- Grant admin consent if required by your tenant

Environment variables
---------------------
Set the following before running:

```bash
export AUTOMAIL_CLIENT_ID="<your_client_id>"
export AUTOMAIL_TENANT_ID="<your_tenant_id>"
```

Optional environment variables:
- `AUTOMAIL_TEMPLATE` (default: `reply_template.html`)
- `AUTOMAIL_ATTACHMENTS_DIR` (default: `attachments`)
- `AUTOMAIL_LOG` (default: `autoreply.log`)

Files
-----
- `automail.py` – main script
- `reply_template.html` – example Jinja2 HTML template with placeholders
- `attachments/` – place any files here to be attached to replies

Run (dry run)
-------------
Print what would be sent without sending any email:

```bash
python automail.py --dry-run
```

Run (live)
----------
Reply once and exit:

```bash
python automail.py
```

Run on a schedule (every 60s)
-----------------------------
```bash
python automail.py --interval 60
```

Additional options
------------------
```bash
python automail.py --help
```

Notes and limitations
---------------------
- This is an MVP for low-volume use (<50 incoming emails/hour).
- The script skips obvious no-reply addresses.
- On first run, device code flow will prompt you to visit a URL and enter a code.
- Replies are created as a message in the original thread (createReply) and sent.
- The original message gets a category `AutoReplied` for tracking.
- Outlook COM fallback (pywin32) is Windows-only and intentionally omitted here to keep dependencies minimal; Microsoft Graph is the preferred and implemented path in this MVP.

Troubleshooting
---------------
- If authentication fails, verify `AUTOMAIL_CLIENT_ID` and `AUTOMAIL_TENANT_ID` and that permissions are granted.
- If you see 403/401 from Graph, ensure admin consent is granted and delegated permissions are correct.
- Ensure `reply_template.html` exists and is readable.
- If attachments fail, check file sizes and names; large files may exceed limits.

# Automail
An application with libs to work with matrices
