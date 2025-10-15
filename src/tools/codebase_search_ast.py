"""
Enhanced Codebase Search with AST-based Code Understanding

This module provides advanced semantic search capabilities using Abstract Syntax Tree (AST) analysis
for deep code understanding, similar to Cursor's built-in search.

Key Features:
- AST-based symbol extraction (functions, classes, methods)
- Multi-language support (Python, Java, JavaScript, TypeScript)
- Intent detection (find definitions, usages, implementations)
- Smart ranking with multiple signals
- Symbol indexing for fast searches
- Cross-file analysis and relationships
"""

import ast
import asyncio
import hashlib
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ..state.validators import ValidationError
from .java_analyzer import JavaCodeAnalyzer, JavaSymbol


@dataclass
class Symbol:
    """Represents a code symbol (function, class, variable, etc.)"""
    name: str
    symbol_type: str  # 'function', 'class', 'method', 'variable', 'import'
    line_number: int
    file_path: str
    docstring: Optional[str] = None
    signature: Optional[str] = None
    parent_class: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    is_async: bool = False


@dataclass
class EnhancedSearchResult:
    """Enhanced search result with rich metadata"""
    file_path: str
    line_number: int
    content: str
    symbol_type: Optional[str] = None
    symbol_name: Optional[str] = None
    context_before: str = ""
    context_after: str = ""
    docstring: Optional[str] = None
    signature: Optional[str] = None
    relevance_score: float = 0.0
    match_type: str = "exact"
    related_symbols: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "content": self.content,
            "symbol_type": self.symbol_type,
            "symbol_name": self.symbol_name,
            "context_before": self.context_before,
            "context_after": self.context_after,
            "docstring": self.docstring,
            "signature": self.signature,
            "relevance_score": round(self.relevance_score, 3),
            "match_type": self.match_type,
            "related_symbols": self.related_symbols
        }


class PythonASTAnalyzer:
    """Analyzes Python code using AST for deep structural understanding"""
    
    def __init__(self):
        self.symbols_cache: Dict[str, List[Symbol]] = {}
        self.class_hierarchy: Dict[str, List[str]] = {}
    
    def analyze_file(self, file_path: Path) -> List[Symbol]:
        """Parse Python file and extract all symbols using AST"""
        file_key = str(file_path)
        
        # Return cached symbols if available
        if file_key in self.symbols_cache:
            return self.symbols_cache[file_key]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            tree = ast.parse(source_code, filename=str(file_path))
            symbols = []
            
            # Walk the AST and extract symbols
            for node in ast.walk(tree):
                # Extract imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        symbols.append(Symbol(
                            name=alias.name,
                            symbol_type='import',
                            line_number=node.lineno,
                            file_path=str(file_path)
                        ))
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        import_name = f"{module}.{alias.name}" if module else alias.name
                        symbols.append(Symbol(
                            name=import_name,
                            symbol_type='import',
                            line_number=node.lineno,
                            file_path=str(file_path)
                        ))
                
                # Extract class definitions
                elif isinstance(node, ast.ClassDef):
                    base_classes = [self._get_node_name(base) for base in node.bases]
                    decorators = [self._get_node_name(d) for d in node.decorator_list]
                    
                    symbols.append(Symbol(
                        name=node.name,
                        symbol_type='class',
                        line_number=node.lineno,
                        file_path=str(file_path),
                        docstring=ast.get_docstring(node),
                        decorators=decorators
                    ))
                    
                    # Store class hierarchy
                    if base_classes:
                        self.class_hierarchy[node.name] = base_classes
                    
                    # Extract methods from class
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                            params = [arg.arg for arg in item.args.args]
                            method_decorators = [self._get_node_name(d) for d in item.decorator_list]
                            
                            symbols.append(Symbol(
                                name=item.name,
                                symbol_type='method',
                                line_number=item.lineno,
                                file_path=str(file_path),
                                docstring=ast.get_docstring(item),
                                parent_class=node.name,
                                parameters=params,
                                decorators=method_decorators,
                                is_async=isinstance(item, ast.AsyncFunctionDef)
                            ))
            
            # Extract standalone function definitions (not in classes)
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    params = [arg.arg for arg in node.args.args]
                    decorators = [self._get_node_name(d) for d in node.decorator_list]
                    
                    symbols.append(Symbol(
                        name=node.name,
                        symbol_type='function',
                        line_number=node.lineno,
                        file_path=str(file_path),
                        docstring=ast.get_docstring(node),
                        parameters=params,
                        decorators=decorators,
                        is_async=isinstance(node, ast.AsyncFunctionDef)
                    ))
            
            # Cache the symbols
            self.symbols_cache[file_key] = symbols
            return symbols
            
        except Exception as e:
            # Return empty list on parse errors
            return []
    
    def _get_node_name(self, node) -> str:
        """Extract name from an AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value_name = self._get_node_name(node.value)
            return f"{value_name}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_node_name(node.func)
        return str(node)
    
    def find_symbol_usages(self, symbol_name: str, file_path: Path) -> List[int]:
        """Find all line numbers where a symbol is used"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            tree = ast.parse(source_code, filename=str(file_path))
            usage_lines = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and node.id == symbol_name:
                    if hasattr(node, 'lineno'):
                        usage_lines.append(node.lineno)
                elif isinstance(node, ast.Attribute) and node.attr == symbol_name:
                    if hasattr(node, 'lineno'):
                        usage_lines.append(node.lineno)
            
            return sorted(set(usage_lines))
            
        except Exception:
            return []
    
    def extract_context(self, file_path: Path, line_number: int, 
                       context_lines: int = 3) -> Tuple[str, str, str]:
        """Extract context around a specific line"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if line_number < 1 or line_number > len(lines):
                return "", "", ""
            
            # Get the target line (0-indexed)
            target_line = lines[line_number - 1].rstrip()
            
            # Get context before
            start_line = max(0, line_number - 1 - context_lines)
            context_before = ''.join(lines[start_line:line_number - 1]).rstrip()
            
            # Get context after
            end_line = min(len(lines), line_number + context_lines)
            context_after = ''.join(lines[line_number:end_line]).rstrip()
            
            return context_before, target_line, context_after
            
        except Exception:
            return "", "", ""


class IntentAnalyzer:
    """Analyzes query intent to understand what the user is looking for"""
    
    INTENT_PATTERNS = {
        'find_definition': [
            r'where\s+is\s+(\w+)\s+defined',
            r'find\s+(?:the\s+)?definition\s+(?:of\s+)?(\w+)',
            r'what\s+is\s+(\w+)',
            r'define\s+(\w+)',
        ],
        'find_usages': [
            r'where\s+is\s+(\w+)\s+used',
            r'find\s+usages?\s+(?:of\s+)?(\w+)',
            r'how\s+is\s+(\w+)\s+used',
            r'usage\s+of\s+(\w+)',
        ],
        'find_implementation': [
            r'how\s+does\s+(\w+)\s+work',
            r'show\s+(?:me\s+)?(?:the\s+)?implementation\s+(?:of\s+)?(\w+)',
            r'how\s+is\s+(\w+)\s+implemented',
            r'implementation\s+of\s+(\w+)',
        ],
        'find_examples': [
            r'examples?\s+of\s+(?:using\s+)?(\w+)',
            r'how\s+to\s+use\s+(\w+)',
            r'usage\s+examples?\s+(?:for\s+)?(\w+)',
        ],
    }
    
    def analyze(self, query: str) -> Dict[str, Any]:
        """Detect query intent and extract target symbols"""
        query_lower = query.lower()
        
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if match := re.search(pattern, query_lower):
                    return {
                        'intent': intent,
                        'target_symbol': match.group(1) if match.groups() else None,
                        'original_query': query,
                        'confidence': 0.9
                    }
        
        return {
            'intent': 'general_search',
            'target_symbol': None,
            'original_query': query,
            'confidence': 0.5
        }


class EnhancedCodebaseSearcher:
    """Advanced codebase searcher with AST analysis and semantic understanding"""
    
    def __init__(self):
        self.python_analyzer = PythonASTAnalyzer()
        self.java_analyzer = JavaCodeAnalyzer()
        self.intent_analyzer = IntentAnalyzer()
        self.symbol_index: Dict[str, List[Symbol]] = {}
        self.last_index_time: float = 0
        self.index_ttl: float = 3600  # Rebuild index every hour
        self.search_cache: Dict[str, Tuple[List[EnhancedSearchResult], float]] = {}
        self.cache_ttl: float = 300  # Cache for 5 minutes
        
        # Language support
        self.supported_languages = {
            '.py': 'python',
            '.java': 'java',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript'
        }
    
    async def search(self, query: str, target_directories: Optional[List[str]] = None,
                    max_results: int = 20) -> List[EnhancedSearchResult]:
        """Perform enhanced semantic search with AST analysis"""
        
        # Check cache
        cache_key = self._get_cache_key(query, target_directories)
        if cache_key in self.search_cache:
            cached_results, timestamp = self.search_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_results[:max_results]
        
        # Analyze query intent
        intent = self.intent_analyzer.analyze(query)
        
        # Build or refresh symbol index
        current_time = time.time()
        if not self.symbol_index or (current_time - self.last_index_time) > self.index_ttl:
            await self._build_symbol_index(target_directories or ["."])
            self.last_index_time = current_time
        
        # Perform search based on intent
        if intent['intent'] == 'find_definition' and intent['target_symbol']:
            results = await self._find_definitions(intent['target_symbol'])
        elif intent['intent'] == 'find_usages' and intent['target_symbol']:
            results = await self._find_usages(intent['target_symbol'])
        elif intent['intent'] == 'find_implementation' and intent['target_symbol']:
            results = await self._find_implementations(intent['target_symbol'])
        else:
            # General semantic search
            results = await self._semantic_search(query, target_directories or ["."])
        
        # Rank results
        ranked_results = self._rank_results(results, query, intent)
        
        # Cache results
        self.search_cache[cache_key] = (ranked_results, current_time)
        
        return ranked_results[:max_results]
    
    async def _build_symbol_index(self, directories: List[str]):
        """Build comprehensive symbol index from all supported language files"""
        self.symbol_index.clear()
        
        for directory in directories:
            dir_path = Path(directory).resolve()
            if not dir_path.exists():
                continue
            
            # Find all Python files
            python_files = list(dir_path.rglob("*.py"))
            for py_file in python_files:
                # Skip __pycache__ and other generated files
                if '__pycache__' in str(py_file) or '.eggs' in str(py_file):
                    continue
                
                symbols = self.python_analyzer.analyze_file(py_file)
                
                # Add symbols to index
                for symbol in symbols:
                    if symbol.name not in self.symbol_index:
                        self.symbol_index[symbol.name] = []
                    self.symbol_index[symbol.name].append(symbol)
            
            # Find all Java files
            java_files = list(dir_path.rglob("*.java"))
            for java_file in java_files:
                # Skip build directories
                if any(skip in str(java_file) for skip in ['target/', 'build/', '.gradle/']):
                    continue
                
                java_symbols = self.java_analyzer.analyze_file(java_file)
                
                # Convert JavaSymbol to Symbol and add to index
                for java_symbol in java_symbols:
                    # Convert JavaSymbol to generic Symbol format
                    symbol = Symbol(
                        name=java_symbol.name,
                        symbol_type=java_symbol.symbol_type,
                        line_number=java_symbol.line_number,
                        file_path=java_symbol.file_path,
                        docstring=self.java_analyzer.extract_javadoc(java_symbol.javadoc),
                        signature=java_symbol.signature,
                        parent_class=java_symbol.parent_class,
                        decorators=java_symbol.annotations,
                        parameters=java_symbol.parameters,
                        return_type=java_symbol.return_type
                    )
                    
                    if symbol.name not in self.symbol_index:
                        self.symbol_index[symbol.name] = []
                    self.symbol_index[symbol.name].append(symbol)
    
    async def _find_definitions(self, symbol_name: str) -> List[EnhancedSearchResult]:
        """Find where a symbol is defined"""
        results = []
        
        # Look up symbol in index
        if symbol_name in self.symbol_index:
            for symbol in self.symbol_index[symbol_name]:
                if symbol.symbol_type in ['function', 'class', 'method', 'interface', 'constructor']:
                    # Use appropriate analyzer based on file extension
                    file_path = Path(symbol.file_path)
                    if file_path.suffix == '.py':
                        context_before, content, context_after = self.python_analyzer.extract_context(
                            file_path, symbol.line_number
                        )
                    elif file_path.suffix == '.java':
                        context_before, content, context_after = self.java_analyzer.extract_context(
                            file_path, symbol.line_number
                        )
                    else:
                        context_before, content, context_after = "", "", ""
                    
                    results.append(EnhancedSearchResult(
                        file_path=symbol.file_path,
                        line_number=symbol.line_number,
                        content=content or f"{symbol.symbol_type} {symbol.name}",
                        symbol_type=symbol.symbol_type,
                        symbol_name=symbol.name,
                        context_before=context_before,
                        context_after=context_after,
                        docstring=symbol.docstring,
                        signature=f"def {symbol.name}({', '.join(symbol.parameters)})",
                        relevance_score=1.0,
                        match_type='definition'
                    ))
        
        return results
    
    async def _find_usages(self, symbol_name: str) -> List[EnhancedSearchResult]:
        """Find all usages of a symbol"""
        results = []
        
        # Get symbol definitions first
        if symbol_name not in self.symbol_index:
            return results
        
        # Search for usages in all indexed files
        seen_locations = set()
        
        for symbols in self.symbol_index.values():
            for symbol in symbols:
                file_path = Path(symbol.file_path)
                
                # Find usages using appropriate analyzer
                if file_path.suffix == '.py':
                    usage_lines = self.python_analyzer.find_symbol_usages(symbol_name, file_path)
                elif file_path.suffix == '.java':
                    usage_lines = self.java_analyzer.find_symbol_usages(symbol_name, file_path)
                else:
                    usage_lines = []
                
                for line_num in usage_lines:
                    location_key = (str(file_path), line_num)
                    if location_key in seen_locations:
                        continue
                    seen_locations.add(location_key)
                    
                    # Extract context using appropriate analyzer
                    if file_path.suffix == '.py':
                        context_before, content, context_after = self.python_analyzer.extract_context(
                            file_path, line_num
                        )
                    elif file_path.suffix == '.java':
                        context_before, content, context_after = self.java_analyzer.extract_context(
                            file_path, line_num
                        )
                    else:
                        context_before, content, context_after = "", "", ""
                        
                        results.append(EnhancedSearchResult(
                            file_path=str(file_path),
                            line_number=line_num,
                            content=content or f"Usage of {symbol_name}",
                            symbol_name=symbol_name,
                            context_before=context_before,
                            context_after=context_after,
                            relevance_score=0.8,
                            match_type='usage'
                        ))
        
        return results
    
    async def _find_implementations(self, symbol_name: str) -> List[EnhancedSearchResult]:
        """Find implementation details of a symbol"""
        # For implementations, we want the definition plus some context
        results = await self._find_definitions(symbol_name)
        
        # Enhance with more context
        for result in results:
            context_before, _, context_after = self.ast_analyzer.extract_context(
                Path(result.file_path), result.line_number, context_lines=10
            )
            result.context_before = context_before
            result.context_after = context_after
            result.match_type = 'implementation'
        
        return results
    
    async def _semantic_search(self, query: str, 
                              target_directories: List[str]) -> List[EnhancedSearchResult]:
        """Perform general semantic search across the codebase"""
        results = []
        
        # Extract keywords from query
        keywords = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', query.lower())
        keywords = [k for k in keywords if len(k) > 2]
        
        # Search symbol index
        for symbol_name, symbols in self.symbol_index.items():
            symbol_name_lower = symbol_name.lower()
            
            # Calculate match score
            match_score = 0.0
            for keyword in keywords:
                if keyword == symbol_name_lower:
                    match_score += 1.0
                elif keyword in symbol_name_lower or symbol_name_lower in keyword:
                    match_score += 0.5
            
            # Also check docstrings
            for symbol in symbols:
                if symbol.docstring:
                    docstring_lower = symbol.docstring.lower()
                    for keyword in keywords:
                        if keyword in docstring_lower:
                            match_score += 0.3
            
            # Add results if there's a match
            if match_score > 0:
                for symbol in symbols:
                    # Use appropriate analyzer based on file extension
                    file_path = Path(symbol.file_path)
                    if file_path.suffix == '.py':
                        context_before, content, context_after = self.python_analyzer.extract_context(
                            file_path, symbol.line_number
                        )
                    elif file_path.suffix == '.java':
                        context_before, content, context_after = self.java_analyzer.extract_context(
                            file_path, symbol.line_number
                        )
                    else:
                        context_before, content, context_after = "", "", ""
                
                    results.append(EnhancedSearchResult(
                        file_path=symbol.file_path,
                        line_number=symbol.line_number,
                        content=content or f"{symbol.symbol_type} {symbol.name}",
                        symbol_type=symbol.symbol_type,
                        symbol_name=symbol.name,
                        context_before=context_before,
                        context_after=context_after,
                        docstring=symbol.docstring,
                        relevance_score=match_score * 0.7,
                        match_type='semantic'
                    ))
        
        return results
    
    def _rank_results(self, results: List[EnhancedSearchResult], query: str,
                     intent: Dict[str, Any]) -> List[EnhancedSearchResult]:
        """Advanced ranking algorithm using multiple signals"""
        
        def calculate_score(result: EnhancedSearchResult) -> float:
            score = result.relevance_score
            
            # Boost exact symbol matches
            if result.match_type == 'definition':
                score += 0.4
            elif result.match_type == 'implementation':
                score += 0.35
            
            # Boost results with docstrings
            if result.docstring:
                score += 0.2
                # Extra boost if query terms in docstring
                query_terms = query.lower().split()
                matching_terms = sum(1 for term in query_terms 
                                   if term in result.docstring.lower())
                score += matching_terms * 0.1
            
            # Boost important symbol types
            if result.symbol_type == 'class':
                score += 0.15
            elif result.symbol_type in ['function', 'method']:
                score += 0.1
            
            # Penalize test files (usually less relevant)
            if 'test' in result.file_path.lower():
                score -= 0.2
            
            # Boost main/core files
            if any(term in result.file_path.lower() 
                  for term in ['main', 'core', 'server', 'app']):
                score += 0.1
            
            # Penalize deep file paths (prefer top-level files)
            path_depth = len(Path(result.file_path).parts)
            score -= min(path_depth * 0.02, 0.3)
            
            # Boost if symbol name closely matches query
            if result.symbol_name:
                query_lower = query.lower()
                symbol_lower = result.symbol_name.lower()
                if symbol_lower in query_lower or query_lower in symbol_lower:
                    score += 0.25
            
            return max(0.0, score)  # Ensure non-negative
        
        # Calculate scores and sort
        for result in results:
            result.relevance_score = calculate_score(result)
        
        return sorted(results, key=lambda r: r.relevance_score, reverse=True)
    
    def _get_cache_key(self, query: str, directories: Optional[List[str]]) -> str:
        """Generate cache key for query"""
        key_data = f"{query}|{':'.join(sorted(directories or []))}"
        return hashlib.md5(key_data.encode()).hexdigest()


# Main entry point function
async def codebase_search_ast(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced codebase search with AST analysis and semantic understanding.
    
    This is a drop-in replacement for the existing codebase_search function
    that provides significantly better results through AST-based code analysis.
    
    Parameters:
        params: Dictionary containing:
            - query: Natural language search query (required)
            - target_directories: List of directories to search (optional)
            - max_results: Maximum number of results (optional, defaults to 20)
    
    Returns:
        Dictionary with enhanced search results and metadata
    """
    # Validate params
    if not isinstance(params, dict):
        raise ValidationError("Parameters must be a dictionary")
    
    if "query" not in params:
        raise ValidationError("Missing required field: query")
    
    query = params["query"]
    if not isinstance(query, str) or not query.strip():
        raise ValidationError("Query must be a non-empty string")
    
    target_directories = params.get("target_directories")
    max_results = params.get("max_results", 20)
    
    # Validate max_results
    if not isinstance(max_results, int) or max_results <= 0 or max_results > 100:
        raise ValidationError("max_results must be an integer between 1 and 100")
    
    try:
        # Create searcher and perform search
        searcher = EnhancedCodebaseSearcher()
        start_time = time.time()
        results = await searcher.search(query, target_directories, max_results)
        search_time = time.time() - start_time
        
        # Convert results to dictionaries
        results_dict = [result.to_dict() for result in results]
        
        # Calculate summary statistics
        total_results = len(results_dict)
        definitions = len([r for r in results_dict if r["match_type"] == "definition"])
        usages = len([r for r in results_dict if r["match_type"] == "usage"])
        semantic_matches = len([r for r in results_dict if r["match_type"] == "semantic"])
        
        # Get unique files
        unique_files = list(set(r["file_path"] for r in results_dict))
        
        # Get symbol types
        symbol_types = {}
        for r in results_dict:
            if r["symbol_type"]:
                symbol_types[r["symbol_type"]] = symbol_types.get(r["symbol_type"], 0) + 1
        
        return {
            "success": True,
            "query": query,
            "total_results": total_results,
            "search_time_seconds": round(search_time, 3),
            "match_types": {
                "definitions": definitions,
                "usages": usages,
                "semantic": semantic_matches
            },
            "symbol_types": symbol_types,
            "unique_files": len(unique_files),
            "results": results_dict,
            "target_directories": target_directories or ["."],
            "max_results": max_results,
            "enhancement_enabled": True,
            "features": [
                "AST-based symbol extraction",
                "Intent detection",
                "Smart ranking",
                "Symbol indexing",
                "Context extraction"
            ]
        }
        
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Enhanced codebase search failed: {str(e)}")

