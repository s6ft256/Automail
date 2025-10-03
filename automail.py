#!/usr/bin/env python3
"""
Automail - Automatic Email Reply System
Main application script
"""
import json
import os
import sys
import time
from datetime import datetime
from graph_auth import GraphAuthenticator
from email_handler import EmailHandler
from template_engine import TemplateEngine


class Automail:
    """Main application class for automatic email replies"""
    
    def __init__(self, config_path="config.json"):
        """
        Initialize Automail application
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.template_engine = None
        self.email_handler = None
        self.access_token = None
        self.processed_messages = set()
    
    def _load_config(self, config_path):
        """
        Load configuration from file
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            dict: Configuration dictionary
        """
        if not os.path.exists(config_path):
            print(f"Configuration file not found: {config_path}")
            print("Please copy config.example.json to config.json and update with your settings.")
            sys.exit(1)
        
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def _authenticate(self):
        """Authenticate with Microsoft Graph API"""
        print("Authenticating with Microsoft Graph API...")
        
        authenticator = GraphAuthenticator(
            client_id=self.config["client_id"],
            tenant_id=self.config.get("tenant_id", "common"),
            scopes=self.config.get("scopes", ["Mail.ReadWrite", "Mail.Send"])
        )
        
        self.access_token = authenticator.get_access_token()
        
        if not self.access_token:
            print("Failed to authenticate. Exiting.")
            sys.exit(1)
        
        self.email_handler = EmailHandler(self.access_token)
        print("Authentication successful!\n")
    
    def _initialize_template(self):
        """Initialize template engine"""
        template_path = self.config.get("reply_template", "reply_template.html")
        
        if not os.path.exists(template_path):
            print(f"Template file not found: {template_path}")
            sys.exit(1)
        
        self.template_engine = TemplateEngine(template_path)
        
        # Display template info
        placeholders = self.template_engine.get_placeholders()
        print(f"Template loaded: {template_path}")
        print(f"Placeholders found: {', '.join(placeholders) if placeholders else 'None'}\n")
    
    def _get_attachments(self):
        """
        Get list of attachment file paths
        
        Returns:
            list: List of absolute paths to attachment files
        """
        attachments_folder = self.config.get("attachments_folder", "attachments")
        
        if not os.path.exists(attachments_folder):
            return []
        
        attachments = []
        for filename in os.listdir(attachments_folder):
            file_path = os.path.join(attachments_folder, filename)
            
            # Skip directories and README files
            if os.path.isfile(file_path) and filename.lower() != "readme.txt":
                attachments.append(os.path.abspath(file_path))
        
        return attachments
    
    def _process_message(self, message):
        """
        Process a single message and send auto-reply
        
        Args:
            message: Message object from Graph API
            
        Returns:
            bool: True if message was processed successfully
        """
        message_id = message["id"]
        
        # Skip if already processed in this session
        if message_id in self.processed_messages:
            return False
        
        subject = message.get("subject", "(No Subject)")
        sender = message.get("from", {}).get("emailAddress", {}).get("address", "Unknown")
        received = message.get("receivedDateTime", "")
        
        print(f"\n{'='*60}")
        print(f"Processing message:")
        print(f"  From: {sender}")
        print(f"  Subject: {subject}")
        print(f"  Received: {received}")
        print(f"{'='*60}")
        
        # Render template with variables
        template_vars = self.config.get("template_variables", {})
        reply_body = self.template_engine.render(template_vars)
        
        # Get attachments
        attachments = self._get_attachments()
        
        if attachments:
            print(f"Attachments to include: {len(attachments)}")
            for att in attachments:
                print(f"  - {os.path.basename(att)}")
        
        # Send reply
        print("Sending auto-reply...")
        success = self.email_handler.send_reply(message_id, reply_body, attachments)
        
        if success:
            print("✓ Reply sent successfully!")
            
            # Mark as read
            if self.email_handler.mark_as_read(message_id):
                print("✓ Message marked as read")
            
            self.processed_messages.add(message_id)
            return True
        else:
            print("✗ Failed to send reply")
            return False
    
    def run_once(self):
        """Process unread emails once"""
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking for unread messages...")
        
        messages = self.email_handler.get_unread_messages()
        
        if not messages:
            print("No unread messages found.")
            return
        
        print(f"Found {len(messages)} unread message(s)")
        
        for message in messages:
            self._process_message(message)
    
    def run_continuous(self):
        """Run continuously, checking for new emails at regular intervals"""
        poll_interval = self.config.get("poll_interval_seconds", 60)
        
        print("\n" + "="*60)
        print("AUTOMAIL - Automatic Email Reply Service")
        print("="*60)
        print(f"Polling interval: {poll_interval} seconds")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                self.run_once()
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            print("\n\nShutting down gracefully...")
            print("Goodbye!")
    
    def start(self, continuous=True):
        """
        Start the Automail application
        
        Args:
            continuous: If True, run continuously; if False, run once
        """
        self._authenticate()
        self._initialize_template()
        
        if continuous:
            self.run_continuous()
        else:
            self.run_once()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Automail - Automatic Email Reply System"
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to configuration file (default: config.json)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process emails once and exit (default: run continuously)"
    )
    
    args = parser.parse_args()
    
    app = Automail(config_path=args.config)
    app.start(continuous=not args.once)


if __name__ == "__main__":
    main()
