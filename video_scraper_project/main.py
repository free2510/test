# -*- coding: utf-8 -*-
"""
Video Scraper Project - Main Entry Point

Scrapes videos from larozaa.yachts, uploads to DoodStream with organized folders,
and updates Google Sheets in REAL-TIME after each video.

Folder Structure on DoodStream:
  رمضان 2026 - مسلسلات (Category)
    └── مسلسل حكاية نرجس (Series)
        └── مسلسل حكاية نرجس الحلقة 7 السابعة.mp4 (Video)
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from config.settings import CATEGORY_URL
from src.core.processor import VideoProcessor
from src.utils.helpers import setup_logging


def main():
    """Main entry point for the video scraper."""
    logger = setup_logging("main")
    
    print("=" * 60)
    print("🚀 Video Processing Pipeline - REAL-TIME UPDATES")
    print("=" * 60)
    
    # Initialize processor
    processor = VideoProcessor()
    
    # Process all videos from category
    results = processor.process_all(CATEGORY_URL)
    
    # Exit with appropriate code
    if results['success'] > 0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
