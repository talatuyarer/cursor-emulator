"""
Java Code Analyzer for Enhanced Codebase Search

Provides AST-like analysis for Java code using regex-based parsing.
For production use, consider integrating with JavaParser or Tree-sitter.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class JavaSymbol:
    """Represents a Java code symbol"""
    name: str
    symbol_type: str  # 'class', 'interface', 'method', 'field', 'enum', 'import'
    line_number: int
    file_path: str
    modifiers: List[str] = field(default_factory=list)  # public, private, static, etc.
    signature: Optional[str] = None
    parent_class: Optional[str] = None
    return_type: Optional[str] = None
    parameters: List[str] = field(default_factory=list)
    annotations: List[str] = field(default_factory=list)
    javadoc: Optional[str] = None
    implements: List[str] = field(default_factory=list)
    extends: Optional[str] = None


class JavaCodeAnalyzer:
    """Analyzes Java code to extract symbols and structure"""
    
    def __init__(self):
        self.symbols_cache = {}
        
        # Java modifiers
        self.modifiers = ['public', 'private', 'protected', 'static', 'final', 
                         'abstract', 'synchronized', 'native', 'volatile', 'transient']
        
        # Common Java annotations
        self.common_annotations = ['@Override', '@Deprecated', '@SuppressWarnings',
                                  '@FunctionalInterface', '@SafeVarargs', '@Autowired',
                                  '@Service', '@Repository', '@Controller', '@RestController',
                                  '@Component', '@Bean', '@Configuration', '@Entity', '@Table']
    
    def analyze_file(self, file_path: Path) -> List[JavaSymbol]:
        """Parse Java file and extract all symbols"""
        file_key = str(file_path)
        
        # Return cached symbols if available
        if file_key in self.symbols_cache:
            return self.symbols_cache[file_key]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            symbols = []
            current_class = None
            current_javadoc = None
            current_annotations = []
            
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                
                # Extract Javadoc comments
                if stripped.startswith('/**'):
                    current_javadoc = stripped
                elif current_javadoc and not stripped.startswith('*/'):
                    current_javadoc += ' ' + stripped
                elif stripped.startswith('*/'):
                    if current_javadoc:
                        current_javadoc += ' ' + stripped
                    # Javadoc complete, will be used for next symbol
                
                # Extract annotations
                if stripped.startswith('@'):
                    annotation = re.match(r'@\w+(\([^)]*\))?', stripped)
                    if annotation:
                        current_annotations.append(annotation.group())
                
                # Extract package declaration
                if match := re.match(r'package\s+([\w.]+)\s*;', stripped):
                    symbols.append(JavaSymbol(
                        name=match.group(1),
                        symbol_type='package',
                        line_number=i,
                        file_path=str(file_path)
                    ))
                
                # Extract imports
                elif match := re.match(r'import\s+(?:static\s+)?([\w.*]+)\s*;', stripped):
                    symbols.append(JavaSymbol(
                        name=match.group(1),
                        symbol_type='import',
                        line_number=i,
                        file_path=str(file_path)
                    ))
                
                # Extract class declarations
                elif match := re.match(
                    r'(?:(public|private|protected|abstract|final|static)\s+)*'
                    r'(class|interface|enum)\s+'
                    r'(\w+)'
                    r'(?:\s+extends\s+([\w.<>,\s]+))?'
                    r'(?:\s+implements\s+([\w.<>,\s]+))?',
                    stripped
                ):
                    modifiers = self._extract_modifiers(stripped)
                    class_type = match.group(2)  # class, interface, or enum
                    class_name = match.group(3)
                    extends = match.group(4)
                    implements_str = match.group(5)
                    
                    implements = []
                    if implements_str:
                        implements = [s.strip() for s in implements_str.split(',')]
                    
                    current_class = class_name
                    
                    symbols.append(JavaSymbol(
                        name=class_name,
                        symbol_type=class_type,
                        line_number=i,
                        file_path=str(file_path),
                        modifiers=modifiers,
                        signature=stripped,
                        javadoc=current_javadoc,
                        annotations=current_annotations.copy(),
                        extends=extends,
                        implements=implements
                    ))
                    
                    # Reset for next symbol
                    current_javadoc = None
                    current_annotations = []
                
                # Extract method declarations
                elif match := re.match(
                    r'(?:(public|private|protected|static|final|abstract|synchronized|native)\s+)*'
                    r'(?:<[\w\s,<>]+>\s+)?'  # Generic type parameters
                    r'([\w<>[\]]+)\s+'  # Return type
                    r'(\w+)\s*'  # Method name
                    r'\(([^)]*)\)',  # Parameters
                    stripped
                ):
                    if not any(keyword in stripped for keyword in ['class', 'interface', 'enum', 'if', 'while', 'for']):
                        modifiers = self._extract_modifiers(stripped)
                        return_type = match.group(2)
                        method_name = match.group(3)
                        params_str = match.group(4)
                        
                        # Skip constructors matching class name
                        if method_name == current_class:
                            symbol_type = 'constructor'
                        else:
                            symbol_type = 'method'
                        
                        # Parse parameters
                        parameters = self._parse_parameters(params_str)
                        
                        symbols.append(JavaSymbol(
                            name=method_name,
                            symbol_type=symbol_type,
                            line_number=i,
                            file_path=str(file_path),
                            modifiers=modifiers,
                            signature=stripped,
                            parent_class=current_class,
                            return_type=return_type,
                            parameters=parameters,
                            javadoc=current_javadoc,
                            annotations=current_annotations.copy()
                        ))
                        
                        # Reset for next symbol
                        current_javadoc = None
                        current_annotations = []
                
                # Extract field declarations
                elif current_class and re.match(
                    r'(?:(public|private|protected|static|final|transient|volatile)\s+)*'
                    r'([\w<>[\]]+)\s+'  # Type
                    r'(\w+)\s*'  # Field name
                    r'(?:=|;)',  # Assignment or end
                    stripped
                ):
                    if not any(keyword in stripped for keyword in ['class', 'interface', 'return', 'if', 'while', 'for']):
                        modifiers = self._extract_modifiers(stripped)
                        
                        # Extract type and field name
                        parts = stripped.split()
                        if len(parts) >= 2:
                            field_type = parts[-2] if parts[-2] not in self.modifiers else parts[-3]
                            field_name_match = re.search(r'\b(\w+)\s*[=;]', stripped)
                            if field_name_match:
                                field_name = field_name_match.group(1)
                                
                                symbols.append(JavaSymbol(
                                    name=field_name,
                                    symbol_type='field',
                                    line_number=i,
                                    file_path=str(file_path),
                                    modifiers=modifiers,
                                    signature=stripped,
                                    parent_class=current_class,
                                    return_type=field_type,
                                    javadoc=current_javadoc,
                                    annotations=current_annotations.copy()
                                ))
                                
                                # Reset for next symbol
                                current_javadoc = None
                                current_annotations = []
            
            # Cache the symbols
            self.symbols_cache[file_key] = symbols
            return symbols
            
        except Exception as e:
            return []
    
    def _extract_modifiers(self, line: str) -> List[str]:
        """Extract Java modifiers from a line"""
        found_modifiers = []
        for modifier in self.modifiers:
            if re.search(r'\b' + modifier + r'\b', line):
                found_modifiers.append(modifier)
        return found_modifiers
    
    def _parse_parameters(self, params_str: str) -> List[str]:
        """Parse method parameters"""
        if not params_str or params_str.strip() == '':
            return []
        
        parameters = []
        for param in params_str.split(','):
            param = param.strip()
            if param:
                # Extract parameter name (last word)
                parts = param.split()
                if parts:
                    param_name = parts[-1]
                    parameters.append(param_name)
        
        return parameters
    
    def find_symbol_usages(self, symbol_name: str, file_path: Path) -> List[int]:
        """Find all line numbers where a symbol is used"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            usage_lines = []
            
            for i, line in enumerate(lines, 1):
                # Look for symbol as a standalone word (not part of another identifier)
                if re.search(r'\b' + re.escape(symbol_name) + r'\b', line):
                    usage_lines.append(i)
            
            return usage_lines
            
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
    
    def extract_javadoc(self, javadoc_str: Optional[str]) -> Optional[str]:
        """Clean and format Javadoc comment"""
        if not javadoc_str:
            return None
        
        # Remove /** and */ markers
        cleaned = re.sub(r'/\*\*|\*/', '', javadoc_str)
        # Remove leading * from each line
        cleaned = re.sub(r'\n\s*\*\s*', ' ', cleaned)
        # Clean up whitespace
        cleaned = ' '.join(cleaned.split())
        
        return cleaned.strip() if cleaned.strip() else None

