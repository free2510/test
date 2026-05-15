# -*- coding: utf-8 -*-
"""
Video downloader module for downloading videos from URLs.
"""

import os
import logging
from typing import Optional
import requests
from tqdm import tqdm

from config.settings import (
    TEMP_FOLDER,
    DEFAULT_TEMP_FOLDER,
    DEFAULT_HEADERS,
    VIDEO_MIN_SIZE,
    REQUEST_TIMEOUT,
)
from src.utils.helpers import setup_logging, sanitize_filename


class VideoDownloader:
    """
    Downloader class for downloading videos from URLs.
    
    This class handles:
    - Downloading videos with progress tracking
    - Saving to temporary folder
    - Verifying downloaded file size
    - Cleaning up failed downloads
    """
    
    def __init__(self, temp_folder: str = None, headers: dict = None):
        """
        Initialize the video downloader.
        
        Args:
            temp_folder: Folder to store temporary downloads. If None, uses config default.
            headers: HTTP headers for requests
        """
        # Use provided temp_folder, or fall back to config's DEFAULT_TEMP_FOLDER
        self.temp_folder = temp_folder or TEMP_FOLDER or DEFAULT_TEMP_FOLDER
        self.headers = headers or DEFAULT_HEADERS
        self.logger = setup_logging(self.__class__.__name__)
        
        # Ensure temp folder exists
        os.makedirs(self.temp_folder, exist_ok=True)
        self.logger.info(f"Temp folder initialized: {self.temp_folder}")
    
    def download_video(self, url: str, filename: str) -> Optional[str]:
        """
        Download a video from URL to temp folder.
        
        Args:
            url: Direct video URL
            filename: Filename to save as
        
        Returns:
            Path to downloaded file or None if download fails
        """
        filepath = os.path.join(self.temp_folder, sanitize_filename(filename))
        
        try:
            headers = {**self.headers}
            response = requests.get(url, headers=headers, stream=True, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            # Download with progress bar
            with open(filepath, 'wb') as f, tqdm(
                desc=f"⬇️ {os.path.basename(filepath)[:30]}",
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
                bar_format='{l_bar}{bar}| {n:.1f}/{total_fmt} [{remaining}, {rate_fmt}]',
                mininterval=0.5,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
            
            # Verify download
            if os.path.exists(filepath) and os.path.getsize(filepath) > VIDEO_MIN_SIZE:
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                self.logger.info(f"Download successful! Size: {size_mb:.2f} MB")
                return filepath
            else:
                self.logger.error(f"Download failed: File too small or missing")
                self._cleanup(filepath)
                return None
                
        except Exception as e:
            self.logger.error(f"Download error: {e}")
            self._cleanup(filepath)
            return None
    
    def _cleanup(self, filepath: str) -> None:
        """
        Remove a file if it exists.
        
        Args:
            filepath: Path to file to remove
        """
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                self.logger.debug(f"Cleaned up file: {filepath}")
        except Exception as e:
            self.logger.warning(f"Could not cleanup file {filepath}: {e}")
    
    def delete_file(self, filepath: str) -> bool:
        """
        Delete a file by path.
        
        Args:
            filepath: Path to file to delete
        
        Returns:
            True if deleted, False otherwise
        """
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                self.logger.info(f"Deleted file: {filepath}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting file: {e}")
            return False
