"""
PDF processing service
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add core to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent / "core"))

from ..core.models import PDFSection

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Service for processing PDF files"""
    
    def __init__(self):
        pass
    
    def process_pdf_to_sections(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """Process a PDF file into sections"""
        try:
            logger.info(f"🔄 Processing PDF: {pdf_path.name}")
            
            # Import the existing PDF processor
            from core.extract_pdf_complete import process_pdf_to_sections, get_pdf_hash
            
            # Extract printer model from filename
            printer_model = self._extract_model_from_filename(pdf_path.name)
            
            # Process PDF
            sections_data = process_pdf_to_sections(str(pdf_path), printer_model=printer_model)
            
            # Add PDF hash to all sections
            pdf_hash = get_pdf_hash(str(pdf_path))
            for section in sections_data:
                section['pdf_hash'] = pdf_hash
            
            logger.info(f"✅ Generated {len(sections_data)} sections from {pdf_path.name}")
            return sections_data
            
        except Exception as e:
            logger.error(f"❌ Failed to process {pdf_path.name}: {e}")
            return []
    
    def _extract_model_from_filename(self, filename: str) -> str:
        """Extract printer model from filename"""
        # Remove extension
        base_name = os.path.splitext(filename)[0]
        
        # Common patterns for model extraction
        import re
        
        # Try to match patterns like "impressoraL3150" -> "impressoraL3150"
        # or "ImpressoraL375" -> "ImpressoraL375"
        model_match = re.search(r'[Ii]mpressor[ao]?[Ll]?\d{3,4}(?:_[Ll]?\d{3,4})?', base_name)
        if model_match:
            return model_match.group()
        
        # Fallback: use the base filename
        return base_name
