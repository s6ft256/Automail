# Automail System Architecture

## Overview

Automail is a Python-based email automation system that monitors an inbox and automatically sends predefined replies with attachments using Microsoft Graph API.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User / Administrator                     │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ Configures
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Configuration Layer                         │
├─────────────────────────────────────────────────────────────────┤
│  • config.json        - Application settings                     │
│  • reply_template.html - HTML email template                     │
│  • attachments/       - Files to attach                          │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ Loads
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Application Layer (automail.py)               │
├─────────────────────────────────────────────────────────────────┤
│  • CLI Interface                                                 │
│  • Main orchestration logic                                      │
│  • Continuous monitoring loop                                    │
│  • Message processing pipeline                                   │
└───────┬─────────────────┬─────────────────┬─────────────────────┘
        │                 │                 │
        │ Uses            │ Uses            │ Uses
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│ graph_auth.py│  │template_     │  │ email_handler.py │
│              │  │engine.py     │  │                  │
├──────────────┤  ├──────────────┤  ├──────────────────┤
│Authentication│  │Template      │  │Email Operations  │
│- Device Flow │  │- Load HTML   │  │- Fetch Messages  │
│- Token Cache │  │- Replace     │  │- Send Replies    │
│- MSAL Client │  │  Placeholders│  │- Add Attachments │
└──────┬───────┘  └──────────────┘  └────────┬─────────┘
       │                                      │
       │ Authenticates                        │ API Calls
       ▼                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Microsoft Graph API                           │
├─────────────────────────────────────────────────────────────────┤
│  • Authentication Endpoint (login.microsoftonline.com)           │
│  • Graph API Endpoint (graph.microsoft.com/v1.0)                 │
│  • Mail.ReadWrite, Mail.Send permissions                         │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ Accesses
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Microsoft 365 Mailbox                         │
├─────────────────────────────────────────────────────────────────┤
│  • Read unread messages                                          │
│  • Send replies with attachments                                 │
│  • Mark messages as read                                         │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Application Layer (automail.py)

**Responsibilities:**
- CLI interface and argument parsing
- Configuration loading and validation
- Main orchestration of the auto-reply process
- Continuous monitoring loop with configurable intervals
- Error handling and logging

**Key Classes:**
- `Automail` - Main application class

**Key Methods:**
- `start(continuous)` - Entry point
- `run_once()` - Process emails once
- `run_continuous()` - Monitor continuously
- `_process_message(message)` - Handle single message

**Flow:**
1. Load configuration from JSON
2. Initialize authentication
3. Initialize template engine
4. Enter monitoring loop (continuous or one-time)
5. For each unread message:
   - Render template
   - Collect attachments
   - Send reply
   - Mark as read

### 2. Authentication Module (graph_auth.py)

**Responsibilities:**
- Microsoft Graph API authentication
- Device code flow implementation
- Token caching and refresh
- MSAL (Microsoft Authentication Library) integration

**Key Classes:**
- `GraphAuthenticator` - Handles authentication

**Authentication Flow:**
1. Check for cached token
2. If no cache, initiate device code flow
3. Display code to user
4. Wait for user authentication
5. Receive and cache access token
6. Return token for API calls

**Token Management:**
- Tokens cached in `token_cache.bin`
- Automatic silent refresh when possible
- Re-authentication prompt when needed

### 3. Email Handler Module (email_handler.py)

**Responsibilities:**
- Microsoft Graph API email operations
- Message retrieval and filtering
- Reply sending with attachments
- Message status updates

**Key Classes:**
- `EmailHandler` - Email operations

**Key Methods:**
- `get_unread_messages()` - Fetch unread inbox messages
- `send_reply()` - Send reply (simple or with attachments)
- `_send_reply_with_attachments()` - Create draft, attach, send
- `_add_attachment()` - Attach file to message
- `mark_as_read()` - Update message status

**API Endpoints Used:**
```
GET  /me/messages                     # List messages
POST /me/messages/{id}/reply          # Quick reply
POST /me/messages/{id}/createReply    # Create draft
PATCH /me/messages/{id}               # Update message
POST /me/messages/{id}/attachments    # Add attachment
POST /me/messages/{id}/send           # Send draft
```

### 4. Template Engine (template_engine.py)

**Responsibilities:**
- Load HTML template files
- Parse placeholder syntax
- Replace placeholders with values
- Return rendered HTML

**Key Classes:**
- `TemplateEngine` - Template rendering

**Placeholder Syntax:**
- Format: `{{variable_name}}`
- Example: `{{name}}`, `{{company}}`

**Process:**
1. Load template from file
2. Identify all placeholders using regex
3. Replace each placeholder with corresponding value
4. Return rendered HTML string

## Data Flow

### Typical Request Flow

```
User Action
    │
    ├─> Start Application (python automail.py)
    │
    ▼
Configuration Loading
    │
    ├─> Load config.json
    ├─> Load reply_template.html
    ├─> Scan attachments/ folder
    │
    ▼
Authentication
    │
    ├─> Check token_cache.bin
    ├─> If expired/missing: Device Code Flow
    ├─> Display code to user
    ├─> User authenticates via browser
    ├─> Receive and cache token
    │
    ▼
Main Loop (Every poll_interval_seconds)
    │
    ├─> Call Graph API: GET /me/messages?$filter=isRead eq false
    │
    ▼
For Each Unread Message
    │
    ├─> Extract message details (sender, subject, etc.)
    │
    ├─> Render template with variables
    │
    ├─> Collect attachment file paths
    │
    ├─> If attachments:
    │   ├─> Call: POST /me/messages/{id}/createReply
    │   ├─> Call: PATCH /me/messages/{id} (update body)
    │   ├─> For each file: POST /me/messages/{id}/attachments
    │   └─> Call: POST /me/messages/{id}/send
    │   
    ├─> Else:
    │   └─> Call: POST /me/messages/{id}/reply
    │
    ├─> Call: PATCH /me/messages/{id} (mark as read)
    │
    └─> Log results
```

## Security Model

### Authentication Security
- **Device Code Flow**: No client secrets stored
- **Token Caching**: Tokens stored locally in `token_cache.bin`
- **Token Refresh**: Automatic silent refresh
- **Delegated Permissions**: Acts on behalf of user

### Data Security
- Configuration files excluded from git
- Token cache excluded from git
- No hardcoded credentials
- HTTPS for all API communication

### Permission Scopes
- `Mail.ReadWrite` - Read and write access to user mail
- `Mail.Send` - Send mail as user
- Principle of least privilege

## Scalability Considerations

### Current Implementation
- Single-threaded processing
- Sequential message handling
- Suitable for: Personal use, small teams

### Potential Improvements
- Multi-threading for parallel processing
- Message queue for handling high volumes
- Database for tracking processed messages
- Webhook-based triggers instead of polling

## Error Handling

### Error Types Handled
1. **Authentication Errors**
   - Invalid client ID
   - Expired tokens
   - Permission denied

2. **API Errors**
   - Network failures
   - Rate limiting
   - Invalid requests

3. **File Errors**
   - Missing templates
   - Missing attachments
   - File read errors

4. **Configuration Errors**
   - Missing config file
   - Invalid JSON
   - Missing required fields

### Error Handling Strategy
- Try-catch blocks around API calls
- Graceful degradation (skip attachments if failed)
- User-friendly error messages
- Continue processing on non-fatal errors

## Configuration

### config.json Structure
```json
{
  "client_id": "string",           # Required: Azure AD app client ID
  "tenant_id": "string",           # Optional: Default "common"
  "scopes": ["string"],            # Optional: Default Mail permissions
  "reply_template": "string",      # Required: Path to HTML template
  "attachments_folder": "string",  # Required: Path to attachments
  "poll_interval_seconds": number, # Optional: Default 60
  "template_variables": {          # Optional: Template values
    "key": "value"
  }
}
```

## Dependencies

### Python Packages
- **msal** (>=1.24.0) - Microsoft Authentication Library
- **requests** (>=2.31.0) - HTTP client for Graph API
- **pywin32** (>=306) - Windows COM support (optional, Windows only)

### External Services
- **Microsoft Azure AD** - Authentication provider
- **Microsoft Graph API** - Email operations
- **Microsoft 365** - Mailbox hosting

## Deployment Options

### Local Development
```bash
python automail.py --once  # Test mode
```

### Continuous Service

#### Linux (systemd)
```bash
systemctl start automail
```

#### Windows (Task Scheduler)
Create scheduled task to run at startup

#### Docker (Future Enhancement)
```dockerfile
FROM python:3.9
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "automail.py"]
```

## Monitoring and Logging

### Current Logging
- Console output with timestamps
- Status messages for each operation
- Error messages with details

### Future Enhancements
- File-based logging
- Log rotation
- Structured logging (JSON)
- Integration with monitoring tools

## Testing Strategy

### Unit Tests (Potential)
- Template rendering
- Placeholder extraction
- Configuration loading

### Integration Tests (Potential)
- Mock Graph API responses
- End-to-end flow testing
- Error scenario testing

### Manual Testing
- Template rendering test (test_template.py)
- CLI interface verification
- Configuration validation

## Maintenance

### Regular Tasks
- Review and rotate credentials
- Update dependencies
- Monitor API usage and costs
- Review and update templates

### Monitoring Points
- Authentication success/failure rate
- Reply send success/failure rate
- Processing time per message
- API error rates

## Future Enhancements

### Potential Features
1. **Advanced Filtering**
   - Filter by sender domain
   - Filter by subject keywords
   - Time-based rules

2. **Multiple Templates**
   - Template selection based on rules
   - Per-sender templates

3. **Database Integration**
   - Track processed messages
   - Analytics and reporting
   - Audit trail

4. **Web Interface**
   - Configuration UI
   - Status dashboard
   - Log viewer

5. **Outlook COM Fallback**
   - Windows-only alternative
   - Local Outlook integration

6. **Advanced Attachments**
   - Dynamic attachment selection
   - Attachment templating
   - Cloud storage integration

## Conclusion

Automail is a robust, secure, and maintainable email automation system built on modern Python practices and Microsoft Graph API. The modular architecture allows for easy extension and customization while maintaining security and reliability.
