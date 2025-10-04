#!/usr/bin/env python3
"""
Automail MVP: Automated email replies via Microsoft Graph API (device code flow).

Features:
- Auth via device code (delegated) using msal
- Fetch unread Inbox messages
- Generate HTML reply from Jinja2 template with placeholders (e.g., {{name}})
- Attach all files from attachments/ directory
- Send reply as an actual thread reply (createReply -> add body/attachments -> send)
- Mark original as replied implicitly by using the reply flow; also add a category "AutoReplied"
- CLI flags: --dry-run, --interval N, --max N, --verbose
- Logging to autoreply.log

Dependencies: msal, requests, jinja2
Cross-platform: Windows/Mac/Linux

Configuration via environment variables:
- AUTOMAIL_CLIENT_ID: Azure AD app's Application (client) ID (required)
- AUTOMAIL_TENANT_ID: Azure AD Directory (tenant) ID (required)

Usage examples:
- Dry run once: python automail.py --dry-run
- Live run every 60s: python automail.py --interval 60
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional

# Lazy-import optional third-party libs so --help works without them installed
try:
    import requests  # type: ignore
except Exception:  # pragma: no cover - import-time guard
    requests = None  # type: ignore

try:
    import msal  # type: ignore
except Exception:  # pragma: no cover - import-time guard
    msal = None  # type: ignore

try:
    from jinja2 import Template  # type: ignore
except Exception:  # pragma: no cover - import-time guard
    Template = None  # type: ignore


# --- Defaults / constants ---
REPLY_TEMPLATE_PATH = os.environ.get("AUTOMAIL_TEMPLATE", "reply_template.html")
ATTACHMENTS_DIR = os.environ.get("AUTOMAIL_ATTACHMENTS_DIR", "attachments")
LOG_FILE = os.environ.get("AUTOMAIL_LOG", "autoreply.log")

CLIENT_ID = os.environ.get("AUTOMAIL_CLIENT_ID", "")
TENANT_ID = os.environ.get("AUTOMAIL_TENANT_ID", "")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}" if TENANT_ID else ""
SCOPES = ["Mail.ReadWrite", "Mail.Send"]

# Simple filters to avoid replying to obvious no-reply addresses
NO_REPLY_HINTS = (
    "no-reply", "noreply", "do-not-reply", "donotreply", "mailer-daemon", "postmaster"
)


def ensure_deps():
    missing = []
    if requests is None:
        missing.append("requests")
    if msal is None:
        missing.append("msal")
    if Template is None:
        missing.append("jinja2")
    if missing:
        print(
            "Missing dependencies: " + ", ".join(missing) +
            "\nInstall them with: pip install msal requests jinja2",
            file=sys.stderr,
        )
        sys.exit(1)


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def load_template(path: str) -> Template:
    if Template is None:
        raise RuntimeError("jinja2 not available")
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Template file not found at '{path}'. Create it or set AUTOMAIL_TEMPLATE."
        )
    with open(path, "r", encoding="utf-8") as f:
        return Template(f.read())


def read_attachments(dir_path: str) -> List[Dict[str, Any]]:
    attachments: List[Dict[str, Any]] = []
    if not os.path.isdir(dir_path):
        logging.info("Attachments directory '%s' not found; continuing without attachments.", dir_path)
        return attachments
    for fname in sorted(os.listdir(dir_path)):
        fpath = os.path.join(dir_path, fname)
        if not os.path.isfile(fpath):
            continue
        # Skip hidden files
        if fname.startswith('.'):
            continue
        try:
            with open(fpath, "rb") as fh:
                content_bytes = fh.read()
            b64 = base64.b64encode(content_bytes).decode("ascii")
            attachments.append({
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": fname,
                "contentBytes": b64,
            })
        except Exception as e:
            logging.error("Failed reading attachment '%s': %s", fpath, e)
    return attachments


class GraphClient:
    def __init__(self, client_id: str, tenant_id: str, scopes: List[str]):
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.scopes = scopes
        self._app: Optional[msal.PublicClientApplication] = None
        self._token: Optional[str] = None
        self._cache: Optional["msal.SerializableTokenCache"] = None
        self._cache_path = os.path.join(os.getcwd(), ".automail_token_cache.bin")

    def _init_app(self) -> msal.PublicClientApplication:
        assert msal is not None
        if not self._app:
            # Simple persistent cache for better UX across runs
            self._cache = msal.SerializableTokenCache()
            if os.path.exists(self._cache_path):
                try:
                    with open(self._cache_path, "r") as f:
                        self._cache.deserialize(f.read())  # type: ignore[arg-type]
                except Exception:
                    pass
            self._app = msal.PublicClientApplication(
                self.client_id,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}",
                token_cache=self._cache,
            )
        return self._app

    def get_token(self, force_interactive: bool = False) -> str:
        app = self._init_app()
        if not force_interactive:
            accounts = app.get_accounts()
            if accounts:
                result = app.acquire_token_silent(self.scopes, account=accounts[0])
                if result and "access_token" in result:
                    self._token = result["access_token"]
                    return self._token
        # Device code flow
        flow = app.initiate_device_flow(scopes=self.scopes)
        if "user_code" not in flow:
            raise RuntimeError("Failed to create device flow: %s" % json.dumps(flow, indent=2))
        print(flow["message"])  # Shows device code and verification URL to the user
        result = app.acquire_token_by_device_flow(flow)
        if not result or "access_token" not in result:
            raise RuntimeError("Authentication failed: %s" % json.dumps(result, indent=2))
        self._token = result["access_token"]
        # Persist cache if changed
        if self._cache is not None:
            try:
                if self._cache.has_state_changed:  # type: ignore[attr-defined]
                    with open(self._cache_path, "w") as f:
                        f.write(self._cache.serialize())  # type: ignore[arg-type]
            except Exception:
                pass
        return self._token

    def _headers(self) -> Dict[str, str]:
        if not self._token:
            raise RuntimeError("Token not available; call get_token() first")
        return {"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}

    def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        assert requests is not None
        return requests.get(url, headers=self._headers(), params=params or {}, timeout=20)

    def post(self, url: str, payload: Any = None) -> requests.Response:
        assert requests is not None
        return requests.post(url, headers=self._headers(), json=payload, timeout=30)

    def patch(self, url: str, payload: Any = None) -> requests.Response:
        assert requests is not None
        return requests.patch(url, headers=self._headers(), json=payload, timeout=30)


def fetch_unread_emails(gc: GraphClient, max_count: int = 50) -> List[Dict[str, Any]]:
    url = "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages"
    params = {
        "$filter": "isRead eq false and isDraft eq false",
        "$orderby": "receivedDateTime desc",
        "$top": max(1, min(max_count, 50)),
        "$select": "id,subject,from,receivedDateTime,conversationId",
    }
    resp = gc.get(url, params=params)
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to fetch unread emails: {resp.status_code} {resp.text}")
    data = resp.json()
    messages = data.get("value", [])
    # Filter out obvious no-reply addresses
    filtered: List[Dict[str, Any]] = []
    for m in messages:
        try:
            addr = (m.get("from") or {}).get("emailAddress", {}).get("address", "")
        except Exception:
            addr = ""
        if not addr:
            continue
        if any(hint in addr.lower() for hint in NO_REPLY_HINTS):
            logging.info("Skipping no-reply address: %s (id=%s)", addr, m.get("id"))
            continue
        filtered.append(m)
    return filtered


def mark_replied(gc: GraphClient, message_id: str, category: str = "AutoReplied") -> None:
    # Mark as read and add a category for tracking.
    url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}"
    payload = {"isRead": True, "categories": [category]}
    resp = gc.patch(url, payload)
    if resp.status_code not in (200, 202):
        logging.debug("Failed to mark message %s as replied: %s", message_id, resp.text)


def create_reply_draft(gc: GraphClient, message_id: str) -> Dict[str, Any]:
    url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/createReply"
    resp = gc.post(url, payload={})
    if resp.status_code != 201:
        raise RuntimeError(f"Failed to create reply draft: {resp.status_code} {resp.text}")
    return resp.json()


def update_reply_body(gc: GraphClient, reply_id: str, html: str) -> None:
    url = f"https://graph.microsoft.com/v1.0/me/messages/{reply_id}"
    payload = {"body": {"contentType": "HTML", "content": html}}
    resp = gc.patch(url, payload)
    if resp.status_code not in (200, 202):
        raise RuntimeError(f"Failed to update reply body: {resp.status_code} {resp.text}")


def add_attachments_to_message(gc: GraphClient, message_id: str, attachments: List[Dict[str, Any]]) -> None:
    if not attachments:
        return
    url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/attachments"
    for att in attachments:
        resp = gc.post(url, payload=att)
        if resp.status_code != 201:
            raise RuntimeError(
                f"Failed to add attachment '{att.get('name')}': {resp.status_code} {resp.text}"
            )


def send_message(gc: GraphClient, message_id: str) -> None:
    url = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/send"
    resp = gc.post(url, payload=None)
    if resp.status_code != 202:
        raise RuntimeError(f"Failed to send message: {resp.status_code} {resp.text}")


def render_reply(template: Template, sender_name: str, sender_email: str, subject: str) -> str:
    # Provide a few common placeholders
    return template.render(name=sender_name or "there", email=sender_email, subject=subject)


def process_once(gc: GraphClient, template: Template, attachments: List[Dict[str, Any]], dry_run: bool, max_to_process: int) -> int:
    messages = fetch_unread_emails(gc, max_count=max_to_process)
    processed = 0
    for msg in messages:
        msg_id = msg.get("id")
        subject = msg.get("subject", "")
        from_obj = (msg.get("from") or {}).get("emailAddress", {})
        sender_email = from_obj.get("address", "")
        sender_name = from_obj.get("name", "") or sender_email
        if not msg_id or not sender_email:
            logging.debug("Skipping message without id or sender: %s", msg)
            continue

        try:
            reply_html = render_reply(template, sender_name, sender_email, subject)
            if dry_run:
                logging.info(
                    "DRY-RUN: Would reply to %s (id=%s, subject='Re: %s') with %d attachment(s)",
                    sender_email, msg_id, subject, len(attachments)
                )
                # Print to console for visibility
                print("----- DRY RUN REPLY START -----")
                print(reply_html)
                print("----- DRY RUN REPLY END -----\n")
            else:
                draft = create_reply_draft(gc, msg_id)
                reply_id = draft.get("id")
                if not reply_id:
                    raise RuntimeError("Reply draft did not return an id")
                update_reply_body(gc, reply_id, reply_html)
                add_attachments_to_message(gc, reply_id, attachments)
                send_message(gc, reply_id)
                mark_replied(gc, msg_id, category="AutoReplied")
                logging.info("Replied to %s for message %s", sender_email, msg_id)
            processed += 1
        except Exception as e:
            logging.error("Failed processing message %s (%s): %s", msg_id, sender_email, e)
    return processed


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Automated email replies via Microsoft Graph")
    p.add_argument("--dry-run", action="store_true", help="Print replies instead of sending")
    p.add_argument("--interval", type=int, default=0, help="Run every N seconds (0 = run once and exit)")
    p.add_argument("--max", dest="max_to_process", type=int, default=50, help="Max unread messages to process per run")
    p.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return p.parse_args(argv)


def assert_config_required_if_live(is_dry_run: bool) -> None:
    if is_dry_run:
        return
    if not CLIENT_ID or not TENANT_ID:
        print(
            "Missing configuration: set AUTOMAIL_CLIENT_ID and AUTOMAIL_TENANT_ID environment variables.",
            file=sys.stderr,
        )
        sys.exit(2)


def sample_messages() -> List[Dict[str, Any]]:
    # Offline preview messages used in --dry-run to avoid Graph dependency
    return [
        {
            "id": "sample-1",
            "subject": "Question about your product",
            "from": {"emailAddress": {"address": "john.doe@example.com", "name": "John Doe"}},
        },
        {
            "id": "sample-2",
            "subject": "Support request",
            "from": {"emailAddress": {"address": "jane.smith@example.org", "name": "Jane Smith"}},
        },
    ]


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)
    setup_logging(verbose=args.verbose)
    ensure_deps()
    assert_config_required_if_live(args.dry_run)

    # Prepare resources
    try:
        template = load_template(REPLY_TEMPLATE_PATH)
    except Exception as e:
        logging.error("Failed to load template '%s': %s", REPLY_TEMPLATE_PATH, e)
        sys.exit(1)

    attachments = read_attachments(ATTACHMENTS_DIR)

    # In dry-run, run offline preview without Graph auth
    offline_preview = args.dry_run
    gc: Optional[GraphClient] = None
    if not offline_preview:
        gc = GraphClient(CLIENT_ID, TENANT_ID, SCOPES)
        # Acquire token upfront
        try:
            gc.get_token()
        except Exception as e:
            logging.error("Authentication error: %s", e)
            sys.exit(1)

    def run_once() -> int:
        if offline_preview or gc is None:
            # Render and print previews from sample messages
            processed = 0
            for msg in sample_messages()[: max(1, min(args.max_to_process, 50))]:
                subject = msg.get("subject", "")
                from_obj = (msg.get("from") or {}).get("emailAddress", {})
                sender_email = from_obj.get("address", "")
                sender_name = from_obj.get("name", "") or sender_email
                reply_html = render_reply(template, sender_name, sender_email, subject)
                logging.info(
                    "DRY-RUN: Would reply to %s (subject='Re: %s') with %d attachment(s)",
                    sender_email, subject, len(attachments)
                )
                print("----- DRY RUN REPLY START -----")
                print(reply_html)
                print("----- DRY RUN REPLY END -----\n")
                processed += 1
            return processed
        else:
            return process_once(gc, template, attachments, args.dry_run, args.max_to_process)

    if args.interval and args.interval > 0:
        logging.info("Starting scheduled mode: every %d seconds", args.interval)
        total = 0
        while True:
            try:
                processed = run_once()
                total += processed
                logging.debug("Processed %d messages this cycle (total=%d)", processed, total)
            except Exception as e:
                logging.error("Run cycle failed: %s", e)
            # Refresh token silently each cycle (if live mode)
            if not offline_preview and gc is not None:
                try:
                    gc.get_token(force_interactive=False)
                except Exception:
                    pass
            time.sleep(args.interval)
    else:
        processed = run_once()
        logging.info("Done. Processed %d unread messages.", processed)


if __name__ == "__main__":
    main()
