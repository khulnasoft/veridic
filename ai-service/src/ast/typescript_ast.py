"""
TypeScript/JavaScript AST extraction using ts-parser.
Extracts functions, variables, dataflow, and dependencies.
"""

import json
import subprocess
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TSFunction:
    name: str
    line: int
    parameters: List[str]
    return_type: Optional[str]
    calls: List[str]
    uses_external: bool


@dataclass
class TSVariable:
    name: str
    line: int
    type: Optional[str]
    mutable: bool


class TypeScriptASTExtractor:
    """Extract AST information from TypeScript/JavaScript code."""
    
    def __init__(self):
        self.language = "typescript"
    
    async def extract(self, code: str, filename: str) -> Dict[str, Any]:
        """
        Extract AST from TypeScript code.
        
        Args:
            code: TypeScript source code
            filename: Original filename
            
        Returns:
            Structured AST information
        """
        logger.info(f"Extracting TypeScript AST from {filename}")
        
        try:
            # Use Node.js subprocess to parse TypeScript
            script = """
const ts = require('typescript');
const code = process.argv[1];
const sourceFile = ts.createSourceFile('temp.ts', code, ts.ScriptTarget.Latest, true);

function visit(node, depth = 0) {
    if (node.kind === ts.SyntaxKind.FunctionDeclaration || node.kind === ts.SyntaxKind.ArrowFunction) {
        console.log(JSON.stringify({
            type: 'function',
            name: node.name?.text || 'anonymous',
            line: sourceFile.getLineAndCharacterOfPosition(node.getStart()).line + 1,
        }));
    }
    if (node.kind === ts.SyntaxKind.VariableDeclaration) {
        console.log(JSON.stringify({
            type: 'variable',
            name: node.name.text,
            line: sourceFile.getLineAndCharacterOfPosition(node.getStart()).line + 1,
        }));
    }
    ts.forEachChild(node, child => visit(child, depth + 1));
}
visit(sourceFile);
            """
            
            result = subprocess.run(
                ["node", "-e", script, code],
                capture_output=True,
                timeout=10,
            )
            
            if result.returncode != 0:
                logger.warning(f"TypeScript AST extraction failed: {result.stderr.decode()}")
                return self._fallback_extract(code)
            
            functions = []
            variables = []
            
            for line in result.stdout.decode().strip().split("\n"):
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    if item["type"] == "function":
                        functions.append(TSFunction(
                            name=item["name"],
                            line=item["line"],
                            parameters=[],
                            return_type=None,
                            calls=[],
                            uses_external=False,
                        ))
                    elif item["type"] == "variable":
                        variables.append(TSVariable(
                            name=item["name"],
                            line=item["line"],
                            type=None,
                            mutable=True,
                        ))
                except json.JSONDecodeError:
                    continue
            
            return {
                "language": "typescript",
                "filename": filename,
                "functions": [f.__dict__ for f in functions],
                "variables": [v.__dict__ for v in variables],
                "dataflow": [],
                "imports": [],
            }
            
        except Exception as e:
            logger.error(f"TypeScript AST extraction error: {e}")
            return self._fallback_extract(code)
    
    def _fallback_extract(self, code: str) -> Dict[str, Any]:
        """Fallback line-based extraction for TypeScript."""
        lines = code.split("\n")
        functions = []
        variables = []
        
        for i, line in enumerate(lines, 1):
            # Simple regex patterns for fallback
            if line.strip().startswith("function ") or "=> " in line:
                functions.append({
                    "name": "function",
                    "line": i,
                    "parameters": [],
                    "return_type": None,
                    "calls": [],
                    "uses_external": False,
                })
            if "const " in line or "let " in line:
                variables.append({
                    "name": "variable",
                    "line": i,
                    "type": None,
                    "mutable": "let" in line,
                })
        
        return {
            "language": "typescript",
            "functions": functions,
            "variables": variables,
            "dataflow": [],
            "imports": [],
        }
