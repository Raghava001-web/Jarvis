"""
PDF Handler - PDF text extraction and summarization
====================================================
Features:
- Extract text from PDF files
- Summarize PDF content using AI
- Get page count and metadata
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any


class PDFHandler:
    """Handles PDF operations including text extraction and summarization"""
    
    def __init__(self, perception=None, decision_engine=None):
        print("[PDF] Initializing PDF Handler...")
        self.perception = perception
        self.decision_engine = decision_engine
        
        # Check for PyPDF2
        self.pypdf_available = False
        try:
            import PyPDF2
            self.pypdf_available = True
            print("[PDF] PyPDF2 available")
        except ImportError:
            print("[PDF] PyPDF2 not available - install with: pip install PyPDF2")
        
        # Check for pdfplumber (better text extraction)
        self.pdfplumber_available = False
        try:
            import pdfplumber
            self.pdfplumber_available = True
            print("[PDF] pdfplumber available")
        except ImportError:
            print("[PDF] pdfplumber not available")
        
        print("[PDF] PDF Handler Ready")
    
    def _get_title(self) -> str:
        if self.perception:
            return getattr(self.perception, 'user_title', 'sir')
        return 'sir'
    
    def _speak(self, text: str):
        if self.perception:
            self.perception.speak(text)
        else:
            print(f"[PDF] {text}")
    
    def extract_text(self, file_path: str, max_pages: int = None) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            file_path: Path to PDF file
            max_pages: Maximum pages to extract (None = all)
            
        Returns:
            Extracted text or empty string
        """
        title = self._get_title()
        path = Path(file_path)
        
        if not path.exists():
            self._speak(f"PDF file not found, {title}.")
            return ""
        
        if not path.suffix.lower() == '.pdf':
            self._speak(f"That's not a PDF file, {title}.")
            return ""
        
        try:
            self._speak(f"Reading PDF, {title}. One moment.")
            
            text = ""
            
            # Try pdfplumber first (better extraction)
            if self.pdfplumber_available:
                import pdfplumber
                with pdfplumber.open(str(path)) as pdf:
                    pages = pdf.pages[:max_pages] if max_pages else pdf.pages
                    for page in pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n\n"
            
            # Fallback to PyPDF2
            elif self.pypdf_available:
                import PyPDF2
                with open(str(path), 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    pages = reader.pages[:max_pages] if max_pages else reader.pages
                    for page in pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n\n"
            
            else:
                self._speak(f"PDF reading capability not available, {title}. Please install PyPDF2.")
                return ""
            
            return text.strip()
            
        except Exception as e:
            print(f"[PDF] Error extracting text: {e}")
            self._speak(f"Failed to read PDF, {title}.")
            return ""
    
    def get_info(self, file_path: str) -> Dict[str, Any]:
        """Get PDF metadata and page count"""
        path = Path(file_path)
        
        if not path.exists() or not path.suffix.lower() == '.pdf':
            return {}
        
        try:
            info = {
                "filename": path.name,
                "size_mb": round(path.stat().st_size / (1024 * 1024), 2),
                "pages": 0,
                "title": None,
                "author": None,
            }
            
            if self.pypdf_available:
                import PyPDF2
                with open(str(path), 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    info["pages"] = len(reader.pages)
                    
                    if reader.metadata:
                        info["title"] = reader.metadata.get('/Title')
                        info["author"] = reader.metadata.get('/Author')
            
            return info
            
        except Exception as e:
            print(f"[PDF] Error getting info: {e}")
            return {}
    
    def summarize(self, file_path: str, max_pages: int = 10) -> str:
        """
        Summarize a PDF using AI.
        
        Args:
            file_path: Path to PDF file
            max_pages: Maximum pages to read for summary
            
        Returns:
            Summary text
        """
        title = self._get_title()
        
        # Extract text first
        text = self.extract_text(file_path, max_pages=max_pages)
        
        if not text:
            return "Could not extract text from PDF."
        
        # Get PDF info
        info = self.get_info(file_path)
        pages = info.get('pages', 'unknown')
        
        self._speak(f"Summarizing {pages} page PDF, {title}.")
        
        # Use decision engine for AI summarization
        if self.decision_engine and hasattr(self.decision_engine, 'summarize'):
            try:
                summary = self.decision_engine.summarize(text)
                return summary
            except Exception as e:
                print(f"[PDF] AI summarization error: {e}")
        
        # Fallback: Simple extractive summary (first and last paragraphs)
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        if len(paragraphs) <= 3:
            return text[:1000]  # Return first 1000 chars for short PDFs
        
        # Take first 2 and last paragraph as summary
        summary = (
            f"**PDF: {info.get('filename', 'Unknown')}** ({pages} pages)\n\n"
            f"{paragraphs[0]}\n\n"
            f"{paragraphs[1]}\n\n"
            f"...\n\n"
            f"{paragraphs[-1]}"
        )
        
        return summary
    
    def find_pdfs(self, directory: str = None, recent: int = 5) -> list:
        """Find recent PDF files in a directory"""
        search_dir = Path(directory) if directory else Path.home() / "Documents"
        
        if not search_dir.exists():
            return []
        
        try:
            pdfs = sorted(
                search_dir.rglob("*.pdf"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            return pdfs[:recent]
        except Exception as e:
            print(f"[PDF] Error finding PDFs: {e}")
            return []
