"""
Unified AST extraction orchestrator for all languages.
"""

import logging
from typing import Dict, Any
from .typescript_ast import TypeScriptASTExtractor
from .python_ast import PythonASTExtractor
from .go_ast import GoASTExtractor
from .rust_ast import RustASTExtractor

logger = logging.getLogger(__name__)


class ASTExtractor:
    """Unified AST extraction for multiple languages."""
    
    def __init__(self):
        self.extractors = {
            "typescript": TypeScriptASTExtractor(),
            "javascript": TypeScriptASTExtractor(),
            "python": PythonASTExtractor(),
            "go": GoASTExtractor(),
            "rust": RustASTExtractor(),
        }
    
    async def extract(self, code: str, language: str, filename: str) -> Dict[str, Any]:
        """
        Extract AST from code in specified language.
        
        Args:
            code: Source code to analyze
            language: Programming language (typescript, python, go, rust)
            filename: Original filename
            
        Returns:
            Structured AST information
        """
        logger.info(f"Extracting AST for {language}: {filename}")
        
        extractor = self.extractors.get(language.lower())
        
        if not extractor:
            logger.warning(f"No AST extractor for language: {language}")
            return {
                "language": language,
                "filename": filename,
                "error": f"Unsupported language: {language}",
            }
        
        try:
            return await extractor.extract(code, filename)
        except Exception as e:
            logger.error(f"AST extraction failed for {language}: {e}")
            return {
                "language": language,
                "filename": filename,
                "error": str(e),
            }
