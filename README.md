# AI File Organizer

An intelligent file organization system that uses AI to analyze and categorize files based on their content.

## Features

- Scans directories for files
- Extracts text content from various file types (PDF, DOCX, TXT, MD)
- Uses AI models to analyze content and suggest categories
- Automatically organizes files into category-based directories
- Provides a Streamlit-based web interface for configuration and monitoring
- Comprehensive logging of all operations

## Installation

1. Clone the repository:
```bash
git clone https://github.com/a64mahmo/SmartFile
cd SmartFile
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the application:
   - Copy `config.yaml` and update it with your settings

## Usage

### Command Line
```bash
python main.py
```

### Web Interface
```bash
streamlit run ui_streamlit.py
```

## Configuration

Edit `config.yaml` to customize:
- Source and destination directories
- Supported file types
- Logging configuration

## Project Structure

```
ai-file-organizer/
├── main.py                  # Entry point
├── file_scanner.py          # Scans files in a folder
├── content_extractor.py     # Extracts text content
├── ai_categorizer.py        # AI logic: rename & classify
├── file_mover.py            # Moves/renames files
├── config.yaml              # User config (paths, settings)
├── ui_streamlit.py          # Optional UI (preview, manual mode)
├── logs/                    # Log moved files/actions
└── tests/                   # Unit tests
```

## Requirements

- Python 3.8+
- Dependencies listed in requirements.txt

## License

MIT License 
