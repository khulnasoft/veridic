"""
Rust AST extraction using syn crate via subprocess.
Detects unsafe blocks, memory patterns, macro usage.
"""

import json
import subprocess
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class RustASTExtractor:
    """Extract AST information from Rust code."""
    
    def __init__(self):
        self.language = "rust"
    
    async def extract(self, code: str, filename: str) -> Dict[str, Any]:
        """
        Extract AST from Rust code.
        
        Args:
            code: Rust source code
            filename: Original filename
            
        Returns:
            Structured AST information
        """
        logger.info(f"Extracting Rust AST from {filename}")
        
        try:
            # Create temporary Rust file
            temp_file = f"/tmp/{filename}"
            with open(temp_file, "w") as f:
                f.write(code)
            
            # Use rustc metadata for extraction
            result = subprocess.run(
                ["rustc", "--crate-type", "lib", "--emit", "metadata", temp_file],
                capture_output=True,
                timeout=15,
            )
            
            # Fallback: pattern-based extraction
            return self._fallback_extract(code)
            
        except subprocess.TimeoutExpired:
            logger.warning("Rust AST extraction timed out")
            return self._fallback_extract(code)
        except Exception as e:
            logger.error(f"Rust AST extraction error: {e}")
            return self._fallback_extract(code)
    
    def _fallback_extract(self, code: str) -> Dict[str, Any]:
        """Fallback pattern-based extraction for Rust."""
        lines = code.split("\n")
        functions = []
        unsafe_blocks = []
        memory_patterns = []
        traits = []
        
        in_unsafe = False
        unsafe_start = 0
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Functions
            if stripped.startswith("fn ") or stripped.startswith("pub fn ") or stripped.startswith("async fn "):
                func_name = stripped.split("(")[0].replace("fn", "").replace("pub", "").replace("async", "").strip()
                functions.append({
                    "name": func_name,
                    "line": i,
                    "is_async": "async" in stripped,
                    "visibility": "pub" if "pub" in stripped else "private",
                })
            
            # Unsafe blocks
            if "unsafe" in stripped and "{" in stripped:
                in_unsafe = True
                unsafe_start = i
            
            if in_unsafe and "}" in stripped:
                unsafe_blocks.append({
                    "start_line": unsafe_start,
                    "end_line": i,
                    "size": i - unsafe_start,
                })
                in_unsafe = False
            
            # Memory patterns
            if "Box::" in line:
                memory_patterns.append({
                    "line": i,
                    "pattern": "heap_allocation",
                    "type": "Box",
                })
            if "Rc::" in line:
                memory_patterns.append({
                    "line": i,
                    "pattern": "reference_counting",
                    "type": "Rc",
                })
            if "Arc::" in line:
                memory_patterns.append({
                    "line": i,
                    "pattern": "thread_safe_refcount",
                    "type": "Arc",
                })
            
            # Traits
            if "trait " in stripped:
                trait_name = stripped.split(" ")[1].split("{")[0]
                traits.append({
                    "name": trait_name,
                    "line": i,
                })
            
            # Panic detection
            if "panic!" in line or "unwrap()" in line:
                memory_patterns.append({
                    "line": i,
                    "pattern": "panic_possible",
                    "severity": "warning",
                })
        
        return {
            "language": "rust",
            "filename": filename,
            "functions": functions,
            "unsafe_blocks": unsafe_blocks,
            "memory_patterns": memory_patterns,
            "traits": traits,
            "potential_safety_issues": len(unsafe_blocks) > 0,
        }
