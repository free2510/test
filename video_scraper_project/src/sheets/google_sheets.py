# -*- coding: utf-8 -*-
"""
Google Sheets manager module for real-time updates.
"""

import time
import logging
from typing import Optional, Dict, Any, List
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config.settings import (
    GOOGLE_SHEET_ID,
    GOOGLE_SCOPES,
    TOKEN_PATH,
    CREDENTIALS_PATH,
    SHEET_HEADERS,
    SHEET_RANGE,
    MAX_RETRIES,
    RETRY_DELAY,
)
from src.utils.helpers import setup_logging


class GoogleSheetsManager:
    """
    Manager class for Google Sheets operations.
    
    This class handles:
    - Authentication with Google API
    - Initializing sheet with headers
    - Real-time row updates and inserts
    - Checking for existing video entries
    """
    
    def __init__(self, sheet_id: str = None):
        """
        Initialize the Google Sheets manager.
        
        Args:
            sheet_id: Google Sheet ID
        """
        self.sheet_id = sheet_id or GOOGLE_SHEET_ID
        self.logger = setup_logging(self.__class__.__name__)
        
        # Google API services
        self.creds = None
        self.service = None
        self.sheet = None
        self.drive_service = None
        
        # Track which videos we've already created rows for in this session
        self.session_processed_rows: set = set()
    
    def authenticate(self) -> bool:
        """
        Authenticate with Google API.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Load credentials from token file if exists
            if TOKEN_PATH and hasattr(TOKEN_PATH, 'exists'):
                from pathlib import Path
                if Path(TOKEN_PATH).exists():
                    self.creds = Credentials.from_authorized_user_file(TOKEN_PATH, GOOGLE_SCOPES)
            
            # Refresh or get new credentials
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    # For Google Colab
                    try:
                        from google.colab import auth
                        auth.authenticate_user()
                        if TOKEN_PATH and hasattr(TOKEN_PATH, 'exists'):
                            from pathlib import Path
                            if Path(TOKEN_PATH).exists():
                                self.creds = Credentials.from_authorized_user_file(TOKEN_PATH, GOOGLE_SCOPES)
                    except ImportError:
                        # Not in Colab - use standard OAuth flow
                        if CREDENTIALS_PATH and hasattr(CREDENTIALS_PATH, 'exists'):
                            from pathlib import Path
                            if Path(CREDENTIALS_PATH).exists():
                                flow = InstalledAppFlow.from_client_secrets_file(
                                    CREDENTIALS_PATH, GOOGLE_SCOPES
                                )
                                self.creds = flow.run_local_server(port=0)
            
            if not self.creds or not self.creds.valid:
                self.logger.error("Could not obtain valid credentials")
                return False
            
            # Build services
            self.service = build('sheets', 'v4', credentials=self.creds)
            self.sheet = self.service.spreadsheets()
            self.drive_service = build('drive', 'v3', credentials=self.creds)
            
            self.logger.info("Google Sheets + Drive connected")
            return True
            
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False
    
    def init_sheet(self) -> bool:
        """
        Initialize Google Sheet with headers if needed.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.service:
                if not self.authenticate():
                    return False
            
            # Check if sheet has headers
            result = self.sheet.values().get(
                spreadsheetId=self.sheet_id, 
                range='Sheet1!A1:Z1'
            ).execute()
            values = result.get('values', [])
            
            if not values or not values[0]:
                # Add headers
                headers = [SHEET_HEADERS]
                self.sheet.values().update(
                    spreadsheetId=self.sheet_id,
                    range='Sheet1!A1:I1',
                    valueInputOption='RAW',
                    body={'values': headers}
                ).execute()
                self.logger.info("Sheet headers added")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Sheet init error: {e}")
            return False
    
    def get_existing_video_row(self, video_id: str) -> Optional[int]:
        """
        Check if video already exists in sheet and return row number.
        
        Args:
            video_id: Video ID to search for
        
        Returns:
            Row number if found, None otherwise
        """
        try:
            if not self.service:
                if not self.authenticate():
                    return None
            
            # Get all data from sheet
            result = self.sheet.values().get(
                spreadsheetId=self.sheet_id,
                range='Sheet1!A:I'
            ).execute()
            
            values = result.get('values', [])
            
            # Skip header row (index 0), start from row 2 (index 1)
            for idx, row in enumerate(values[1:], start=2):
                if len(row) >= 3 and row[2] == video_id:  # Column C is Video ID
                    return idx
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking existing row: {e}")
            return None
    
    def update_sheet_realtime(self, video_data: Dict[str, Any], 
                              status: str = "Processing",
                              is_final: bool = False) -> bool:
        """
        Update Google Sheet IMMEDIATELY after each video.
        Updates existing row or creates new one.
        
        Args:
            video_data: Dictionary containing video information
            status: Status message to display
            is_final: Whether this is the final update for this video
        
        Returns:
            True if successful, False otherwise
        """
        for attempt in range(MAX_RETRIES):
            try:
                if not self.service:
                    if not self.authenticate():
                        return False
                
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                video_id = video_data.get('video_id', '')
                
                # Check if this video already has a row in the sheet
                existing_row = self.get_existing_video_row(video_id)
                
                row_data = [
                    timestamp,
                    video_data.get('title', ''),
                    video_data.get('video_id', ''),
                    video_data.get('watch_link', ''),
                    video_data.get('series_name', ''),
                    video_data.get('category', ''),
                    video_data.get('dood_watch', ''),
                    video_data.get('dood_download', ''),
                    status
                ]
                
                if existing_row:
                    # Update existing row instead of creating duplicate
                    range_name = f'Sheet1!A{existing_row}:I{existing_row}'
                    self.sheet.values().update(
                        spreadsheetId=self.sheet_id,
                        range=range_name,
                        valueInputOption='RAW',
                        body={'values': [row_data]}
                    ).execute()
                    self.logger.info(f"REAL-TIME UPDATE: Row {existing_row} updated")
                else:
                    # Only add new row for initial or final status
                    # Don't create duplicate rows for intermediate statuses
                    if status != "⏳ Starting" and status != "✅ Success" and not status.startswith("❌"):
                        return True
                    
                    self.sheet.values().append(
                        spreadsheetId=self.sheet_id,
                        range='Sheet1!A:I',
                        valueInputOption='RAW',
                        insertDataOption='INSERT_ROWS',
                        body={'values': [row_data]}
                    ).execute()
                    self.logger.info(f"REAL-TIME UPDATE: New row added")
                
                return True
                
            except Exception as e:
                self.logger.error(f"Sheet update attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    # Try to re-authenticate
                    self.service = None
                else:
                    self.logger.error("Failed to update sheet after max retries")
                    return False
        
        return False
    
    def upload_to_google_drive(self, file_path: str, title: str, 
                               series_name: str = None) -> Optional[str]:
        """
        Upload file to Google Drive and return file ID.
        
        Args:
            file_path: Path to file to upload
            title: Title/name for the file
            series_name: Optional series name for folder organization
        
        Returns:
            File ID if successful, None otherwise
        """
        try:
            if not self.drive_service:
                if not self.authenticate():
                    return None
            
            # Find or create series folder in MyDrive
            parent_id = ''  # Root of MyDrive
            if series_name:
                try:
                    # Search for series folder
                    query = f"name='{series_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
                    result = self.drive_service.files().list(
                        q=query, 
                        spaces='drive', 
                        fields='files(id, name)'
                    ).execute()
                    files = result.get('files', [])
                    
                    if files:
                        parent_id = files[0].get('id')
                        self.logger.info(f"Using series folder: {series_name}")
                    else:
                        # Create series folder
                        folder_metadata = {
                            'name': series_name,
                            'mimeType': 'application/vnd.google-apps.folder'
                        }
                        folder = self.drive_service.files().create(
                            body=folder_metadata, 
                            fields='id'
                        ).execute()
                        parent_id = folder.get('id')
                        self.logger.info(f"Created series folder: {series_name}")
                except Exception as e:
                    self.logger.warning(f"Folder error: {e}")
                    parent_id = ''
            
            # File metadata
            file_metadata = {'name': f"[TEMP] {title}"}
            if parent_id:
                file_metadata['parents'] = [parent_id]
            
            from googleapiclient.http import MediaFileUpload
            media = MediaFileUpload(file_path, mimetype='video/mp4', resumable=True)
            
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            self.logger.info(f"Uploaded to Drive: https://drive.google.com/file/d/{file_id}/view")
            
            return file_id
            
        except Exception as e:
            self.logger.error(f"Drive upload error: {e}")
            return None
    
    def delete_from_google_drive(self, drive_file_id: str) -> bool:
        """
        Delete file from Google Drive.
        
        Args:
            drive_file_id: ID of file to delete
        
        Returns:
            True if deleted, False otherwise
        """
        if not drive_file_id:
            return False
        
        try:
            if not self.drive_service:
                if not self.authenticate():
                    return False
            
            self.logger.info(f"Deleting temp file from Google Drive...")
            self.drive_service.files().delete(fileId=drive_file_id).execute()
            self.logger.info("Temp file deleted from Drive!")
            return True
            
        except Exception as e:
            self.logger.warning(f"Could not delete temp file: {e}")
            return False
