# Automail

An automatic email reply system that monitors your inbox and sends predefined responses with optional attachments using Microsoft Graph API.

## Features

- 🔐 **Microsoft Graph API Authentication** - Secure authentication using device code flow
- 📧 **Automatic Email Replies** - Automatically respond to unread emails
- 📎 **Attachment Support** - Include files from a specified folder in replies
- 🎨 **HTML Templates** - Use customizable HTML templates with placeholders
- ⚙️ **Configurable** - Easy JSON-based configuration
- 🔄 **Continuous Monitoring** - Poll for new emails at configurable intervals
- 🪟 **Windows Fallback** - Optional pywin32 support for Outlook COM (Windows only)

## Prerequisites

- Python 3.7 or higher
- Microsoft Azure AD application with the following:
  - Client ID
  - Permissions: `Mail.ReadWrite`, `Mail.Send`
  - Configured as a public client (mobile and desktop flows enabled)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/s6ft256/Automail.git
cd Automail
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up configuration:
```bash
cp config.example.json config.json
```

4. Edit `config.json` with your Azure AD application details:
```json
{
  "client_id": "YOUR_CLIENT_ID_HERE",
  "tenant_id": "common",
  "scopes": ["Mail.ReadWrite", "Mail.Send"],
  "reply_template": "reply_template.html",
  "attachments_folder": "attachments",
  "poll_interval_seconds": 60,
  "template_variables": {
    "name": "Valued Customer",
    "company": "Automail Inc."
  }
}
```

## Azure AD App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations** > **New registration**
3. Register your application:
   - Name: Automail (or any name you prefer)
   - Supported account types: Choose based on your needs
   - Redirect URI: Not needed for device code flow
4. After registration, note your **Application (client) ID**
5. Go to **API permissions** > **Add a permission** > **Microsoft Graph** > **Delegated permissions**
6. Add these permissions:
   - `Mail.ReadWrite`
   - `Mail.Send`
7. Go to **Authentication** > **Advanced settings** and enable **"Allow public client flows"**

## Usage

### Run Continuously (Default)

Monitor inbox and automatically reply to new emails:

```bash
python automail.py
```

### Run Once

Process current unread emails and exit:

```bash
python automail.py --once
```

### Custom Configuration File

Use a different configuration file:

```bash
python automail.py --config my-config.json
```

## Template Customization

Edit `reply_template.html` to customize your auto-reply message. Use `{{variable}}` syntax for placeholders:

```html
<p>Dear {{name}},</p>
<p>Thank you for contacting {{company}}.</p>
```

Define placeholder values in `config.json`:

```json
{
  "template_variables": {
    "name": "Valued Customer",
    "company": "Your Company Name"
  }
}
```

## Attachments

Place files in the `attachments/` folder to automatically include them in all auto-replies. The system will attach all files in this folder (except README.txt).

## Authentication Flow

On first run, the application will display a device code authentication message:

```
============================================================
AUTHENTICATION REQUIRED
============================================================
To sign in, use a web browser to open the page https://microsoft.com/devicelogin
and enter the code XXXXXXXXX to authenticate.
============================================================
```

Follow the instructions to authenticate. The token will be cached in `token_cache.bin` for future use.

## Configuration Options

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `client_id` | string | Azure AD application client ID | Required |
| `tenant_id` | string | Azure AD tenant ID | "common" |
| `scopes` | array | Graph API permission scopes | ["Mail.ReadWrite", "Mail.Send"] |
| `reply_template` | string | Path to HTML template file | "reply_template.html" |
| `attachments_folder` | string | Path to attachments directory | "attachments" |
| `poll_interval_seconds` | integer | Seconds between inbox checks | 60 |
| `template_variables` | object | Variables for template substitution | {} |

## File Structure

```
Automail/
├── automail.py              # Main application script
├── graph_auth.py            # Microsoft Graph authentication
├── email_handler.py         # Email operations
├── template_engine.py       # Template rendering
├── config.json              # Configuration (not in git)
├── config.example.json      # Example configuration
├── reply_template.html      # Email reply template
├── attachments/             # Folder for attachment files
│   └── README.txt
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Security Notes

- Never commit `config.json` or `token_cache.bin` to version control
- Keep your Azure AD client ID and tokens secure
- Regularly review and rotate your credentials
- Use appropriate Azure AD permission scopes (principle of least privilege)

## Troubleshooting

### Authentication Issues

- Ensure your Azure AD app has "Allow public client flows" enabled
- Verify the client ID is correct
- Check that required permissions are granted and admin consent is provided if needed

### Email Not Sending

- Verify you have granted `Mail.ReadWrite` and `Mail.Send` permissions
- Check that your account has an active mailbox
- Review the console output for specific error messages

### Missing Attachments

- Ensure files are placed in the `attachments/` folder
- Check file permissions
- Large attachments may fail - Graph API has size limits

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
