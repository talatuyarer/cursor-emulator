import asyncio
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..state.validators import ValidationError


class SearchResult:
    """Represents a single search result"""
    
    def __init__(self, file_path: str, line_number: int, content: str, 
                 context_before: str = "", context_after: str = "", 
                 relevance_score: float = 0.0, match_type: str = "exact"):
        self.file_path = file_path
        self.line_number = line_number
        self.content = content
        self.context_before = context_before
        self.context_after = context_after
        self.relevance_score = relevance_score
        self.match_type = match_type
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "content": self.content,
            "context_before": self.context_before,
            "context_after": self.context_after,
            "relevance_score": self.relevance_score,
            "match_type": self.match_type
        }


class QueryAnalyzer:
    """Analyzes natural language queries and extracts search patterns"""
    
    # Common programming patterns and their search terms
    PATTERNS = {
        # Authentication & Security
        "authentication": ["auth", "login", "password", "token", "jwt", "session", "credential"],
        "authorization": ["permission", "role", "access", "grant", "deny", "rbac", "acl"],
        "security": ["security", "encrypt", "hash", "secure", "vulnerability", "attack"],
        
        # Database & Data
        "database": ["database", "db", "sql", "query", "table", "model", "schema", "migration"],
        "data": ["data", "store", "save", "load", "fetch", "retrieve", "persist"],
        "api": ["api", "endpoint", "route", "request", "response", "rest", "graphql"],
        
        # Error Handling
        "error": ["error", "exception", "fail", "catch", "try", "throw", "handle"],
        "logging": ["log", "debug", "info", "warn", "error", "trace", "audit"],
        
        # Configuration & Setup
        "config": ["config", "setting", "option", "parameter", "environment", "env"],
        "initialization": ["init", "setup", "startup", "bootstrap", "initialize", "create"],
        
        # Testing
        "test": ["test", "spec", "mock", "stub", "fixture", "assert", "expect"],
        "validation": ["validate", "check", "verify", "confirm", "assert", "test"],
        
        # UI & Frontend
        "ui": ["ui", "component", "view", "template", "render", "display", "show"],
        "frontend": ["frontend", "client", "browser", "dom", "html", "css", "javascript"],
        
        # Backend & Services
        "backend": ["backend", "server", "service", "controller", "handler", "middleware"],
        "service": ["service", "microservice", "api", "endpoint", "handler", "controller"],
        
        # File & I/O
        "file": ["file", "upload", "download", "read", "write", "stream", "buffer"],
        "io": ["io", "input", "output", "stream", "buffer", "pipe", "channel"],
        
        # Performance & Optimization
        "performance": ["performance", "optimize", "cache", "memory", "speed", "fast"],
        "cache": ["cache", "memoize", "store", "buffer", "redis", "memory"],
        
        # Networking
        "network": ["network", "http", "tcp", "udp", "socket", "connection", "request"],
        "communication": ["communicate", "message", "event", "signal", "notify", "broadcast"],
    }
    
    # File type patterns
    FILE_PATTERNS = {
        "python": [".py"],
        "javascript": [".js", ".jsx"],
        "typescript": [".ts", ".tsx"],
        "java": [".java"],
        "go": [".go"],
        "rust": [".rs"],
        "cpp": [".cpp", ".cc", ".cxx", ".hpp", ".h"],
        "c": [".c", ".h"],
        "php": [".php"],
        "ruby": [".rb"],
        "swift": [".swift"],
        "kotlin": [".kt"],
        "scala": [".scala"],
        "html": [".html", ".htm"],
        "css": [".css", ".scss", ".sass"],
        "json": [".json"],
        "yaml": [".yaml", ".yml"],
        "xml": [".xml"],
        "markdown": [".md", ".markdown"],
        "text": [".txt"],
        "config": [".conf", ".cfg", ".ini", ".toml", ".properties"],
    }
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze natural language query and extract search patterns"""
        query_lower = query.lower()
        
        # Extract file types if mentioned
        file_types = []
        for lang, extensions in self.FILE_PATTERNS.items():
            if lang in query_lower:
                file_types.extend(extensions)
        
        # Extract search terms based on patterns
        search_terms = []
        pattern_matches = {}
        
        for pattern, terms in self.PATTERNS.items():
            if pattern in query_lower:
                search_terms.extend(terms)
                pattern_matches[pattern] = terms
        
        # Extract direct keywords (words that look like code terms)
        direct_keywords = self._extract_direct_keywords(query)
        search_terms.extend(direct_keywords)
        
        # Remove duplicates and empty strings
        search_terms = list(set([term for term in search_terms if term.strip()]))
        
        return {
            "original_query": query,
            "search_terms": search_terms,
            "file_types": file_types,
            "pattern_matches": pattern_matches,
            "direct_keywords": direct_keywords,
            "query_type": self._classify_query_type(query_lower)
        }
    
    def _extract_direct_keywords(self, query: str) -> List[str]:
        """Extract direct keywords that look like code terms"""
        # Find words that look like function names, class names, etc.
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', query)
        
        # Filter for code-like terms
        code_keywords = []
        for word in words:
            if (len(word) > 2 and 
                not word.lower() in ['the', 'and', 'or', 'but', 'for', 'with', 'how', 'what', 'where', 'when', 'why']):
                code_keywords.append(word)
        
        return code_keywords
    
    def _classify_query_type(self, query: str) -> str:
        """Classify the type of query"""
        if any(word in query for word in ['how', 'does', 'work', 'implement']):
            return "how"
        elif any(word in query for word in ['where', 'find', 'locate']):
            return "where"
        elif any(word in query for word in ['what', 'is', 'are']):
            return "what"
        elif any(word in query for word in ['why', 'cause', 'reason']):
            return "why"
        else:
            return "general"


class FileAnalyzer:
    """Analyzes file contents and extracts context"""
    
    def __init__(self):
        self.code_file_extensions = {
            '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.go', '.rs', 
            '.cpp', '.cc', '.cxx', '.hpp', '.h', '.c', '.php', '.rb', 
            '.swift', '.kt', '.scala', '.html', '.css', '.scss', '.sass'
        }
    
    def is_code_file(self, file_path: Path) -> bool:
        """Check if file is a code file"""
        return file_path.suffix.lower() in self.code_file_extensions
    
    def extract_file_context(self, file_path: Path, line_number: int, 
                           context_lines: int = 3) -> Tuple[str, str, str]:
        """Extract context around a specific line"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            if line_number < 1 or line_number > len(lines):
                return "", "", ""
            
            # Get the target line (0-indexed)
            target_line = lines[line_number - 1].strip()
            
            # Get context before
            start_line = max(0, line_number - 1 - context_lines)
            context_before = ''.join(lines[start_line:line_number - 1]).strip()
            
            # Get context after
            end_line = min(len(lines), line_number + context_lines)
            context_after = ''.join(lines[line_number:end_line]).strip()
            
            return context_before, target_line, context_after
            
        except Exception:
            return "", "", ""
    
    def analyze_file_structure(self, file_path: Path) -> Dict[str, Any]:
        """Analyze file structure and extract metadata"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Basic file analysis
            lines = content.split('\n')
            total_lines = len(lines)
            non_empty_lines = len([line for line in lines if line.strip()])
            
            # Extract imports/dependencies
            imports = []
            if file_path.suffix == '.py':
                imports = re.findall(r'^(?:from\s+\S+\s+)?import\s+(\S+)', content, re.MULTILINE)
            elif file_path.suffix in ['.js', '.jsx', '.ts', '.tsx']:
                imports = re.findall(r'import\s+(?:.*\s+from\s+)?[\'"]([^\'"]+)[\'"]', content)
            
            # Extract function/class definitions
            definitions = []
            if file_path.suffix == '.py':
                definitions.extend(re.findall(r'^def\s+(\w+)', content, re.MULTILINE))
                definitions.extend(re.findall(r'^class\s+(\w+)', content, re.MULTILINE))
            elif file_path.suffix in ['.js', '.jsx', '.ts', '.tsx']:
                definitions.extend(re.findall(r'function\s+(\w+)', content))
                definitions.extend(re.findall(r'class\s+(\w+)', content))
                definitions.extend(re.findall(r'const\s+(\w+)\s*=', content))
            
            return {
                "total_lines": total_lines,
                "non_empty_lines": non_empty_lines,
                "imports": imports,
                "definitions": definitions,
                "file_size": len(content)
            }
            
        except Exception:
            return {"total_lines": 0, "non_empty_lines": 0, "imports": [], "definitions": [], "file_size": 0}


class CodebaseSearcher:
    """Main codebase search engine"""
    
    def __init__(self):
        self.query_analyzer = QueryAnalyzer()
        self.file_analyzer = FileAnalyzer()
    
    async def search(self, query: str, target_directories: Optional[List[str]] = None, 
                    max_results: int = 20) -> List[SearchResult]:
        """Perform codebase search"""
        # Analyze the query
        analysis = self.query_analyzer.analyze_query(query)
        
        # Determine search directories
        if target_directories is None:
            target_directories = ["."]
        
        # Convert to Path objects
        search_dirs = [Path(d).resolve() for d in target_directories]
        
        # Perform searches
        results = []
        
        # 1. Exact text search
        exact_results = await self._exact_text_search(analysis, search_dirs)
        results.extend(exact_results)
        
        # 2. Pattern-based search
        pattern_results = await self._pattern_search(analysis, search_dirs)
        results.extend(pattern_results)
        
        # 3. File-based search
        file_results = await self._file_based_search(analysis, search_dirs)
        results.extend(file_results)
        
        # Remove duplicates and rank results
        unique_results = self._deduplicate_results(results)
        ranked_results = self._rank_results(unique_results, analysis)
        
        return ranked_results[:max_results]
    
    async def _exact_text_search(self, analysis: Dict[str, Any], 
                               search_dirs: List[Path]) -> List[SearchResult]:
        """Perform exact text search using grep"""
        results = []
        
        for term in analysis["search_terms"]:
            for search_dir in search_dirs:
                if not search_dir.exists():
                    continue
                
                try:
                    # Use grep to search for exact matches
                    cmd = [
                        "grep", "-r", "-n", "-i", 
                        "--include=*.py", "--include=*.js", "--include=*.ts",
                        "--include=*.java", "--include=*.go", "--include=*.rs",
                        "--include=*.cpp", "--include=*.h", "--include=*.c",
                        term, str(search_dir)
                    ]
                    
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    stdout, stderr = await process.communicate()
                    
                    if process.returncode == 0:
                        lines = stdout.decode('utf-8', errors='ignore').split('\n')
                        for line in lines:
                            if ':' in line:
                                parts = line.split(':', 2)
                                if len(parts) >= 3:
                                    file_path = parts[0]
                                    line_number = int(parts[1])
                                    content = parts[2].strip()
                                    
                                    # Extract context
                                    context_before, target_line, context_after = self.file_analyzer.extract_file_context(
                                        Path(file_path), line_number
                                    )
                                    
                                    results.append(SearchResult(
                                        file_path=file_path,
                                        line_number=line_number,
                                        content=target_line,
                                        context_before=context_before,
                                        context_after=context_after,
                                        relevance_score=0.8,  # High score for exact matches
                                        match_type="exact"
                                    ))
                
                except Exception:
                    continue
        
        return results
    
    async def _pattern_search(self, analysis: Dict[str, Any], 
                            search_dirs: List[Path]) -> List[SearchResult]:
        """Perform pattern-based search"""
        results = []
        
        # Search for pattern-related terms
        for pattern, terms in analysis["pattern_matches"].items():
            for term in terms:
                for search_dir in search_dirs:
                    if not search_dir.exists():
                        continue
                    
                    try:
                        # Search for the term in code files
                        for file_path in search_dir.rglob("*"):
                            if (file_path.is_file() and 
                                self.file_analyzer.is_code_file(file_path)):
                                
                                try:
                                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        lines = f.readlines()
                                    
                                    for i, line in enumerate(lines, 1):
                                        if term.lower() in line.lower():
                                            context_before, target_line, context_after = self.file_analyzer.extract_file_context(
                                                file_path, i
                                            )
                                            
                                            results.append(SearchResult(
                                                file_path=str(file_path),
                                                line_number=i,
                                                content=target_line,
                                                context_before=context_before,
                                                context_after=context_after,
                                                relevance_score=0.6,  # Medium score for pattern matches
                                                match_type="pattern"
                                            ))
                                
                                except Exception:
                                    continue
                    
                    except Exception:
                        continue
        
        return results
    
    async def _file_based_search(self, analysis: Dict[str, Any], 
                               search_dirs: List[Path]) -> List[SearchResult]:
        """Perform file-based search (search in filenames and structure)"""
        results = []
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            
            try:
                for file_path in search_dir.rglob("*"):
                    if file_path.is_file() and self.file_analyzer.is_code_file(file_path):
                        # Check if filename matches search terms
                        filename = file_path.name.lower()
                        file_stem = file_path.stem.lower()
                        
                        for term in analysis["search_terms"]:
                            if term.lower() in filename or term.lower() in file_stem:
                                # Get file structure
                                structure = self.file_analyzer.analyze_file_structure(file_path)
                                
                                # Create a result for the file
                                results.append(SearchResult(
                                    file_path=str(file_path),
                                    line_number=1,
                                    content=f"File: {file_path.name}",
                                    context_before="",
                                    context_after=f"Definitions: {', '.join(structure['definitions'][:5])}",
                                    relevance_score=0.4,  # Lower score for filename matches
                                    match_type="filename"
                                ))
                                break
            
            except Exception:
                continue
        
        return results
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results"""
        seen = set()
        unique_results = []
        
        for result in results:
            key = (result.file_path, result.line_number, result.content)
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        return unique_results
    
    def _rank_results(self, results: List[SearchResult], 
                     analysis: Dict[str, Any]) -> List[SearchResult]:
        """Rank results by relevance"""
        def calculate_score(result: SearchResult) -> float:
            score = result.relevance_score
            
            # Boost score for exact matches in important files
            if result.match_type == "exact":
                score += 0.2
            
            # Boost score for main files vs test files
            if "test" not in result.file_path.lower():
                score += 0.1
            
            # Boost score for shorter file paths (likely main files)
            path_depth = len(Path(result.file_path).parts)
            score += max(0, 0.1 - (path_depth * 0.01))
            
            return score
        
        # Sort by calculated score
        return sorted(results, key=calculate_score, reverse=True)


async def codebase_search(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform semantic codebase search.
    
    Parameters:
        params: Dictionary containing:
            - query: Natural language search query (required)
            - target_directories: List of directories to search (optional)
            - max_results: Maximum number of results (optional, defaults to 20)
    
    Returns:
        Dictionary with search results and metadata
    """
    # Validate params structure
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
        searcher = CodebaseSearcher()
        results = await searcher.search(query, target_directories, max_results)
        
        # Convert results to dictionaries
        results_dict = [result.to_dict() for result in results]
        
        # Calculate summary statistics
        total_results = len(results_dict)
        exact_matches = len([r for r in results_dict if r["match_type"] == "exact"])
        pattern_matches = len([r for r in results_dict if r["match_type"] == "pattern"])
        filename_matches = len([r for r in results_dict if r["match_type"] == "filename"])
        
        # Get unique files
        unique_files = list(set(r["file_path"] for r in results_dict))
        
        return {
            "success": True,
            "query": query,
            "total_results": total_results,
            "exact_matches": exact_matches,
            "pattern_matches": pattern_matches,
            "filename_matches": filename_matches,
            "unique_files": len(unique_files),
            "results": results_dict,
            "target_directories": target_directories or ["."],
            "max_results": max_results
        }
        
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Codebase search failed: {str(e)}")
