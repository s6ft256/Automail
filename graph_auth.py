"""
Microsoft Graph API Authentication Module
Handles authentication using device code flow
"""
import json
import msal
import os


class GraphAuthenticator:
    """Handles Microsoft Graph API authentication"""
    
    def __init__(self, client_id, tenant_id="common", scopes=None):
        """
        Initialize the authenticator
        
        Args:
            client_id: Azure AD application client ID
            tenant_id: Azure AD tenant ID (default: "common")
            scopes: List of permission scopes required
        """
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.scopes = scopes or ["Mail.ReadWrite", "Mail.Send"]
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.token_cache_file = "token_cache.bin"
        
        # Initialize MSAL app with token cache
        self.cache = msal.SerializableTokenCache()
        if os.path.exists(self.token_cache_file):
            with open(self.token_cache_file, 'r') as f:
                self.cache.deserialize(f.read())
        
        self.app = msal.PublicClientApplication(
            client_id=self.client_id,
            authority=self.authority,
            token_cache=self.cache
        )
    
    def _save_cache(self):
        """Save token cache to file"""
        if self.cache.has_state_changed:
            with open(self.token_cache_file, 'w') as f:
                f.write(self.cache.serialize())
    
    def get_access_token(self):
        """
        Get access token using device code flow
        
        Returns:
            str: Access token or None if authentication fails
        """
        # Try to get token from cache first
        accounts = self.app.get_accounts()
        if accounts:
            result = self.app.acquire_token_silent(self.scopes, account=accounts[0])
            if result and "access_token" in result:
                return result["access_token"]
        
        # If no cached token, use device code flow
        flow = self.app.initiate_device_flow(scopes=self.scopes)
        
        if "user_code" not in flow:
            raise ValueError("Failed to create device flow. Error: " + 
                           json.dumps(flow, indent=2))
        
        print("\n" + "="*60)
        print("AUTHENTICATION REQUIRED")
        print("="*60)
        print(flow["message"])
        print("="*60 + "\n")
        
        # Wait for user to authenticate
        result = self.app.acquire_token_by_device_flow(flow)
        
        if "access_token" in result:
            self._save_cache()
            print("Authentication successful!")
            return result["access_token"]
        else:
            error = result.get("error")
            error_desc = result.get("error_description")
            print(f"Authentication failed: {error} - {error_desc}")
            return None
