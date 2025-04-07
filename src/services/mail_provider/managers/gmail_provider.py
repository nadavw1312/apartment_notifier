from .mail_provider import MailProvider
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import os
import base64
import asyncio
from typing import Dict
import logging

class GmailProvider(MailProvider):
    def __init__(self, credentials_path: str = 'credentials.json'):
        self.SCOPES = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.modify'
        ]
        self.credentials_path = credentials_path
        self.creds = None
        self.service = None
        self.logger = logging.getLogger(__name__)
        self._setup_logging()

    def _setup_logging(self):
        self.logger.setLevel(logging.INFO)

    async def get_token(self) -> None:
        """Initial token setup - run this once to get your token"""
        try:
            if not os.path.exists(self.credentials_path):
                raise FileNotFoundError(
                    f"credentials.json not found at {self.credentials_path}. "
                    "Please download it from Google Cloud Console."
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path, 
                self.SCOPES
            )
            
            # This will open a browser window for authentication
            self.creds = flow.run_local_server(port=0)

            # Save the token for future use
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)
                self.logger.info("Token successfully saved to token.pickle")

        except Exception as e:
            self.logger.error(f"Failed to get token: {str(e)}")
            raise

    async def authenticate(self) -> None:
        """Handle Gmail authentication using saved token"""
        try:
            # Check for existing token
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    self.creds = pickle.load(token)
                    self.logger.info("Loaded existing token")

            # If no valid token exists, get a new one
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                    self.logger.info("Refreshed expired token")
                else:
                    await self.get_token()

            # Save the refreshed token
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)

            # Build the Gmail service
            self.service = build('gmail', 'v1', credentials=self.creds)
            self.logger.info("Successfully authenticated with Gmail")

        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            raise

    async def watch_inbox(self, query: str = "") -> None:
        """Monitor inbox for new emails matching the query"""
        last_history_id = None
        
        while True:
            try:
                results = await asyncio.to_thread(
                    self.service.users().messages().list(
                        userId='me',
                        q=query,
                        labelIds=['INBOX']
                    ).execute
                )

                messages = results.get('messages', [])

                if messages:
                    latest_message = messages[0]
                    if latest_message['id'] != last_history_id:
                        message_data = await self.process_message(latest_message['id'])
                        await self.handle_notification(message_data)
                        last_history_id = latest_message['id']

                await asyncio.sleep(10)  # Configurable polling interval

            except Exception as e:
                self.logger.error(f"Error in watch_inbox: {str(e)}")
                await asyncio.sleep(60)

    async def process_message(self, msg_id: str) -> Dict:
        """Process a single email message"""
        try:
            message = await asyncio.to_thread(
                self.service.users().messages().get(
                    userId='me', 
                    id=msg_id, 
                    format='full'
                ).execute
            )

            headers = message['payload']['headers']
            subject = next(h['value'] for h in headers if h['name'] == 'Subject')
            sender = next(h['value'] for h in headers if h['name'] == 'From')

            if 'parts' in message['payload']:
                parts = message['payload']['parts']
                data = parts[0]['body'].get('data', '')
            else:
                data = message['payload']['body'].get('data', '')

            content = base64.urlsafe_b64decode(data).decode() if data else ""

            return {
                'id': msg_id,
                'subject': subject,
                'sender': sender,
                'content': content
            }

        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            raise

    async def send_email(self, to: str, subject: str, body: str) -> None:
        """Send an email using Gmail"""
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode('utf-8')

            await asyncio.to_thread(
                self.service.users().messages().send(
                    userId='me',
                    body={'raw': raw_message}
                ).execute
            )
            
            self.logger.info(f"Email sent successfully to {to}")

        except Exception as e:
            self.logger.error(f"Failed to send email: {str(e)}")
            raise 