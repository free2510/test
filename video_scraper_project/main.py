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
import argparse
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from config.settings import CATEGORY_URL, DEFAULT_TEMP_FOLDER
from src.core.processor import VideoProcessor
from src.utils.helpers import setup_logging


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Video Scraper & Uploader - Download videos and upload to DoodStream"
    )
    parser.add_argument(
        "--temp-folder", "-t",
        type=str,
        default=None,
        help=f"Path to temporary folder for downloaded videos. "
             f"If not specified, uses: {DEFAULT_TEMP_FOLDER}"
    )
    parser.add_argument(
        "--category-url", "-u",
        type=str,
        default=CATEGORY_URL,
        help="URL of the category page to scrape videos from"
    )
    return parser.parse_args()


def main():
    """Main entry point for the video scraper."""
    args = parse_arguments()
    logger = setup_logging("main")
    
    print("=" * 60)
    print("🚀 Video Processing Pipeline - REAL-TIME UPDATES")
    print("=" * 60)
    
    # Determine temp folder to use
    temp_folder = args.temp_folder
    if temp_folder:
        print(f"📁 Using custom temp folder: {temp_folder}")
    else:
        print(f"📁 Using default temp folder: {DEFAULT_TEMP_FOLDER}")
    
    # Initialize processor with optional custom temp folder
    processor = VideoProcessor(temp_folder=temp_folder)
    
    # Process all videos from category
    results = processor.process_all(args.category_url)
    
    # Exit with appropriate code
    if results['success'] > 0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
