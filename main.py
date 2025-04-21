#!/usr/bin/env python3

import yaml
from file_scanner import FileScanner
from content_extractor import ContentExtractor
from ai_categorizer import AICategorizer
from file_mover import FileMover
import logging
from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime

# Initialize logger at module level
logger = logging.getLogger(__name__)

def setup_logging(config: Dict[str, Any]) -> None:
    """Set up logging configuration."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        filename=log_dir / "file_organizer.log",
        level=getattr(logging, config["logging"]["level"]),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Also log to console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

def load_config() -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open("config.yaml", "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        raise

def save_operation_log(operation: Dict[str, Any]) -> None:
    """Save operation details to a JSON log file."""
    try:
        log_file = Path("logs/operations.json")
        log_file.parent.mkdir(exist_ok=True)
        
        operations = []
        if log_file.exists():
            with open(log_file, 'r') as f:
                operations = json.load(f)
        
        operations.append(operation)
        
        with open(log_file, 'w') as f:
            json.dump(operations, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving operation log: {str(e)}")
        raise

def main():
    try:
        # Load configuration
        config = load_config()
        setup_logging(config)
        
        logger.info("Starting file organization process")
        
        # Initialize components
        scanner = FileScanner(supported_extensions=config.get("supported_extensions", ['.pdf', '.docx', '.txt', '.md', '.pptx', '.dmg', '.xlsx']))
        extractor = ContentExtractor()
        
        # Extract AI settings
        ai_settings = config.get("ai_settings", {})
        model_name = ai_settings.get("model_name", "facebook/bart-large-mnli")
        device = ai_settings.get("device", "cpu")
        categorizer = AICategorizer(model_name=model_name, device=device)
        
        # Initialize FileMover with destination directory
        destination_dir = Path(config["destination_directory"])
        destination_dir.mkdir(parents=True, exist_ok=True)
        mover = FileMover(destination_dir=str(destination_dir.absolute()))  # Convert to absolute path string
        
        # Get file statistics
        stats = scanner.get_file_stats(Path(config["source_directory"]))
        logger.info(f"Found {stats['total_files']} total files")
        logger.info(f"Found {stats['supported_files']} supported files")
        logger.info(f"Found {stats['unsupported_files']} unsupported files")
        logger.info(f"Total size: {stats['total_size'] / (1024*1024):.2f} MB")
        
        # Process files
        processed_files = set()  # Track processed files to avoid duplicates
        for file_path in scanner.scan_files(Path(config["source_directory"])):
            file_path_str = str(file_path)
            if file_path_str in processed_files:
                continue
                
            try:
                logger.info(f"Processing file: {file_path}")
                
                # Extract content
                content = extractor.extract_content(file_path)
                if not content:
                    logger.warning(f"No content extracted from {file_path}")
                    continue
                
                # Analyze and categorize
                result = categorizer.analyze_and_categorize(content, file_path)
                logger.info(f"Suggested category: {result['category']}, new name: {result['new_filename']}")
                
                # Move file
                destination = mover.move_file(
                    file_path,
                    result["new_filename"],
                    result["category"]
                )
                if destination:
                    logger.info(f"Moved {file_path} to {destination}")
                    processed_files.add(file_path_str)
                    
                    # Save operation details
                    operation = {
                        'timestamp': datetime.now().isoformat(),
                        'source': str(file_path),
                        'destination': str(destination),
                        'category': result['category'],
                        'new_name': result['new_filename'],
                        'confidence': result.get('confidence', 0.0)
                    }
                    save_operation_log(operation)
                else:
                    logger.error(f"Failed to move {file_path}")
                    
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                continue
                
        logger.info("File organization process completed")
        
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
        raise

if __name__ == "__main__":
    main() 