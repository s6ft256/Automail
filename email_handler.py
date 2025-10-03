"""
Email Handler Module
Handles email monitoring and auto-reply functionality
"""
import requests
import os
import base64
import mimetypes
from datetime import datetime, timezone


class EmailHandler:
    """Handles email operations using Microsoft Graph API"""
    
    def __init__(self, access_token):
        """
        Initialize email handler
        
        Args:
            access_token: Microsoft Graph API access token
        """
        self.access_token = access_token
        self.graph_endpoint = "https://graph.microsoft.com/v1.0"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def get_unread_messages(self, max_results=10):
        """
        Get unread messages from inbox
        
        Args:
            max_results: Maximum number of messages to retrieve
            
        Returns:
            list: List of unread message objects
        """
        url = f"{self.graph_endpoint}/me/messages"
        params = {
            "$filter": "isRead eq false",
            "$top": max_results,
            "$select": "id,subject,from,receivedDateTime,isRead"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json().get("value", [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching messages: {e}")
            return []
    
    def send_reply(self, message_id, reply_body, attachments=None):
        """
        Send a reply to a message
        
        Args:
            message_id: ID of the message to reply to
            reply_body: HTML content of the reply
            attachments: List of file paths to attach
            
        Returns:
            bool: True if reply was sent successfully
        """
        url = f"{self.graph_endpoint}/me/messages/{message_id}/reply"
        
        # Prepare reply payload
        payload = {
            "message": {
                "body": {
                    "contentType": "HTML",
                    "content": reply_body
                }
            },
            "comment": reply_body
        }
        
        # If attachments are provided, use createReply and send separately
        if attachments:
            return self._send_reply_with_attachments(message_id, reply_body, attachments)
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error sending reply: {e}")
            return False
    
    def _send_reply_with_attachments(self, message_id, reply_body, attachments):
        """
        Send a reply with attachments (requires creating draft first)
        
        Args:
            message_id: ID of the message to reply to
            reply_body: HTML content of the reply
            attachments: List of file paths to attach
            
        Returns:
            bool: True if reply was sent successfully
        """
        # Step 1: Create a reply draft
        create_reply_url = f"{self.graph_endpoint}/me/messages/{message_id}/createReply"
        
        try:
            response = requests.post(create_reply_url, headers=self.headers)
            response.raise_for_status()
            draft = response.json()
            draft_id = draft["id"]
        except requests.exceptions.RequestException as e:
            print(f"Error creating reply draft: {e}")
            return False
        
        # Step 2: Update the draft body
        update_url = f"{self.graph_endpoint}/me/messages/{draft_id}"
        update_payload = {
            "body": {
                "contentType": "HTML",
                "content": reply_body
            }
        }
        
        try:
            response = requests.patch(update_url, headers=self.headers, json=update_payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error updating draft body: {e}")
            return False
        
        # Step 3: Add attachments
        for file_path in attachments:
            if not os.path.exists(file_path):
                print(f"Warning: Attachment file not found: {file_path}")
                continue
            
            if not self._add_attachment(draft_id, file_path):
                print(f"Warning: Failed to attach file: {file_path}")
        
        # Step 4: Send the draft
        send_url = f"{self.graph_endpoint}/me/messages/{draft_id}/send"
        
        try:
            response = requests.post(send_url, headers=self.headers)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error sending draft: {e}")
            return False
    
    def _add_attachment(self, message_id, file_path):
        """
        Add an attachment to a message
        
        Args:
            message_id: ID of the message
            file_path: Path to the file to attach
            
        Returns:
            bool: True if attachment was added successfully
        """
        url = f"{self.graph_endpoint}/me/messages/{message_id}/attachments"
        
        # Read file content
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
        except IOError as e:
            print(f"Error reading file {file_path}: {e}")
            return False
        
        # Encode file content as base64
        file_content_base64 = base64.b64encode(file_content).decode('utf-8')
        
        # Get file name and mime type
        file_name = os.path.basename(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        mime_type = mime_type or "application/octet-stream"
        
        # Prepare attachment payload
        attachment_payload = {
            "@odata.type": "#microsoft.graph.fileAttachment",
            "name": file_name,
            "contentType": mime_type,
            "contentBytes": file_content_base64
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=attachment_payload)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error adding attachment: {e}")
            return False
    
    def mark_as_read(self, message_id):
        """
        Mark a message as read
        
        Args:
            message_id: ID of the message to mark as read
            
        Returns:
            bool: True if message was marked as read successfully
        """
        url = f"{self.graph_endpoint}/me/messages/{message_id}"
        payload = {"isRead": True}
        
        try:
            response = requests.patch(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error marking message as read: {e}")
            return False
