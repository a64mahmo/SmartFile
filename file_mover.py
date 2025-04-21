from pathlib import Path
import shutil
import logging
import json
from datetime import datetime
from typing import Optional, Dict
import os

class FileMover:
    def __init__(self, destination_dir: str):
        self.destination_dir = Path(destination_dir).resolve()  # Convert to absolute path
        self.destination_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.operations_log = []
        self.rollback_file = Path("logs/rollback.json")
        self.logger.info(f"Initialized FileMover with destination directory: {self.destination_dir}")

    def move_file(self, source_path: Path, new_filename: str, category: str) -> Optional[Path]:
        """Move a file to a new location with enhanced error handling and rollback support."""
        try:
            source_path = source_path.resolve()  # Convert to absolute path
            self.logger.info(f"Source path resolved to: {source_path}")
            
            if not source_path.exists():
                self.logger.error(f"Source file does not exist: {source_path}")
                return None

            # Create destination directory if it doesn't exist
            dest_dir = self.destination_dir / category
            self.logger.info(f"Creating destination directory: {dest_dir}")
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Handle duplicate filenames
            dest_path = dest_dir / new_filename
            counter = 1
            while dest_path.exists():
                name_parts = new_filename.rsplit('.', 1)
                if len(name_parts) == 2:
                    new_name = f"{name_parts[0]}_{counter}.{name_parts[1]}"
                else:
                    new_name = f"{new_filename}_{counter}"
                dest_path = dest_dir / new_name
                counter += 1

            # Log the operation before moving
            operation = {
                'timestamp': datetime.now().isoformat(),
                'source': str(source_path),
                'destination': str(dest_path),
                'category': category,
                'new_name': new_filename
            }
            self._save_operation(operation)
            
            # Check permissions
            if not os.access(str(source_path), os.R_OK):
                self.logger.error(f"No read permission for source file: {source_path}")
                return None
                
            if not os.access(str(dest_dir), os.W_OK):
                self.logger.error(f"No write permission for destination directory: {dest_dir}")
                return None
            
            # Move the file
            self.logger.info(f"Attempting to move {source_path} to {dest_path}")
            try:
                shutil.move(str(source_path), str(dest_path))
                self.logger.info(f"Successfully moved {source_path} to {dest_path}")
            except PermissionError as e:
                self.logger.error(f"Permission error while moving file: {str(e)}")
                return None
            except OSError as e:
                self.logger.error(f"OS error while moving file: {str(e)}")
                return None
            
            return dest_path

        except Exception as e:
            self.logger.error(f"Error moving file {source_path}: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def _save_operation(self, operation: Dict) -> None:
        """Save operation to rollback file."""
        try:
            # Create logs directory if it doesn't exist
            self.rollback_file.parent.mkdir(exist_ok=True)
            
            # Load existing operations if file exists
            operations = []
            if self.rollback_file.exists():
                with open(self.rollback_file, 'r') as f:
                    operations = json.load(f)
            
            # Add new operation
            operations.append(operation)
            
            # Save updated operations
            with open(self.rollback_file, 'w') as f:
                json.dump(operations, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving operation to rollback file: {str(e)}")

    def rollback_last_operation(self) -> bool:
        """Rollback the last file move operation."""
        try:
            if not self.rollback_file.exists():
                self.logger.warning("No rollback file found")
                return False

            with open(self.rollback_file, 'r') as f:
                operations = json.load(f)

            if not operations:
                self.logger.warning("No operations to rollback")
                return False

            # Get the last operation
            last_op = operations.pop()

            # Move file back to original location
            source = Path(last_op['destination']).resolve()
            destination = Path(last_op['source']).resolve()
            
            if source.exists():
                shutil.move(str(source), str(destination))
                self.logger.info(f"Rolled back: {source} -> {destination}")
                
                # Save updated operations (without the rolled back one)
                with open(self.rollback_file, 'w') as f:
                    json.dump(operations, f, indent=2)
                    
                return True
            else:
                self.logger.error(f"Source file not found for rollback: {source}")
                return False

        except Exception as e:
            self.logger.error(f"Error during rollback: {str(e)}")
            return False 