# Automail Quick Reference

## Command Line Usage

```bash
# Run continuously (monitor inbox)
python automail.py

# Process once and exit
python automail.py --once

# Use custom config file
python automail.py --config my-config.json
```

## Configuration File (config.json)

```json
{
  "client_id": "your-azure-ad-client-id",
  "tenant_id": "common",
  "scopes": ["Mail.ReadWrite", "Mail.Send"],
  "reply_template": "reply_template.html",
  "attachments_folder": "attachments",
  "poll_interval_seconds": 60,
  "template_variables": {
    "name": "Valued Customer",
    "company": "Your Company"
  }
}
```

## Template Syntax

Use `{{variable}}` for placeholders:

```html
<p>Dear {{name}},</p>
<p>Thank you for contacting {{company}}.</p>
```

## File Structure

```
Automail/
├── automail.py              # Main script
├── graph_auth.py            # Authentication
├── email_handler.py         # Email operations
├── template_engine.py       # Template rendering
├── config.json              # Your configuration (not in git)
├── reply_template.html      # Email template
├── attachments/             # Files to attach
└── requirements.txt         # Dependencies
```

## Modules Overview

### automail.py
Main application entry point with CLI interface.

**Key Functions:**
- `start(continuous)` - Start the application
- `run_once()` - Process emails once
- `run_continuous()` - Monitor inbox continuously

### graph_auth.py
Microsoft Graph API authentication using device code flow.

**Key Class:** `GraphAuthenticator`
- `get_access_token()` - Authenticate and get token
- Token caching in `token_cache.bin`

### email_handler.py
Email operations using Graph API.

**Key Class:** `EmailHandler`
- `get_unread_messages()` - Fetch unread emails
- `send_reply()` - Send auto-reply with attachments
- `mark_as_read()` - Mark message as read

### template_engine.py
HTML template rendering with variable substitution.

**Key Class:** `TemplateEngine`
- `render(variables)` - Replace placeholders
- `get_placeholders()` - List all placeholders

## Common Tasks

### Change Reply Message
Edit `reply_template.html`

### Add Template Variable
1. Add `{{variable}}` to template
2. Add to `config.json` under `template_variables`

### Add Attachment
Copy file to `attachments/` folder

### Change Poll Interval
Modify `poll_interval_seconds` in `config.json`

### Re-authenticate
Delete `token_cache.bin` and restart

## Python API Usage

```python
from automail import Automail

# Create instance
app = Automail(config_path="config.json")

# Run once
app.start(continuous=False)

# Run continuously
app.start(continuous=True)
```

## Environment Variables (Optional)

You can use environment variables instead of config.json:

```python
import os
import json

config = {
    "client_id": os.getenv("AUTOMAIL_CLIENT_ID"),
    "tenant_id": os.getenv("AUTOMAIL_TENANT_ID", "common"),
    # ... other settings
}

with open("config.json", "w") as f:
    json.dump(config, f)
```

## Error Handling

The application logs errors to console. Common error messages:

- `"Failed to authenticate"` - Check client ID and permissions
- `"Error fetching messages"` - Check token and network
- `"Error sending reply"` - Check Mail.Send permission
- `"Template file not found"` - Check template path in config

## Performance Tips

- Increase `poll_interval_seconds` to reduce API calls
- Use `--once` mode for testing
- Remove large attachments to speed up sending
- Cache token is valid for ~1 hour by default

## Security Checklist

- ✓ Config file not in version control
- ✓ Token cache not in version control
- ✓ Client ID kept secure
- ✓ Minimum required permissions only
- ✓ Regular credential rotation

## Useful Graph API Endpoints

The application uses these endpoints:

```
GET  /me/messages                     # List messages
POST /me/messages/{id}/reply          # Send reply
POST /me/messages/{id}/createReply    # Create draft
PATCH /me/messages/{id}               # Update message
POST /me/messages/{id}/attachments    # Add attachment
POST /me/messages/{id}/send           # Send draft
```

## Template Variables Best Practices

- Use descriptive variable names: `{{customer_name}}` not `{{n}}`
- Keep variable names simple (alphanumeric + underscore)
- Document available variables in template comments
- Provide default values in config

## Testing Checklist

Before production use:

1. ✓ Test authentication flow
2. ✓ Send test email to yourself
3. ✓ Verify reply is received
4. ✓ Check attachments are included
5. ✓ Verify template renders correctly
6. ✓ Test error scenarios (no config, bad token, etc.)
7. ✓ Monitor for a few hours in test mode

## Monitoring

Watch console output for:
- Authentication status
- Messages found
- Replies sent
- Errors encountered

Example output:
```
[2024-01-15 10:30:00] Checking for unread messages...
Found 2 unread message(s)
Processing message:
  From: user@example.com
  Subject: Hello
✓ Reply sent successfully!
✓ Message marked as read
```
