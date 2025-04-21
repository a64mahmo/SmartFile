import logging
from pathlib import Path
from typing import Iterator, List, Dict, Any
import os

class FileScanner:
    def __init__(self, supported_extensions: List[str] = None):
        """
        Initialize the FileScanner with optional list of supported file extensions.
        
        Args:
            supported_extensions: List of file extensions to support (e.g., ['.pdf', '.docx'])
        """
        self.logger = logging.getLogger(__name__)
        self.supported_extensions = supported_extensions or [
            '.pdf', '.docx', '.txt', '.md', '.pptx', '.dmg', '.xlsx'
        ]
        self.logger.info(f"Initialized FileScanner with supported extensions: {self.supported_extensions}")
        self._scanned_files = set()  # Track scanned files to prevent duplicates

    def scan_files(self, source_dir: Path) -> Iterator[Path]:
        """Scan directory for supported files."""
        try:
            if not source_dir.exists():
                self.logger.error(f"Source directory does not exist: {source_dir}")
                return
            
            self.logger.info(f"Scanning directory: {source_dir}")
            self._scanned_files.clear()  # Clear the set at the start of each scan
            
            for file_path in source_dir.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                    file_path_str = str(file_path)
                    if file_path_str not in self._scanned_files:
                        self._scanned_files.add(file_path_str)
                        self.logger.info(f"Found supported file: {file_path}")
                        yield file_path
                elif file_path.is_file():
                    self.logger.debug(f"Skipping unsupported file: {file_path}")
        except Exception as e:
            self.logger.error(f"Error scanning directory {source_dir}: {str(e)}")

    def get_file_stats(self, source_dir: Path) -> Dict[str, Any]:
        """Get statistics about files in the source directory."""
        try:
            if not source_dir.exists():
                self.logger.error(f"Source directory does not exist: {source_dir}")
                return {}
                
            total_files = 0
            supported_files = 0
            unsupported_files = 0
            total_size = 0
            
            for file_path in source_dir.rglob("*"):
                if file_path.is_file():
                    total_files += 1
                    total_size += file_path.stat().st_size
                    if file_path.suffix.lower() in self.supported_extensions:
                        supported_files += 1
                    else:
                        unsupported_files += 1
            
            return {
                "total_files": total_files,
                "supported_files": supported_files,
                "unsupported_files": unsupported_files,
                "total_size": total_size
            }
            
        except Exception as e:
            self.logger.error(f"Error getting file stats for {source_dir}: {str(e)}")
            return {} 