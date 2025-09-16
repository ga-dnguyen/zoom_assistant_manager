import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
import webbrowser
import threading
import time
import json
from urllib.parse import urlencode, parse_qs, urlparse
import socket
from datetime import datetime
import os
import sys
import base64


class ZoomAssistantManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Zoom Assistant Manager")
        self.root.geometry("800x700")
        
        # Try to load configuration from config.py
        self.load_config()
        
        # Zoom OAuth configuration
        self.base_url = "https://api.zoom.us/v2"
        
        self.access_token = None
        self.token_expires_at = None
        self.authenticated_email = None
        
        # Load cached token if available
        self.load_cached_token()
        
        self.create_widgets()
        
    def load_config(self):
        """Load configuration from config.py if it exists"""
        self.client_id = ""
        self.client_secret = ""
        
        try:
            # Add current directory to path to import config
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            
            import config
            self.client_id = getattr(config, 'CLIENT_ID', '')
            self.client_secret = getattr(config, 'CLIENT_SECRET', '')
            
            if self.client_id and self.client_secret:
                print("Configuration loaded from config.py")
        except ImportError:
            print("No config.py found, using manual configuration")
        except Exception as e:
            print(f"Error loading config: {e}")
            
    def load_cached_token(self):
        """Load cached access token if available and not expired"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            token_file = os.path.join(current_dir, ".token_cache.json")
            
            if os.path.exists(token_file):
                with open(token_file, 'r') as f:
                    token_data = json.load(f)
                
                expires_at = token_data.get('expires_at')
                if expires_at and time.time() < expires_at:
                    self.access_token = token_data.get('access_token')
                    self.token_expires_at = expires_at
                    self.authenticated_email = token_data.get('email')
                    print("Cached token loaded and is still valid")
                    # Update UI on startup
                    self.root.after(100, self.update_auth_status)
                else:
                    print("Cached token expired")
                    self.clear_cached_token()
        except Exception as e:
            print(f"Error loading cached token: {e}")
            
    def save_cached_token(self):
        """Save access token to cache file"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            token_file = os.path.join(current_dir, ".token_cache.json")
            
            token_data = {
                'access_token': self.access_token,
                'expires_at': self.token_expires_at,
                'email': self.authenticated_email
            }
            
            with open(token_file, 'w') as f:
                json.dump(token_data, f)
            print("Token cached successfully")
        except Exception as e:
            print(f"Error saving token cache: {e}")
            
    def clear_cached_token(self):
        """Clear cached token file"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            token_file = os.path.join(current_dir, ".token_cache.json")
            
            if os.path.exists(token_file):
                os.remove(token_file)
                print("Token cache cleared")
        except Exception as e:
            print(f"Error clearing token cache: {e}")
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Authentication section
        auth_frame = ttk.LabelFrame(main_frame, text="Authentication", padding="5")
        auth_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        auth_frame.columnconfigure(2, weight=1)
        
        self.auth_button = ttk.Button(auth_frame, text="Authenticate", command=self.authenticate)
        self.auth_button.grid(row=0, column=0, padx=(0, 10))
        
        self.configure_button = ttk.Button(auth_frame, text="Configure", command=self.show_config_modal)
        self.configure_button.grid(row=0, column=1, padx=(0, 10))
        
        self.auth_status_label = ttk.Label(auth_frame, text="Not authenticated", foreground="red")
        self.auth_status_label.grid(row=0, column=2, sticky=(tk.W,))
        
        # User input section
        input_frame = ttk.LabelFrame(main_frame, text="User Management", padding="5")
        input_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)
        
        ttk.Label(input_frame, text="Target User Email:").grid(row=0, column=0, sticky=(tk.W,), padx=(0, 5))
        self.target_user_entry = ttk.Entry(input_frame, width=40)
        self.target_user_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(input_frame, text="Assistant Emails (one per line):").grid(row=1, column=0, sticky=(tk.W, tk.N), padx=(0, 5))
        self.assistants_text = scrolledtext.ScrolledText(input_frame, width=40, height=6)
        self.assistants_text.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # Buttons frame
        buttons_frame = ttk.Frame(input_frame)
        buttons_frame.grid(row=2, column=1, sticky=(tk.E,), pady=(10, 0))
        
        # Assistants button
        self.assistants_button = ttk.Button(buttons_frame, text="Assistants", command=self.show_assistants, state="disabled")
        self.assistants_button.grid(row=0, column=0, padx=(0, 5))
        
        # Proceed button
        self.proceed_button = ttk.Button(buttons_frame, text="Proceed", command=self.process_assistants, state="disabled")
        self.proceed_button.grid(row=0, column=1)
        
        # Log section
        log_frame = ttk.LabelFrame(main_frame, text="Process Log", padding="5")
        log_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=70, height=15)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Clear log button
        ttk.Button(log_frame, text="Clear Log", command=self.clear_log).grid(row=1, column=0, sticky=(tk.E,), pady=(5, 0))
        
    def log_message(self, message):
        """Add a timestamped message to the log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def clear_log(self):
        """Clear the log text area"""
        self.log_text.delete(1.0, tk.END)
        
    def show_config_modal(self):
        """Show configuration modal for CLIENT_ID and CLIENT_SECRET"""
        # Create modal window
        config_window = tk.Toplevel(self.root)
        config_window.title("Configuration")
        config_window.geometry("400x200")
        config_window.transient(self.root)
        config_window.grab_set()
        
        # Center the window
        config_window.update_idletasks()
        x = (config_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (config_window.winfo_screenheight() // 2) - (200 // 2)
        config_window.geometry(f"400x200+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(config_window, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        config_window.columnconfigure(0, weight=1)
        config_window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # CLIENT_ID field
        ttk.Label(main_frame, text="Client ID:").grid(row=0, column=0, sticky=(tk.W,), padx=(0, 10), pady=(0, 10))
        client_id_entry = ttk.Entry(main_frame, width=30)
        client_id_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 10))
        client_id_entry.insert(0, self.client_id)
        
        # CLIENT_SECRET field
        ttk.Label(main_frame, text="Client Secret:").grid(row=1, column=0, sticky=(tk.W,), padx=(0, 10), pady=(0, 20))
        client_secret_entry = ttk.Entry(main_frame, width=30, show="*")
        client_secret_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 20))
        client_secret_entry.insert(0, self.client_secret)
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        def save_config():
            """Save configuration and close modal"""
            new_client_id = client_id_entry.get().strip()
            new_client_secret = client_secret_entry.get().strip()
            
            if not new_client_id or not new_client_secret:
                messagebox.showerror("Error", "Both Client ID and Client Secret are required")
                return
            
            if self.save_config_to_file(new_client_id, new_client_secret):
                self.client_id = new_client_id
                self.client_secret = new_client_secret
                self.log_message("Configuration saved successfully")
                config_window.destroy()
            else:
                messagebox.showerror("Error", "Failed to save configuration")
        
        def cancel_config():
            """Close modal without saving"""
            config_window.destroy()
        
        # Save button
        ttk.Button(buttons_frame, text="Save", command=save_config).grid(row=0, column=0, padx=(0, 10))
        
        # Cancel button
        ttk.Button(buttons_frame, text="Cancel", command=cancel_config).grid(row=0, column=1)
        
        # Focus on first field
        client_id_entry.focus()
        
    def save_config_to_file(self, client_id, client_secret):
        """Save CLIENT_ID and CLIENT_SECRET to config.py file"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_file_path = os.path.join(current_dir, "config.py")
            
            config_content = f"""# Zoom Assistant Manager Configuration Template
# Copy this file to config.py and fill in your actual values

# Zoom OAuth App Credentials
# Get these from your Zoom App in the Zoom Marketplace
CLIENT_ID = "{client_id}"
CLIENT_SECRET = "{client_secret}"

"""
            
            with open(config_file_path, 'w') as f:
                f.write(config_content)
            
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
        
    def authenticate(self):
        """Start the OAuth device flow authentication"""        
        if not self.client_id or not self.client_secret:
            messagebox.showerror("Error", "Please configure Client ID and Client Secret using the Configure button")
            return
            
        self.log_message("Starting OAuth device flow authentication...")
        threading.Thread(target=self.device_flow_auth, daemon=True).start()
        
    def device_flow_auth(self):
        """Perform OAuth device flow authentication"""
        try:
            # Step 1: Get device code
            device_auth_url = f"https://zoom.us/oauth/devicecode?client_id={self.client_id}"
            
            # Create basic authorization header
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
            headers = {
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            self.log_message("Requesting device code...")
            response = requests.post(device_auth_url, headers=headers)
            
            if response.status_code != 200:
                self.log_message(f"Error getting device code: {response.text}")
                return
                
            device_info = response.json()
            device_code = device_info["device_code"]
            user_code = device_info["user_code"]
            verification_uri = device_info["verification_uri"]
            interval = device_info.get("interval", 5)
            
            self.log_message(f"Device code obtained. User code: {user_code}")
            self.log_message(f"Opening browser to: {verification_uri}")
            
            # Open browser for user to enter code
            webbrowser.open(verification_uri)
            
            # Step 2: Poll for access token
            token_url = "https://zoom.us/oauth/token"
            token_data = {
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": device_code,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            
            self.log_message("Waiting for user authorization...")
            
            # Poll for token
            max_attempts = 60  # 5 minutes max
            for attempt in range(max_attempts):
                time.sleep(interval)
                
                token_response = requests.post(token_url, data=token_data)
                token_result = token_response.json()
                
                if token_response.status_code == 200:
                    self.access_token = token_result["access_token"]
                    
                    # Calculate token expiration time
                    expires_in = token_result.get("expires_in", 3600)  # Default 1 hour
                    self.token_expires_at = time.time() + expires_in
                    
                    self.log_message("Authentication successful!")
                    
                    # Get user info
                    self.get_user_info()
                    
                    # Save token to cache
                    self.save_cached_token()
                    break
                elif token_result.get("error") == "authorization_pending":
                    self.log_message(f"Waiting for authorization... (attempt {attempt + 1}/{max_attempts})")
                elif token_result.get("error") == "slow_down":
                    interval += 5
                    self.log_message("Slowing down polling...")
                else:
                    self.log_message(f"Authentication failed: {token_result.get('error_description', 'Unknown error')}")
                    break
            else:
                self.log_message("Authentication timed out")
                
        except Exception as e:
            self.log_message(f"Authentication error: {str(e)}")
            
    def get_user_info(self):
        """Get authenticated user information"""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(f"{self.base_url}/users/me", headers=headers)
            
            if response.status_code == 200:
                user_info = response.json()
                self.authenticated_email = user_info.get("email", "Unknown")
                
                # Update UI on main thread
                self.root.after(0, self.update_auth_status)
                self.log_message(f"Authenticated as: {self.authenticated_email}")
            else:
                self.log_message(f"Failed to get user info: {response.text}")
                
        except Exception as e:
            self.log_message(f"Error getting user info: {str(e)}")
            
    def update_auth_status(self):
        """Update authentication status in UI"""
        if self.authenticated_email and self.token_expires_at:
            # Format expiration time
            expires_datetime = datetime.fromtimestamp(self.token_expires_at)
            expires_str = expires_datetime.strftime("%Y-%m-%d %H:%M:%S")
            
            # Check if token is about to expire (within 30 minutes)
            time_remaining = self.token_expires_at - time.time()
            if time_remaining < 1800:  # 30 minutes
                status_text = f"Authenticated as: {self.authenticated_email} (expires: {expires_str}) ⚠️"
                color = "orange"
            else:
                status_text = f"Authenticated as: {self.authenticated_email} (expires: {expires_str})"
                color = "green"
                
            self.auth_status_label.config(text=status_text, foreground=color)
            self.proceed_button.config(state="normal")
            self.assistants_button.config(state="normal")
        elif self.authenticated_email:
            self.auth_status_label.config(text=f"Authenticated as: {self.authenticated_email}", foreground="green")
            self.proceed_button.config(state="normal")
            self.assistants_button.config(state="normal")
        else:
            self.auth_status_label.config(text="Not authenticated", foreground="red")
            self.proceed_button.config(state="disabled")
            self.assistants_button.config(state="disabled")
            
    def is_token_valid(self):
        """Check if the current token is valid and not expired"""
        if not self.access_token:
            return False
        if self.token_expires_at and time.time() >= self.token_expires_at:
            self.log_message("Token has expired, please re-authenticate")
            self.clear_cached_token()
            self.access_token = None
            self.token_expires_at = None
            self.authenticated_email = None
            self.update_auth_status()
            return False
        return True
            
    def show_assistants(self):
        """Show all assistants of the target user"""
        if not self.is_token_valid():
            messagebox.showerror("Error", "Please authenticate first")
            return
            
        target_email = self.target_user_entry.get().strip()
        if not target_email:
            messagebox.showerror("Error", "Please enter target user email")
            return
            
        self.log_message(f"Fetching assistants for: {target_email}")
        
        # Run in separate thread to avoid blocking UI
        threading.Thread(target=self.fetch_assistants, args=(target_email,), daemon=True).start()
        
    def fetch_assistants(self, target_email):
        """Fetch and display assistants for the target user"""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Get target user ID
            target_user_id = self.get_user_id_by_email(target_email, headers)
            if not target_user_id:
                self.log_message(f"Failed to get user ID for {target_email}")
                return
                
            # Get assistants for the user
            response = requests.get(f"{self.base_url}/users/{target_user_id}/assistants", headers=headers)
            
            if response.status_code == 200:
                assistants_data = response.json()
                assistants = assistants_data.get("assistants", [])
                
                if assistants:
                    self.log_message(f"Assistants for {target_email}:")
                    for i, assistant in enumerate(assistants, 1):
                        email = assistant.get("email", "N/A")
                        self.log_message(f"  {i}. {email}")
                else:
                    self.log_message(f"No assistants found for {target_email}")
            else:
                self.log_message(f"Failed to get assistants for {target_email}: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_message(f"Error fetching assistants: {str(e)}")
            
    def process_assistants(self):
        """Process adding assistants to users"""
        if not self.is_token_valid():
            messagebox.showerror("Error", "Please authenticate first")
            return
            
        target_email = self.target_user_entry.get().strip()
        assistants_text = self.assistants_text.get(1.0, tk.END).strip()
        
        if not target_email or not assistants_text:
            messagebox.showerror("Error", "Please enter both target user email and assistant emails")
            return
            
        assistant_emails = [email.strip() for email in assistants_text.split('\n') if email.strip()]
        
        if not assistant_emails:
            messagebox.showerror("Error", "Please enter at least one assistant email")
            return
            
        self.log_message(f"Starting process for target user: {target_email}")
        self.log_message(f"Assistant emails: {', '.join(assistant_emails)}")
        
        # Run in separate thread to avoid blocking UI
        threading.Thread(target=self.execute_assistant_management, 
                        args=(target_email, assistant_emails), daemon=True).start()
        
    def execute_assistant_management(self, target_email, assistant_emails):
        """Execute the assistant management process"""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Get target user ID
            target_user_id = self.get_user_id_by_email(target_email, headers)
            if not target_user_id:
                self.log_message(f"Failed to get user ID for {target_email}")
                return
                
            # Validate assistant emails exist (optional check)
            valid_assistant_emails = []
            for email in assistant_emails:
                user_id = self.get_user_id_by_email(email, headers)
                if user_id:
                    valid_assistant_emails.append(email)
                else:
                    self.log_message(f"Warning: Assistant email not found: {email}")
                    
            if not valid_assistant_emails:
                self.log_message("No valid assistant emails found")
                return
                
            # Step 1: Add all assistants to target user
            self.log_message(f"Step 1: Adding assistants to {target_email}")
            for email in valid_assistant_emails:
                try:
                    self.add_assistant(target_user_id, email, headers)
                    self.log_message(f"✓ Successfully added {email} as assistant to {target_email}")
                except Exception as e:
                    self.log_message(f"✗ Failed to add {email} as assistant to {target_email}: {str(e)}")
                    
            # Step 2: Add target user as assistant to each assistant user
            self.log_message(f"Step 2: Adding {target_email} as assistant to other users")
            for email in valid_assistant_emails:
                try:
                    # Get assistant user ID for this step
                    assistant_user_id = self.get_user_id_by_email(email, headers)
                    if assistant_user_id:
                        self.add_assistant(assistant_user_id, target_email, headers)
                        self.log_message(f"✓ Successfully added {target_email} as assistant to {email}")
                    else:
                        self.log_message(f"✗ Failed to get user ID for {email}")
                except Exception as e:
                    self.log_message(f"✗ Failed to add {target_email} as assistant to {email}: {str(e)}")
                    
            self.log_message("Process completed!")
            
        except Exception as e:
            self.log_message(f"Process error: {str(e)}")
            
    def get_user_id_by_email(self, email, headers):
        """Get user ID by email address"""
        try:
            response = requests.get(f"{self.base_url}/users/{email}", headers=headers)
            if response.status_code == 200:
                user_info = response.json()
                return user_info.get("id")
            else:
                self.log_message(f"User not found: {email} (Status: {response.status_code})")
                return None
        except Exception as e:
            self.log_message(f"Error getting user ID for {email}: {str(e)}")
            return None
            
    def add_assistant(self, user_id, assistant_email, headers):
        """Add an assistant to a user"""
        url = f"{self.base_url}/users/{user_id}/assistants"
        data = {
            "assistants": [
                {
                    "email": assistant_email
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code not in [200, 201, 204]:
            raise Exception(f"API error: {response.status_code} - {response.text}")


def main():
    root = tk.Tk()
    app = ZoomAssistantManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()
