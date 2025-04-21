import unittest
from pathlib import Path
from file_scanner import FileScanner
import tempfile
import os

class TestFileScanner(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()
        self.scanner = FileScanner(self.temp_dir)
        
        # Create some test files
        self.test_files = [
            "test1.txt",
            "test2.pdf",
            "test3.docx",
            ".hidden.txt"
        ]
        
        for file in self.test_files:
            with open(os.path.join(self.temp_dir, file), "w") as f:
                f.write("test content")

    def test_scan_files(self):
        # Get all files from scanner
        files = list(self.scanner.scan_files())
        
        # Should find 3 files (excluding hidden file)
        self.assertEqual(len(files), 3)
        
        # Check that hidden file is not included
        hidden_file = Path(self.temp_dir) / ".hidden.txt"
        self.assertNotIn(hidden_file, files)

    def test_invalid_directory(self):
        with self.assertRaises(ValueError):
            FileScanner("/nonexistent/directory")

if __name__ == "__main__":
    unittest.main() 