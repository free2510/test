# -*- coding: utf-8 -*-
"""
DoodStream uploader module for uploading videos with organized folder structure.

Folder Structure on DoodStream:
  رمضان 2026 - مسلسلات (Category)
    └── مسلسل حكاية نرجس (Series)
        └── مسلسل حكاية نرجس الحلقة 7 السابعة.mp4 (Video)
"""

import time
import logging
from typing import Optional, Dict, Tuple
import requests
from doodstream import DoodStream

from config.settings import (
    DOODSTREAM_API_KEY,
    DOODSTREAM_API_BASE_URL,
    DOODSTREAM_WATCH_BASE_URL,
    DOODSTREAM_DOWNLOAD_BASE_URL,
    DOODSTREAM_API_DELAY,
    CATEGORY_NAME,
    REQUEST_TIMEOUT,
)
from src.utils.helpers import setup_logging


class DoodStreamUploader:
    """
    Uploader class for DoodStream with folder management.
    
    This class handles:
    - Creating category and series folders
    - Uploading videos to correct folder structure
    - Renaming files
    - Managing folder cache to avoid duplicate API calls
    """
    
    def __init__(self, api_key: str = None, category_name: str = None):
        """
        Initialize the DoodStream uploader.
        
        Args:
            api_key: DoodStream API key
            category_name: Name of the main category folder
        """
        self.api_key = api_key or DOODSTREAM_API_KEY
        self.category_name = category_name or CATEGORY_NAME
        self.api_delay = DOODSTREAM_API_DELAY
        self.logger = setup_logging(self.__class__.__name__)
        
        # Initialize DoodStream client
        self.dood = DoodStream(self.api_key)
        
        # Cache for folder IDs to avoid recreating folders
        self.folder_cache: Dict[str, Tuple[Optional[str], Optional[str]]] = {}
    
    def get_or_create_folder_structure(self, series_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Create or retrieve Category > Series folder structure on DoodStream.
        
        Args:
            series_name: Name of the series folder
        
        Returns:
            Tuple of (category_folder_id, series_folder_id)
        """
        # Check cache first
        if series_name in self.folder_cache:
            cat_id, series_id = self.folder_cache[series_name]
            self.logger.info(f"Using cached folder structure for: {series_name}")
            return cat_id, series_id
        
        # Step 1: Find or create Category folder
        category_folder_id = self._get_or_create_category_folder()
        
        # Step 2: Find or create Series folder inside Category
        series_folder_id = None
        if category_folder_id:
            series_folder_id = self._get_or_create_series_folder(
                series_name, 
                category_folder_id
            )
        
        # Cache the result
        if category_folder_id:
            self.folder_cache[series_name] = (category_folder_id, series_folder_id)
            self.logger.info(f"Cached folder structure: {series_name}")
        
        return category_folder_id, series_folder_id
    
    def _get_or_create_category_folder(self) -> Optional[str]:
        """Find or create the main category folder in root."""
        try:
            # List folders in root
            list_url = f"{DOODSTREAM_API_BASE_URL}/folder/list?key={self.api_key}"
            self.logger.debug(f"Listing root folders")
            
            response = requests.get(list_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            full_response = response.json()
            
            result_data = full_response.get('result', {})
            folders = result_data.get('folders', []) if isinstance(result_data, dict) else []
            
            # Search for existing category folder
            for item in folders:
                folder_name = item.get('name', '')
                folder_id = item.get('fld_id') or item.get('code')
                
                if self._names_match(folder_name, self.category_name):
                    self.logger.info(f"Found category folder: {self.category_name} (ID: {folder_id})")
                    return folder_id
            
            # Create category folder if not found
            self.logger.info(f"Creating category folder: {self.category_name}")
            create_url = f"{DOODSTREAM_API_BASE_URL}/folder/create?key={self.api_key}&name={requests.utils.quote(self.category_name)}"
            
            result = requests.get(create_url, timeout=REQUEST_TIMEOUT).json()
            time.sleep(self.api_delay)
            
            if result and result.get('msg') == 'OK':
                res_data = result.get('result', {})
                if isinstance(res_data, dict):
                    category_folder_id = res_data.get('fld_id')
                    if category_folder_id:
                        self.logger.info(f"Created category folder: {self.category_name} (ID: {category_folder_id})")
                        return category_folder_id
            
            # Re-list to get folder ID if creation said "already exists"
            return self._recheck_folder(list_url, self.category_name)
            
        except Exception as e:
            self.logger.error(f"Category folder error: {e}")
            return None
    
    def _get_or_create_series_folder(self, series_name: str, 
                                      category_folder_id: str) -> Optional[str]:
        """Find or create series folder inside category."""
        try:
            # List folders in category
            list_url = f"{DOODSTREAM_API_BASE_URL}/folder/list?key={self.api_key}&fld_id={category_folder_id}"
            self.logger.debug(f"Listing folders in category")
            
            response = requests.get(list_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            full_response = response.json()
            
            result_data = full_response.get('result', {})
            folders = result_data.get('folders', []) if isinstance(result_data, dict) else []
            
            # Search for existing series folder
            for item in folders:
                folder_name = item.get('name', '')
                folder_id = item.get('fld_id') or item.get('code')
                
                if self._names_match(folder_name, series_name):
                    self.logger.info(f"Found series folder: {series_name} (ID: {folder_id})")
                    return folder_id
            
            # Create series folder if not found
            self.logger.info(f"Creating series folder: {series_name}")
            create_url = f"{DOODSTREAM_API_BASE_URL}/folder/create?key={self.api_key}&name={requests.utils.quote(series_name)}&parent_id={category_folder_id}"
            
            result = requests.get(create_url, timeout=REQUEST_TIMEOUT).json()
            time.sleep(self.api_delay)
            
            if result and result.get('msg') == 'OK':
                res_data = result.get('result', {})
                if isinstance(res_data, dict):
                    series_folder_id = res_data.get('fld_id')
                    if series_folder_id:
                        self.logger.info(f"Created series folder: {series_name} (ID: {series_folder_id})")
                        return series_folder_id
            
            # Re-list to get folder ID
            return self._recheck_folder(list_url, series_name)
            
        except Exception as e:
            self.logger.error(f"Series folder error: {e}")
            return None
    
    def _recheck_folder(self, list_url: str, target_name: str) -> Optional[str]:
        """Re-list folders to find a recently created folder."""
        try:
            response = requests.get(list_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            full_response = response.json()
            
            result_data = full_response.get('result', {})
            folders = result_data.get('folders', []) if isinstance(result_data, dict) else []
            
            for item in folders:
                folder_name = item.get('name', '')
                folder_id = item.get('fld_id') or item.get('code')
                
                if self._names_match(folder_name, target_name):
                    self.logger.info(f"Found folder after recheck: {target_name} (ID: {folder_id})")
                    return folder_id
        except Exception as e:
            self.logger.warning(f"Recheck failed: {e}")
        
        return None
    
    def _names_match(self, name1: str, name2: str) -> bool:
        """Check if two names match (with whitespace normalization and partial matching)."""
        name1 = name1.strip()
        name2 = name2.strip()
        
        # Direct match
        if name1 == name2:
            return True
        
        # Partial match
        if name1 in name2 or name2 in name1:
            return True
        
        return False
    
    def upload_to_doodstream(self, file_path: str, series_name: str, 
                             video_title: str) -> Optional[Dict]:
        """
        Upload video to DoodStream in correct folder structure.
        
        Args:
            file_path: Path to video file
            series_name: Name of series for folder organization
            video_title: Title of the video
        
        Returns:
            Dict with filecode, watch_url, download_url, title or None if failed
        """
        try:
            # Step 0: Ensure folder structure exists
            self.logger.info(f"Ensuring folder structure: {self.category_name} > {series_name}")
            cat_folder_id, series_folder_id = self.get_or_create_folder_structure(series_name)
            target_folder_id = series_folder_id if series_folder_id else cat_folder_id
            
            if not target_folder_id:
                self.logger.error("Could not create folder structure. Aborting upload.")
                return None
            
            # Clean the title
            clean_title = video_title.replace('.mp4', '').strip()
            clean_title = ' '.join(clean_title.split())
            
            # Step 1: Upload to root (library limitation)
            self.logger.info("Uploading to DoodStream...")
            result = self.dood.local_upload(file_path)
            
            if not result:
                self.logger.error("Upload failed: No response from DoodStream")
                return None
            
            # Step 2: Extract file_code from response
            file_code = self._extract_file_code(result)
            if not file_code:
                self.logger.error(f"Could not get file code from upload. Response: {result}")
                return None
            
            self.logger.info(f"Uploaded to root! File code: {file_code}")
            time.sleep(self.api_delay)
            
            # Step 3: Rename file
            self._rename_file(file_code, clean_title)
            
            # Step 4: Move to series folder
            if not self._move_to_folder(file_code, target_folder_id, series_name):
                # Fallback: Try clone + delete
                if not self._clone_and_delete(file_code, target_folder_id):
                    self.logger.error("Could not place file in correct folder. Deleting uploaded file.")
                    self.dood.delete_file([file_code])
                    return None
            
            # Build final URLs
            watch_url = f"{DOODSTREAM_WATCH_BASE_URL}/{file_code}"
            download_url = f"{DOODSTREAM_DOWNLOAD_BASE_URL}/{file_code}"
            
            self.logger.info(f"Upload complete!")
            self.logger.info(f"Watch: {watch_url}")
            self.logger.info(f"Download: {download_url}")
            
            return {
                'filecode': file_code,
                'watch_url': watch_url,
                'download_url': download_url,
                'title': clean_title
            }
            
        except Exception as e:
            self.logger.error(f"Upload error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_file_code(self, result) -> Optional[str]:
        """Extract file_code from various response formats."""
        if isinstance(result, dict) and 'result' in result:
            res_data = result['result']
            if isinstance(res_data, list) and len(res_data) > 0:
                return res_data[0].get('filecode')
            elif isinstance(res_data, dict):
                return res_data.get('filecode')
        elif isinstance(result, list) and len(result) > 0:
            return result[0].get('filecode')
        elif isinstance(result, dict):
            return result.get('filecode')
        return None
    
    def _rename_file(self, file_code: str, title: str) -> None:
        """Rename a file on DoodStream."""
        try:
            rename_url = f"{DOODSTREAM_API_BASE_URL}/file/rename?key={self.api_key}&file_code={file_code}&title={requests.utils.quote(title)}"
            rename_resp = requests.get(rename_url, timeout=REQUEST_TIMEOUT).json()
            time.sleep(self.api_delay)
            
            if rename_resp.get('msg') == 'OK':
                self.logger.info(f"Renamed file to: {title}")
            else:
                self.logger.warning(f"Rename response: {rename_resp}")
        except Exception as e:
            self.logger.warning(f"Could not rename file: {e}")
    
    def _move_to_folder(self, file_code: str, folder_id: str, series_name: str) -> bool:
        """Move a file to a folder using the move API."""
        try:
            self.logger.info(f"Moving to folder: {series_name} (ID: {folder_id})")
            
            move_url = f"{DOODSTREAM_API_BASE_URL}/file/move?key={self.api_key}&file_code={file_code}&fld_id={folder_id}"
            move_resp = requests.get(move_url, timeout=REQUEST_TIMEOUT).json()
            time.sleep(self.api_delay)
            
            if move_resp.get('msg') == 'OK':
                self.logger.info("Moved to folder successfully")
                return True
            else:
                self.logger.warning(f"Move response: {move_resp}")
                return False
        except Exception as e:
            self.logger.warning(f"Move error: {e}")
            return False
    
    def _clone_and_delete(self, file_code: str, folder_id: str) -> bool:
        """Fallback method: clone to folder then delete original."""
        try:
            copy_url = f"{DOODSTREAM_API_BASE_URL}/file/clone?key={self.api_key}&file_code={file_code}&fld_id={folder_id}"
            copy_resp = requests.get(copy_url, timeout=REQUEST_TIMEOUT).json()
            time.sleep(self.api_delay)
            
            if copy_resp.get('msg') == 'OK':
                self.logger.info("Copied to folder (fallback method)")
                delete_result = self.dood.delete_file([file_code])
                if delete_result and delete_result.get('msg') == 'OK':
                    self.logger.info("Deleted original from root")
                return True
            else:
                self.logger.warning(f"Clone response: {copy_resp}")
                return False
        except Exception as e:
            self.logger.warning(f"Clone fallback failed: {e}")
            return False
