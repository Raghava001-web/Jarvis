"""
Email Handler - Read, summarize, and SEND emails
Uses Gmail API for reading, SMTP for sending
"""

import os
import json
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime

# Gmail imports
GMAIL_AVAILABLE = False
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GMAIL_AVAILABLE = True
except ImportError:
    print("[EMAIL] Gmail libraries not installed.")
    print("        Install: pip install google-auth google-auth-oauthlib google-api-python-client")


class EmailHandler:
    """Gmail integration for JARVIS - read AND send emails"""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    def __init__(self, perception, knowledge=None):
        print("[EMAIL] Initializing Email Handler...")
        self.perception = perception
        self.knowledge = knowledge  # For LLM summarization
        self.service = None
        self.available = GMAIL_AVAILABLE
        self._authenticated = False  # Lazy auth flag
        
        # SMTP config for sending emails
        self.smtp_email = os.getenv("JARVIS_EMAIL", "jarvisaif0009@gmail.com")
        self.smtp_password = os.getenv("JARVIS_EMAIL_PASSWORD", "")
        self.user_email = os.getenv("USER_EMAIL", "")
        self.smtp_available = bool(self.smtp_password)
        
        if self.smtp_available:
            print(f"[EMAIL] SMTP sending enabled via {self.smtp_email}")
        else:
            print("[EMAIL] SMTP sending disabled (set JARVIS_EMAIL_PASSWORD in .env)")
        
        print("[EMAIL] Handler Ready (auth deferred)")
    
    def _authenticate(self):
        """Authenticate with Gmail - JSON and threaded OAuth"""
        creds = None
        
        data_dir = Path(__file__).parent.parent.parent / "jarvis_data"
        data_dir.mkdir(exist_ok=True)
        
        token_path = data_dir / "gmail_token.json"
        credentials_path = data_dir / "gmail_credentials.json"
        
        if token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(token_path), self.SCOPES)
            except:
                pass
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except:
                    creds = None
            
            if not creds:
                if credentials_path.exists() and not getattr(self, "_oauth_running", False):
                    self._oauth_running = True
                    print("[EMAIL] Launching OAuth browser auth in background...")
                    def _run_oauth():
                        try:
                            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), self.SCOPES)
                            new_creds = flow.run_local_server(port=0)
                            with open(token_path, 'w') as token:
                                token.write(new_creds.to_json())
                            self.service = build('gmail', 'v1', credentials=new_creds)
                            self._authenticated = True
                            print("[EMAIL] Authenticated successfully via browser")
                        except Exception as e:
                            print(f"[EMAIL] Auth error: {e}")
                            self.available = False
                        finally:
                            self._oauth_running = False
                    import threading
                    threading.Thread(target=_run_oauth, daemon=True).start()
                    # Return immediately without blocking
                    return
                else:
                    if not getattr(self, "_oauth_running", False):
                        print("[EMAIL] No credentials file found at:", credentials_path)
                        self.available = False
                    return
            
            # Save refreshed creds
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        if creds and creds.valid:
            try:
                self.service = build('gmail', 'v1', credentials=creds)
                self._authenticated = True
                print("[EMAIL] Authenticated successfully")
            except Exception as e:
                print(f"[EMAIL] Service build error: {e}")
                self.available = False
    
    def _ensure_authenticated(self):
        """Lazy authentication - only authenticate when first needed"""
        if not self._authenticated and self.available:
            print("[EMAIL] First email access - authenticating...")
            self._authenticate()
        return self.available and self.service is not None
    
    def get_unread_emails(self, max_results=5):
        """Get unread emails"""
        title = getattr(self.perception, 'user_title', 'sir')
        
        # Lazy authentication on first use
        if not self._ensure_authenticated():
            return f"Email is not connected, {title}. Please set up Gmail credentials."
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                labelIds=['INBOX', 'UNREAD'],
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                return f"No unread emails, {title}."
            
            email_list = []
            for msg in messages:
                msg_data = self.service.users().messages().get(
                    userId='me', id=msg['id'], format='metadata',
                    metadataHeaders=['From', 'Subject']
                ).execute()
                
                headers = msg_data.get('payload', {}).get('headers', [])
                sender = ""
                subject = ""
                
                for header in headers:
                    if header['name'] == 'From':
                        sender = header['value'].split('<')[0].strip()
                    elif header['name'] == 'Subject':
                        subject = header['value']
                
                if len(subject) > 50:
                    subject = subject[:50] + "..."
                
                email_list.append(f"From {sender}: {subject}")
            
            return f"You have {len(messages)} unread emails, {title}. " + ". ".join(email_list)
            
        except Exception as e:
            print(f"[EMAIL] Error: {e}")
            return f"Error reading emails, {title}."
    
    def summarize_emails(self, count=3):
        """Summarize unread emails using LLM"""
        title = getattr(self.perception, 'user_title', 'sir')
        
        if not self._ensure_authenticated():
            return f"Email is not connected, {title}."
        
        if not self.knowledge or not self.knowledge.enabled:
            return self.get_unread_emails(count)
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                labelIds=['INBOX', 'UNREAD'],
                maxResults=count
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                return f"No unread emails to summarize, {title}."
            
            email_summaries = []
            for msg in messages:
                msg_data = self.service.users().messages().get(
                    userId='me', id=msg['id'], format='full'
                ).execute()
                
                headers = msg_data.get('payload', {}).get('headers', [])
                sender = ""
                subject = ""
                
                for header in headers:
                    if header['name'] == 'From':
                        sender = header['value'].split('<')[0].strip()
                    elif header['name'] == 'Subject':
                        subject = header['value']
                
                snippet = msg_data.get('snippet', '')
                email_summaries.append(f"From: {sender}\nSubject: {subject}\nPreview: {snippet}")
            
            prompt = f"Summarize these {len(email_summaries)} emails in one brief paragraph:\n\n" + "\n\n".join(email_summaries)
            summary = self.knowledge.answer_question(prompt)
            
            return f"Email summary, {title}: {summary}"
            
        except Exception as e:
            print(f"[EMAIL] Error: {e}")
            return f"Error summarizing emails, {title}."
    
    # ═══════════════════════════════════════════════════════════════
    # SEND EMAIL via SMTP
    # ═══════════════════════════════════════════════════════════════
    
    def send_email(self, to_email: str, subject: str, body: str) -> str:
        """Send an email via SMTP (Gmail)"""
        title = getattr(self.perception, 'user_title', 'sir')
        
        if not self.smtp_available:
            return f"Email sending is not configured, {title}. Set JARVIS_EMAIL_PASSWORD in .env."
        
        try:
            msg = MIMEMultipart()
            msg['From'] = f"JARVIS <{self.smtp_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            if not getattr(self, "_smtp_conn", None):
                self._smtp_conn = smtplib.SMTP('smtp.gmail.com', 587)
                self._smtp_conn.starttls()
                self._smtp_conn.login(self.smtp_email, self.smtp_password)
            try:
                self._smtp_conn.send_message(msg)
            except Exception as e:
                # Connection dropped? Reconnect.
                self._smtp_conn = smtplib.SMTP('smtp.gmail.com', 587)
                self._smtp_conn.starttls()
                self._smtp_conn.login(self.smtp_email, self.smtp_password)
                self._smtp_conn.send_message(msg)
            
            print(f"[EMAIL] Sent email to {to_email}: {subject}")
            return f"Email sent to {to_email}, {title}."
            
        except Exception as e:
            print(f"[EMAIL] Send error: {e}")
            return f"Failed to send email, {title}. Error: {str(e)[:60]}"
    
    def send_reminder_email(self, reminder_text: str) -> str:
        """Send a proactive reminder email to the user"""
        title = getattr(self.perception, 'user_title', 'sir')
        
        if not self.user_email:
            print("[EMAIL] No USER_EMAIL configured, skipping reminder email")
            return ""
        
        now = datetime.now().strftime('%I:%M %p, %B %d')
        subject = f"JARVIS Reminder - {now}"
        body = f"""Hello {title},

This is your AI assistant JARVIS with a reminder:

{reminder_text}

---
Sent automatically by JARVIS at {now}
"""
        return self.send_email(self.user_email, subject, body)

