from transformers import pipeline
import logging
from typing import Tuple, Optional, Dict
import re
from pathlib import Path
import torch

class AICategorizer:
    def __init__(self, model_name: str = "facebook/bart-large-mnli", device: str = "cpu"):
        self.logger = logging.getLogger(__name__)
        self.device = device
        self.model_name = model_name
        self.categories = [
            "resume", "cover_letter", "business", "technical", "project", 
            "presentation", "documentation", "archive", "software", "financial", "other"
        ]
        self.logger.info(f"Initializing AICategorizer with model: {model_name} on device: {device}")
        self.classifier = pipeline(
            "zero-shot-classification",
            model=model_name,
            device=0 if device == "cuda" else -1
        )

    def _extract_key_info(self, content: str) -> dict:
        """Extract key information from the content to help with naming."""
        info = {
            "title": "",
            "date": "",
            "author": "",
            "keywords": [],
            "is_resume": False,
            "is_cover_letter": False,
            "is_presentation": False,
            "is_financial": False,
            "is_archive": False,
            "is_book": False
        }
        
        # Convert content to lowercase for case-insensitive matching
        content_lower = content.lower()
        
        # Check for book indicators
        book_indicators = [
            "copyright", "published by", "publisher", "isbn", "edition",
            "chapter", "table of contents", "preface", "introduction",
            "bibliography", "references", "index", "acknowledgments"
        ]
        
        # Check for resume indicators
        resume_indicators = [
            "resume", "cv", "curriculum vitae", "professional experience",
            "work history", "skills", "education", "summary", "objective",
            "employment", "work experience", "professional summary"
        ]
        
        # Check for cover letter indicators
        cover_letter_indicators = [
            "cover letter", "application letter", "motivation letter",
            "dear", "sincerely", "application", "position", "role",
            "hiring manager", "job application"
        ]
        
        # Check for presentation indicators
        presentation_indicators = [
            "slide", "presentation", "powerpoint", "keynote",
            "agenda", "outline", "speaker notes"
        ]
        
        # Check for financial document indicators
        financial_indicators = [
            "credit report", "credit score", "credit history",
            "financial statement", "bank statement", "tax return",
            "invoice", "receipt", "balance sheet", "income statement"
        ]
        
        # Check for book indicators first
        for indicator in book_indicators:
            if indicator in content_lower:
                info["is_book"] = True
                break
                
        # Only check other indicators if it's not a book
        if not info["is_book"]:
            # Check for resume indicators
            for indicator in resume_indicators:
                if indicator in content_lower:
                    info["is_resume"] = True
                    break
                    
            # Check for cover letter indicators
            for indicator in cover_letter_indicators:
                if indicator in content_lower:
                    info["is_cover_letter"] = True
                    break
                    
            # Check for presentation indicators
            for indicator in presentation_indicators:
                if indicator in content_lower:
                    info["is_presentation"] = True
                    break
                    
            # Check for financial document indicators
            for indicator in financial_indicators:
                if indicator in content_lower:
                    info["is_financial"] = True
                    break
        
        # Try to find title in first few lines
        lines = content.split('\n')
        if lines:
            info["title"] = lines[0].strip()
            
        # Look for dates in common formats
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',
            r'\d{2}/\d{2}/\d{4}',
            r'\d{2}-\d{2}-\d{4}',
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}'
        ]
        for pattern in date_patterns:
            matches = re.findall(pattern, content)
            if matches:
                info["date"] = matches[0]
                break
                
        # Look for author/name patterns
        name_patterns = [
            r'Name:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'Author:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'By:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'
        ]
        for pattern in name_patterns:
            matches = re.findall(pattern, content)
            if matches:
                info["author"] = matches[0]
                break
                
        # Extract keywords from content
        words = re.findall(r'\b\w+\b', content.lower())
        info["keywords"] = [word for word in words if len(word) > 3 and word not in self._get_stop_words()]
        
        return info

    def _get_stop_words(self) -> set:
        """Get a set of common stop words."""
        return {
            'the', 'and', 'that', 'have', 'for', 'not', 'with', 'you', 'this', 'but',
            'his', 'from', 'they', 'we', 'say', 'her', 'she', 'will', 'one', 'all',
            'would', 'there', 'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who',
            'get', 'which', 'go', 'me', 'when', 'make', 'can', 'like', 'time', 'just',
            'him', 'know', 'take', 'people', 'into', 'year', 'your', 'good', 'some',
            'could', 'them', 'see', 'other', 'than', 'then', 'now', 'look', 'only',
            'come', 'its', 'over', 'think', 'also', 'back', 'after', 'use', 'two',
            'how', 'our', 'work', 'first', 'well', 'way', 'even', 'new', 'want',
            'because', 'any', 'these', 'give', 'day', 'most', 'us'
        }

    def _generate_filename(self, content: str, category: str, original_path: Path, info: dict = None) -> str:
        """Generate a new filename based on content and category."""
        try:
            name_parts = []
            
            # For books, use the title and author from the content
            if category == "books":
                # Try to extract title and author from the first few lines
                lines = content.split('\n')[:10]
                title = ""
                author = ""
                
                # Look for title patterns
                title_patterns = [
                    r'Title:?\s*([^\n]+)',
                    r'Book:?\s*([^\n]+)',
                    r'([A-Z][^.!?]*\b(?:Book|Novel|Story|Tale)\b[^.!?]*)'
                ]
                
                # Look for author patterns
                author_patterns = [
                    r'Author:?\s*([^\n]+)',
                    r'By:?\s*([^\n]+)',
                    r'Written by:?\s*([^\n]+)'
                ]
                
                # Try to find title and author
                for line in lines:
                    for pattern in title_patterns:
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            title = match.group(1).strip()
                            break
                    
                    for pattern in author_patterns:
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match:
                            author = match.group(1).strip()
                            break
                
                # If no title found, try to use the first non-empty line
                if not title:
                    for line in lines:
                        if line.strip():
                            title = line.strip()
                            break
                
                # Clean up the title and author
                if title:
                    title = re.sub(r'[^\w\s-]', '', title)
                    title = re.sub(r'\s+', ' ', title).strip()
                    name_parts.append(title)
                
                if author:
                    author = re.sub(r'[^\w\s-]', '', author)
                    author = re.sub(r'\s+', ' ', author).strip()
                    name_parts.append(f"by_{author}")
            
            # For other document types
            else:
                # Add category
                name_parts.append(category)
                
                # Add author name if available
                if info and info.get('author'):
                    author = info['author'].replace(' ', '_')
                    name_parts.append(author)
                
                # Add date if available
                if info and info.get('date'):
                    date = info['date'].replace(' ', '_')
                    name_parts.append(date)
                
                # Add document type for specific categories
                if category in ['resume', 'cover_letter']:
                    name_parts.append('document')
            
            # Add a unique identifier to prevent duplicates
            unique_id = hash(str(original_path)) % 10000
            name_parts.append(str(unique_id))
            
            # Join all parts and clean the filename
            new_filename = '_'.join(name_parts)
            new_filename = re.sub(r'[^\w\-_.]', '_', new_filename)  # Replace special characters
            new_filename = re.sub(r'_+', '_', new_filename)  # Replace multiple underscores with single
            
            # Add original extension
            new_filename = f"{new_filename}{original_path.suffix}"
            
            self.logger.info(f"Generated new filename: {new_filename}")
            return new_filename
            
        except Exception as e:
            self.logger.error(f"Error generating filename: {str(e)}")
            return f"{original_path.name}"

    def analyze_and_categorize(self, content: str, file_path: Path) -> Dict[str, str]:
        """Analyze content and return suggested filename and category."""
        try:
            # Extract key information first
            info = self._extract_key_info(content)
            
            # Handle different file types
            if file_path.suffix.lower() == '.dmg':
                return self._handle_dmg_file(content, file_path)
            elif file_path.suffix.lower() == '.pptx':
                return self._handle_pptx_file(content, file_path, info)
            
            # Check for specific document types first
            if info["is_book"]:
                category = "books"
            elif info["is_financial"]:
                category = "financial"
            elif info["is_resume"]:
                category = "resume"
            elif info["is_cover_letter"]:
                category = "cover_letter"
            elif info["is_presentation"]:
                category = "presentation"
            else:
                # Use zero-shot classification for other cases
                result = self.classifier(
                    content,
                    candidate_labels=self.categories,
                    multi_label=False
                )
                category = result['labels'][0]
                confidence = result['scores'][0]
            
            # Generate filename based on content and category
            new_filename = self._generate_filename(content, category, file_path, info)
            
            return {
                "category": category,
                "new_filename": new_filename,
                "confidence": confidence if 'confidence' in locals() else 1.0
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing file {file_path}: {str(e)}")
            return {
                "category": "other",
                "new_filename": file_path.name,
                "confidence": 0.0
            }

    def _handle_pptx_file(self, content: str, file_path: Path, info: dict) -> Dict[str, str]:
        """Handle PPTX files specifically."""
        try:
            # Determine category based on content
            if info["is_presentation"]:
                category = "presentation"
            else:
                # Use zero-shot classification for other cases
                result = self.classifier(
                    content,
                    candidate_labels=self.categories,
                    multi_label=False
                )
                category = result['labels'][0]
            
            new_filename = self._generate_filename(content, category, file_path, info)
            
            return {
                "category": category,
                "new_filename": new_filename,
                "confidence": 1.0 if category == "presentation" else result['scores'][0]
            }
            
        except Exception as e:
            self.logger.error(f"Error handling PPTX file {file_path}: {str(e)}")
            return {
                "category": "presentation",
                "new_filename": file_path.name,
                "confidence": 0.0
            }

    def _handle_dmg_file(self, content: str, file_path: Path) -> Dict[str, str]:
        """Handle DMG files specifically."""
        try:
            # Extract basic information from the DMG content
            dmg_info = self._extract_dmg_info(content)
            
            # Determine category based on DMG content
            if "install" in content.lower() or "setup" in content.lower():
                category = "software"
            elif "backup" in content.lower():
                category = "archive"
            else:
                # Use zero-shot classification for other cases
                result = self.classifier(
                    content,
                    candidate_labels=self.categories,
                    multi_label=False
                )
                category = result['labels'][0]
            
            new_filename = self._generate_filename(content, category, file_path)
            
            return {
                "category": category,
                "new_filename": new_filename,
                "confidence": 1.0 if category in ["software", "archive"] else result['scores'][0]
            }
            
        except Exception as e:
            self.logger.error(f"Error handling DMG file {file_path}: {str(e)}")
            return {
                "category": "archive",
                "new_filename": file_path.name,
                "confidence": 0.0
            }

    def _extract_dmg_info(self, content: str) -> Dict[str, str]:
        """Extract basic information from DMG content."""
        info = {}
        try:
            # Extract name if available
            if "name:" in content.lower():
                name_start = content.lower().find("name:") + 5
                name_end = content.find("\n", name_start)
                if name_end != -1:
                    info['name'] = content[name_start:name_end].strip()
            
            # Extract size if available
            if "size:" in content.lower():
                size_start = content.lower().find("size:") + 5
                size_end = content.find("\n", size_start)
                if size_end != -1:
                    info['size'] = content[size_start:size_end].strip()
            
            return info
        except Exception as e:
            self.logger.error(f"Error extracting DMG info: {str(e)}")
            return info 