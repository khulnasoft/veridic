"""
Python AST extraction using ast module and astroid for advanced analysis.
Extracts functions, classes, variables, imports, and dataflow.
"""

import ast
import logging
from typing import List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PyFunction:
    name: str
    line: int
    parameters: List[str]
    decorators: List[str]
    calls: List[str]
    uses_external: bool


@dataclass
class PyVariable:
    name: str
    line: int
    type_hint: str
    mutable: bool


class PythonASTExtractor:
    """Extract AST information from Python code."""
    
    def __init__(self):
        self.language = "python"
    
    async def extract(self, code: str, filename: str) -> Dict[str, Any]:
        """
        Extract AST from Python code.
        
        Args:
            code: Python source code
            filename: Original filename
            
        Returns:
            Structured AST information
        """
        logger.info(f"Extracting Python AST from {filename}")
        
        try:
            tree = ast.parse(code)
            functions = []
            variables = []
            classes = []
            imports = []
            
            for node in ast.walk(tree):
                # Functions
                if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    params = [arg.arg for arg in node.args.args]
                    decorators = [self._get_decorator_name(d) for d in node.decorator_list]
                    calls = self._find_calls_in_function(node)
                    
                    functions.append(PyFunction(
                        name=node.name,
                        line=node.lineno,
                        parameters=params,
                        decorators=decorators,
                        calls=calls,
                        uses_external=any(c.startswith("external_") for c in calls),
                    ).__dict__)
                
                # Variables
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            variables.append(PyVariable(
                                name=target.id,
                                line=node.lineno,
                                type_hint="",
                                mutable=True,
                            ).__dict__)
                
                # Classes
                elif isinstance(node, ast.ClassDef):
                    classes.append({
                        "name": node.name,
                        "line": node.lineno,
                        "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                    })
                
                # Imports
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({
                            "type": "import",
                            "module": alias.name,
                            "line": node.lineno,
                        })
                elif isinstance(node, ast.ImportFrom):
                    imports.append({
                        "type": "from",
                        "module": node.module or "",
                        "names": [alias.name for alias in node.names],
                        "line": node.lineno,
                    })
            
            return {
                "language": "python",
                "filename": filename,
                "functions": functions,
                "variables": variables,
                "classes": classes,
                "imports": imports,
                "dataflow": self._extract_dataflow(tree),
            }
            
        except SyntaxError as e:
            logger.error(f"Python syntax error: {e}")
            return self._fallback_extract(code)
        except Exception as e:
            logger.error(f"Python AST extraction error: {e}")
            return self._fallback_extract(code)
    
    def _find_calls_in_function(self, func_node: ast.FunctionDef) -> List[str]:
        """Find all function calls within a function."""
        calls = []
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    calls.append(node.func.attr)
        return list(set(calls))  # Deduplicate
    
    def _get_decorator_name(self, decorator: ast.expr) -> str:
        """Extract decorator name from AST node."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
        return "unknown"
    
    def _extract_dataflow(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract variable dataflow (definitions and uses)."""
        dataflow = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        dataflow.append({
                            "type": "definition",
                            "variable": target.id,
                            "line": node.lineno,
                        })
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                dataflow.append({
                    "type": "use",
                    "variable": node.id,
                    "line": node.lineno,
                })
        
        return dataflow
    
    def _fallback_extract(self, code: str) -> Dict[str, Any]:
        """Fallback line-based extraction for Python."""
        lines = code.split("\n")
        functions = []
        variables = []
        
        for i, line in enumerate(lines, 1):
            if line.strip().startswith("def "):
                func_name = line.split("(")[0].replace("def ", "").strip()
                functions.append({
                    "name": func_name,
                    "line": i,
                    "parameters": [],
                    "decorators": [],
                    "calls": [],
                    "uses_external": False,
                })
            elif "=" in line and not line.strip().startswith("#"):
                var_name = line.split("=")[0].strip()
                variables.append({
                    "name": var_name,
                    "line": i,
                    "type_hint": "",
                    "mutable": True,
                })
        
        return {
            "language": "python",
            "functions": functions,
            "variables": variables,
            "dataflow": [],
            "imports": [],
        }
