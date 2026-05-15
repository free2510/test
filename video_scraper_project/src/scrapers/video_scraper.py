# -*- coding: utf-8 -*-
"""
Video scraper module for extracting video information from larozaa.yachts.
"""

import re
import logging
from typing import List, Dict, Optional, NamedTuple
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup

from config.settings import (
    BASE_URL,
    DEFAULT_HEADERS,
    REQUEST_TIMEOUT,
)
from src.utils.helpers import setup_logging


class VideoInfo(NamedTuple):
    """Named tuple to hold video information."""
    title: str
    video_id: str
    watch_page_url: str
    url: str


class ServerInfo(NamedTuple):
    """Named tuple to hold server information."""
    name: str
    url: str


class VideoScraper:
    """
    Scraper class for extracting video information from larozaa.yachts.
    
    This class handles:
    - Scraping videos from category pages
    - Getting watch servers from play pages
    - Extracting direct video URLs from embed pages
    """
    
    def __init__(self, base_url: str = None, headers: Dict = None):
        """
        Initialize the video scraper.
        
        Args:
            base_url: Base URL of the source website
            headers: HTTP headers for requests
        """
        self.base_url = base_url or BASE_URL
        self.headers = headers or DEFAULT_HEADERS
        self.logger = setup_logging(self.__class__.__name__)
    
    def scrape_category_videos(self, category_url: str) -> List[VideoInfo]:
        """
        Scrape all videos from a category page.
        
        Args:
            category_url: URL of the category page
        
        Returns:
            List of VideoInfo named tuples
        """
        self.logger.info(f"Fetching videos from: {category_url}")
        
        try:
            response = requests.get(category_url, headers=self.headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            videos = []
            
            # Find all video items
            video_items = soup.select('li.col-xs-6.col-sm-4.col-md-3')
            
            for item in video_items:
                video_info = self._parse_video_item(item)
                if video_info:
                    videos.append(video_info)
            
            self.logger.info(f"Found {len(videos)} videos")
            return videos
            
        except Exception as e:
            self.logger.error(f"Error scraping category: {e}")
            return []
    
    def _parse_video_item(self, item) -> Optional[VideoInfo]:
        """
        Parse a single video item from HTML.
        
        Args:
            item: BeautifulSoup HTML element
        
        Returns:
            VideoInfo or None if parsing fails
        """
        try:
            link_tag = item.find('a', href=True)
            if not link_tag:
                return None
            
            video_url = link_tag['href'].strip()
            title = link_tag.get('title', '').strip()
            
            # Extract video ID
            parsed = urlparse(video_url)
            params = parse_qs(parsed.query)
            video_id = params.get('vid', [None])[0]
            
            if not video_id:
                return None
            
            return VideoInfo(
                title=title,
                video_id=video_id,
                watch_page_url=f"{self.base_url}/play.php?vid={video_id}",
                url=video_url
            )
        except Exception as e:
            self.logger.debug(f"Error parsing video item: {e}")
            return None
    
    def get_watch_servers(self, play_url: str) -> List[ServerInfo]:
        """
        Get all watch servers from a play page.
        
        Args:
            play_url: URL of the play page
        
        Returns:
            List of ServerInfo named tuples
        """
        try:
            response = requests.get(play_url, headers=self.headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            servers = []
            
            # Find watch list
            watch_list = soup.find('ul', class_='WatchList')
            if not watch_list:
                return servers
            
            li_tags = watch_list.find_all('li', attrs={'data-embed-url': True})
            for li in li_tags:
                server_name = li.find('strong')
                embed_url = li.get('data-embed-url', '').strip()
                
                if server_name and embed_url:
                    servers.append(ServerInfo(
                        name=server_name.get_text(strip=True),
                        url=embed_url
                    ))
            
            self.logger.debug(f"Found {len(servers)} servers")
            return servers
            
        except Exception as e:
            self.logger.error(f"Error getting watch servers: {e}")
            return []
    
    def extract_video_url(self, server_url: str) -> Optional[str]:
        """
        Extract direct video URL from server embed page.
        
        Args:
            server_url: URL of the embed server page
        
        Returns:
            Direct video URL or None if extraction fails
        """
        try:
            headers = {
                **self.headers,
                'Referer': server_url
            }
            
            response = requests.get(server_url, headers=headers, timeout=REQUEST_TIMEOUT)
            
            # Look for video sources with multiple patterns
            patterns = [
                r'source\s*=\s*["\']([^"\']+\.mp4[^"\']*)["\']',
                r"data-url=['\"]([^'\"]+\.mp4[^'\"]+)['\"]",
                r"file:\s*['\"]([^'\"]+\.mp4[^'\"]+)['\"]",
                r"<source\s+src=['\"]([^'\"]+\.mp4[^'\"]+)['\"]",
                r'https?://[^\s"\'<>]+\.mp4'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                if matches:
                    video_url = matches[0].strip()
                    if video_url.startswith('//'):
                        video_url = 'https:' + video_url
                    
                    # Verify it's a valid video URL
                    if self._verify_video_url(video_url, headers):
                        return video_url
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting video URL: {e}")
            return None
    
    def _verify_video_url(self, video_url: str, headers: Dict) -> bool:
        """
        Verify that a URL points to a valid video file.
        
        Args:
            video_url: URL to verify
            headers: HTTP headers for request
        
        Returns:
            True if valid video URL, False otherwise
        """
        try:
            head = requests.head(video_url, headers=headers, timeout=10, allow_redirects=True)
            content_type = head.headers.get('Content-Type', '')
            return 'video' in content_type or head.status_code == 200
        except Exception:
            return False
