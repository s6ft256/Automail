# Automail Setup Guide

This guide walks you through setting up Automail for the first time.

## Quick Start

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Register Azure AD Application

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations** → **New registration**
3. Fill in the registration form:
   - **Name**: `Automail` (or your preferred name)
   - **Supported account types**: 
     - Select "Accounts in this organizational directory only" for single tenant
     - Or "Accounts in any organizational directory" for multi-tenant
   - **Redirect URI**: Leave blank (not needed for device code flow)
4. Click **Register**

### 3. Configure Permissions

After registration:

1. Click on **API permissions** in the left sidebar
2. Click **Add a permission**
3. Select **Microsoft Graph**
4. Select **Delegated permissions**
5. Add these permissions:
   - `Mail.ReadWrite` - Read and write access to user mail
   - `Mail.Send` - Send mail on behalf of user
6. Click **Add permissions**
7. (Optional) If admin consent is required, click **Grant admin consent**

### 4. Enable Public Client Flow

1. Click on **Authentication** in the left sidebar
2. Scroll to **Advanced settings**
3. Under "Allow public client flows", toggle **YES**
4. Click **Save**

### 5. Get Your Client ID

1. Click on **Overview** in the left sidebar
2. Copy the **Application (client) ID**
3. Keep this ID for the next step

### 6. Create Configuration File

```bash
cp config.example.json config.json
```

Edit `config.json` and replace `YOUR_CLIENT_ID_HERE` with your actual client ID:

```json
{
  "client_id": "12345678-1234-1234-1234-123456789abc",
  "tenant_id": "common",
  "scopes": ["Mail.ReadWrite", "Mail.Send"],
  "reply_template": "reply_template.html",
  "attachments_folder": "attachments",
  "poll_interval_seconds": 60,
  "template_variables": {
    "name": "Valued Customer",
    "company": "Your Company Name"
  }
}
```

### 7. Customize Your Reply Template

Edit `reply_template.html` to customize your auto-reply message:

```html
<!DOCTYPE html>
<html>
<body>
    <p>Dear {{name}},</p>
    <p>Your custom message here...</p>
    <p>Best regards,<br>{{company}}</p>
</body>
</html>
```

### 8. Add Attachments (Optional)

Place any files you want to attach in the `attachments/` folder:

```bash
cp /path/to/your/file.pdf attachments/
```

### 9. Run Automail

First run (one-time processing):

```bash
python automail.py --once
```

Continuous monitoring:

```bash
python automail.py
```

### 10. Authenticate

On first run, you'll see:

```
============================================================
AUTHENTICATION REQUIRED
============================================================
To sign in, use a web browser to open the page 
https://microsoft.com/devicelogin and enter the code 
XXXXXXXXX to authenticate.
============================================================
```

1. Open the URL in your browser
2. Enter the code shown
3. Sign in with your Microsoft account
4. Grant the requested permissions
5. Return to the terminal

The authentication token will be cached in `token_cache.bin` for future use.

## Troubleshooting

### "Failed to authenticate"

- Verify your client ID is correct
- Ensure "Allow public client flows" is enabled
- Check that permissions are granted

### "Permission denied" errors

- Ensure you've granted `Mail.ReadWrite` and `Mail.Send` permissions
- Admin consent may be required in some organizations

### No emails being processed

- Check that you have unread emails in your inbox
- Verify your poll interval settings
- Review console output for errors

### Attachments not working

- Ensure files exist in the `attachments/` folder
- Check file sizes (Graph API has limits)
- Verify file permissions

## Advanced Configuration

### Change Poll Interval

Modify `poll_interval_seconds` in `config.json`:

```json
{
  "poll_interval_seconds": 120
}
```

### Use Different Template

Create a new template file and update `config.json`:

```json
{
  "reply_template": "my-custom-template.html"
}
```

### Multiple Attachment Folders

Currently, only one folder is supported. To use multiple folders, create symbolic links or copy files to the main attachments folder.

### Run as a Service

#### Linux (systemd)

Create `/etc/systemd/system/automail.service`:

```ini
[Unit]
Description=Automail Auto-Reply Service
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/Automail
ExecStart=/usr/bin/python3 /path/to/Automail/automail.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable automail
sudo systemctl start automail
```

#### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., "At startup")
4. Set action: Start a program
   - Program: `python.exe`
   - Arguments: `C:\path\to\Automail\automail.py`
   - Start in: `C:\path\to\Automail`

## Security Best Practices

- Never commit `config.json` or `token_cache.bin` to version control
- Use least privilege permissions (only grant required scopes)
- Regularly review and rotate credentials
- Store configuration files securely
- Consider using environment variables for sensitive data
- Enable MFA on your Microsoft account

## Getting Help

If you encounter issues:

1. Check the console output for error messages
2. Review this setup guide
3. Consult the main README.md
4. Check Azure AD app configuration
5. Verify permissions and authentication settings

## Next Steps

- Customize your reply template
- Add company-specific attachments
- Set up as a background service
- Monitor logs and adjust poll interval
- Test with various email scenarios
