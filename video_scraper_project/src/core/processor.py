# -*- coding: utf-8 -*-
"""
Main video processor that orchestrates the entire workflow.
"""

import re
import time
import json
import os
import logging
from typing import Dict, Any, Optional, List

from config.settings import (
    CATEGORY_NAME,
    PROCESSED_FILE,
)
from src.utils.helpers import setup_logging, load_json_file, save_json_file
from src.scrapers import VideoScraper, VideoInfo
from src.core.downloader import VideoDownloader
from src.uploaders import DoodStreamUploader
from src.sheets import GoogleSheetsManager


class VideoProcessor:
    """
    Main processor class that orchestrates the video scraping, downloading,
    uploading, and sheet update workflow.
    
    This class handles:
    - Processing individual videos through the complete pipeline
    - Tracking processed videos for resume capability
    - Coordinating between scraper, downloader, uploader, and sheets manager
    """
    
    def __init__(self, temp_folder: str = None):
        """
        Initialize the video processor with all required components.
        
        Args:
            temp_folder: Custom temporary folder path for downloaded videos.
                        If None, uses the default from config.
        """
        self.logger = setup_logging(self.__class__.__name__)
        
        # Initialize components
        self.scraper = VideoScraper()
        self.downloader = VideoDownloader(temp_folder=temp_folder)
        self.uploader = DoodStreamUploader()
        self.sheets_manager = GoogleSheetsManager()
        
        # Load processed videos set
        self.processed_videos = set()
        self._load_processed_videos()
    
    def _load_processed_videos(self) -> None:
        """Load previously processed videos from JSON file."""
        data = load_json_file(PROCESSED_FILE)
        if data:
            self.processed_videos = set(data)
            self.logger.info(f"Loaded {len(self.processed_videos)} previously processed videos")
    
    def _save_processed_video(self, video_id: str) -> None:
        """Save a processed video ID to the JSON file."""
        self.processed_videos.add(video_id)
        save_json_file(PROCESSED_FILE, list(self.processed_videos))
    
    def extract_series_name(self, title: str) -> str:
        """
        Extract series name from video title.
        
        Args:
            title: Video title
        
        Returns:
            Series name extracted from title
        """
        # Pattern: "مسلسل XXX الحلقة YYY"
        match = re.match(r'(مسلسل\s+[^\s]+(?:\s+[^\s]+)?)\s+الحلقة', title)
        if match:
            return match.group(1).strip()
        return title.split('الحلقة')[0].strip() if 'الحلقة' in title else title[:30]
    
    def process_video(self, video_info: VideoInfo, index: int, total: int) -> bool:
        """
        Process a single video through the complete pipeline.
        
        Args:
            video_info: Video information from scraper
            index: Current video index (1-based)
            total: Total number of videos
        
        Returns:
            True if processing successful, False otherwise
        """
        self.logger.info("=" * 60)
        self.logger.info(f"[{index}/{total}] {video_info.title}")
        self.logger.info("=" * 60)
        
        # Prepare video data for sheet updates
        video_data = {
            'title': video_info.title,
            'video_id': video_info.video_id,
            'watch_link': '',
            'series_name': self.extract_series_name(video_info.title),
            'category': CATEGORY_NAME,
            'dood_watch': '',
            'dood_download': ''
        }
        
        # Update sheet: Starting
        self.sheets_manager.update_sheet_realtime(video_data, status="⏳ Starting")
        
        # Step 1: Get watch servers
        self.logger.info("Getting watch servers...")
        servers = self.scraper.get_watch_servers(video_info.watch_page_url)
        self.logger.info(f"Found {len(servers)} servers")
        
        if not servers:
            self.sheets_manager.update_sheet_realtime(video_data, status="❌ No servers found")
            return False
        
        # Step 2: Try servers until we find working video URL
        video_url = None
        for idx, server in enumerate(servers, 1):
            self.logger.info(f"Testing server {idx}/{len(servers)}: {server.name}")
            
            extracted_url = self.scraper.extract_video_url(server.url)
            if extracted_url:
                video_url = extracted_url
                self.logger.info(f"Working server found: {server.name}")
                video_data['watch_link'] = server.url
                break
        
        if not video_url:
            self.logger.error("No working server found")
            self.sheets_manager.update_sheet_realtime(video_data, status="❌ No working server")
            return False
        
        # Step 3: Download video
        safe_filename = f"{video_info.video_id}_{video_data['series_name']}.mp4"
        self.logger.info("Downloading video...")
        downloaded_path = self.downloader.download_video(video_url, safe_filename)
        
        if not downloaded_path:
            self.sheets_manager.update_sheet_realtime(video_data, status="❌ Download failed")
            return False
        
        # Step 4: Upload to DoodStream
        self.logger.info("Uploading to DoodStream...")
        upload_result = self.uploader.upload_to_doodstream(
            downloaded_path,
            video_data['series_name'],
            video_info.title
        )
        
        # Cleanup local temp file
        self.downloader.delete_file(downloaded_path)
        
        if not upload_result:
            self.sheets_manager.update_sheet_realtime(video_data, status="❌ DoodStream upload failed")
            return False
        
        # Update video data with upload results
        video_data['dood_watch'] = upload_result.get('watch_url', '')
        video_data['dood_download'] = upload_result.get('download_url', '')
        
        # Step 5: Final update - Success
        self.sheets_manager.update_sheet_realtime(video_data, status="✅ Success")
        
        # Save progress
        file_code = upload_result.get('filecode', '')
        self._save_processed_video(video_info.video_id)
        
        self.logger.info(f"COMPLETED!")
        self.logger.info(f"Watch: https://dsvplay.com/e/{file_code}")
        self.logger.info(f"Download: https://dsvplay.com/d/{file_code}")
        
        return True
    
    def process_all(self, category_url: str) -> Dict[str, int]:
        """
        Process all videos from a category URL.
        
        Args:
            category_url: URL of the category page
        
        Returns:
            Dictionary with processing statistics
        """
        # Initialize sheet
        self.sheets_manager.init_sheet()
        
        # Scrape videos
        videos = self.scraper.scrape_category_videos(category_url)
        
        if not videos:
            self.logger.info("All videos already processed or no videos found!")
            return {'success': 0, 'total': 0}
        
        # Process each video
        total = len(videos)
        success_count = 0
        
        self.logger.info(f"Starting processing of {total} videos...")
        
        for idx, video in enumerate(videos, 1):
            try:
                if self.process_video(video, idx, total):
                    success_count += 1
                
                # Small delay between videos
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Error processing {video.title}: {e}")
                # Still update sheet with error
                video_data = {
                    'title': video.title,
                    'video_id': video.video_id,
                    'series_name': self.extract_series_name(video.title),
                    'dood_watch': '',
                    'dood_download': ''
                }
                self.sheets_manager.update_sheet_realtime(
                    video_data, 
                    status=f"❌ Error: {str(e)[:50]}"
                )
        
        # Summary
        self.logger.info("=" * 60)
        self.logger.info("PROCESSING COMPLETE")
        self.logger.info("=" * 60)
        self.logger.info(f"Successfully processed: {success_count}/{total}")
        self.logger.info("Progress saved - you can resume anytime by running again")
        self.logger.info("Google Sheet updated in real-time with all results")
        self.logger.info("=" * 60)
        
        return {
            'success': success_count,
            'total': total,
            'failed': total - success_count
        }
