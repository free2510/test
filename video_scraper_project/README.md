# Video Scraper Project

A professional video scraper and uploader that extracts videos from larozaa.yachts, uploads them to DoodStream with organized folder structure, and updates Google Sheets in real-time.

## 📁 Project Structure

```
video_scraper_project/
├── config/
│   ├── __init__.py          # Config package exports
│   ├── settings.py          # All configuration variables
│   └── .env.example         # Example environment variables
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── downloader.py    # Video download functionality
│   │   └── processor.py     # Main workflow orchestrator
│   ├── scrapers/
│   │   ├── __init__.py
│   │   └── video_scraper.py # Website scraping logic
│   ├── uploaders/
│   │   ├── __init__.py
│   │   └── doodstream_uploader.py  # DoodStream upload logic
│   ├── sheets/
│   │   ├── __init__.py
│   │   └── google_sheets.py # Google Sheets management
│   └── utils/
│       ├── __init__.py
│       └── helpers.py       # Utility functions
├── tests/                   # Test files (to be added)
├── docs/                    # Documentation (to be added)
├── main.py                  # Entry point
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## 🚀 Features

- **Video Scraping**: Extracts video information from larozaa.yachts category pages
- **Multi-Server Support**: Tests multiple servers to find working video URLs
- **Progress Tracking**: Downloads videos with progress bars
- **DoodStream Upload**: Uploads videos with automatic folder organization:
  - Category Folder (e.g., "رمضان 2026 - مسلسلات")
  - Series Folder (e.g., "مسلسل حكاية نرجس")
  - Video File (properly renamed)
- **Real-time Google Sheets Updates**: Updates spreadsheet after each video
- **Resume Capability**: Tracks processed videos to resume interrupted runs
- **Rate Limiting**: Respects DoodStream API rate limits (15-second delays)

## 📦 Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd video_scraper_project
   ```

2. **Create virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp config/.env.example .env
   # Edit .env with your API keys and settings
   ```

## ⚙️ Configuration

Edit `.env` or `config/settings.py` with your credentials:

```env
# DoodStream
DOODSTREAM_API_KEY=your_api_key_here

# Google
GOOGLE_SHEET_ID=your_sheet_id_here

# Source Website
CATEGORY_URL=https://larozaa.yachts/category.php?cat=ramadan-2026
CATEGORY_NAME=رمضان 2026 - مسلسلات

# Paths
TEMP_FOLDER=/content/temp_videos
PROCESSED_FILE=/content/processed_videos.json
```

## 🎯 Usage

### Basic Usage

```bash
python main.py
```

### Google Colab

This project is designed to work in Google Colab. Upload the project folder to Colab and run:

```python
!pip install -r requirements.txt
!python main.py
```

## 📊 Google Sheet Format

The script automatically creates/maintains a Google Sheet with these columns:

| Timestamp | Title | Video ID | Watch Link | Series Name | Category | DoodStream Watch | DoodStream Download | Status |
|-----------|-------|----------|------------|-------------|----------|------------------|---------------------|--------|

## 🔧 API Rate Limiting

The script respects DoodStream's API rate limits by adding 15-second delays between:
1. Folder creation
2. File upload
3. File rename
4. File move

## 📝 Progress Tracking

Processed video IDs are saved to `processed_videos.json`. Running the script again will skip already processed videos.

To reset progress:
```bash
rm /content/processed_videos.json
```

## 🛠️ Development

### Adding New Scrapers

Extend `src/scrapers/video_scraper.py` to support additional websites.

### Adding New Upload Destinations

Create a new uploader class in `src/uploaders/` following the pattern of `doodstream_uploader.py`.

### Testing

```bash
pytest tests/
```

## ⚠️ Important Notes

1. **API Keys**: Never commit your `.env` file with real API keys
2. **Rate Limits**: Don't modify the API delay settings unless you understand the consequences
3. **Folder Structure**: Videos MUST be placed in the correct folder structure on DoodStream
4. **Google Auth**: First run requires manual authentication in browser

## 📄 License

[Add your license here]

## 🤝 Contributing

[Add contribution guidelines here]
