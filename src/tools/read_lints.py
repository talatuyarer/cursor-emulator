import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..state.validators import ValidationError


# Linter configurations for different languages
LINTER_CONFIGS = {
    'python': {
        'extensions': ['.py'],
        'linters': [
            {
                'name': 'ruff',
                'command': 'ruff check {file} --output-format=json',
                'install_command': 'pip install ruff',
                'priority': 1
            },
            {
                'name': 'flake8',
                'command': 'flake8 {file} --format=%(path)s:%(row)d:%(col)d: %(code)s %(text)s',
                'install_command': 'pip install flake8',
                'priority': 2
            },
            {
                'name': 'pylint',
                'command': 'pylint {file} --output-format=json',
                'install_command': 'pip install pylint',
                'priority': 3
            }
        ]
    },
    'java': {
        'extensions': ['.java'],
        'linters': [
            {
                'name': 'checkstyle',
                'command': 'checkstyle -c /google_checks.xml {file}',
                'install_command': 'brew install checkstyle || apt-get install checkstyle',
                'priority': 1
            },
            {
                'name': 'spotbugs',
                'command': 'spotbugs -textui {file}',
                'install_command': 'brew install spotbugs || apt-get install spotbugs',
                'priority': 2
            },
            {
                'name': 'pmd',
                'command': 'pmd check -d {file} -R rulesets/java/basic.xml -f json',
                'install_command': 'brew install pmd || apt-get install pmd',
                'priority': 3
            }
        ]
    },
    'javascript': {
        'extensions': ['.js'],
        'linters': [
            {
                'name': 'eslint',
                'command': 'eslint {file} --format=json',
                'install_command': 'npm install -g eslint',
                'priority': 1
            },
            {
                'name': 'jshint',
                'command': 'jshint {file} --reporter=json',
                'install_command': 'npm install -g jshint',
                'priority': 2
            }
        ]
    },
    'typescript': {
        'extensions': ['.ts', '.tsx'],
        'linters': [
            {
                'name': 'eslint',
                'command': 'eslint {file} --format=json',
                'install_command': 'npm install -g eslint @typescript-eslint/parser',
                'priority': 1
            },
            {
                'name': 'tsc',
                'command': 'tsc --noEmit {file}',
                'install_command': 'npm install -g typescript',
                'priority': 2
            }
        ]
    },
    'go': {
        'extensions': ['.go'],
        'linters': [
            {
                'name': 'golangci-lint',
                'command': 'golangci-lint run {file} --out-format=json',
                'install_command': 'go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest',
                'priority': 1
            },
            {
                'name': 'gofmt',
                'command': 'gofmt -e {file}',
                'install_command': 'go install',
                'priority': 2
            }
        ]
    },
    'rust': {
        'extensions': ['.rs'],
        'linters': [
            {
                'name': 'clippy',
                'command': 'cargo clippy --message-format=json',
                'install_command': 'rustup component add clippy',
                'priority': 1
            },
            {
                'name': 'rustfmt',
                'command': 'rustfmt --check {file}',
                'install_command': 'rustup component add rustfmt',
                'priority': 2
            }
        ]
    },
    'cpp': {
        'extensions': ['.cpp', '.cc', '.cxx', '.c++', '.hpp', '.h'],
        'linters': [
            {
                'name': 'clang-tidy',
                'command': 'clang-tidy {file} --format-style=json',
                'install_command': 'brew install llvm || apt-get install clang-tidy',
                'priority': 1
            },
            {
                'name': 'cppcheck',
                'command': 'cppcheck {file} --output-format=json',
                'install_command': 'brew install cppcheck || apt-get install cppcheck',
                'priority': 2
            }
        ]
    }
}


class LintResult:
    """Represents a single linting result"""
    
    def __init__(self, file_path: str, line: int, column: int, 
                 message: str, severity: str, rule: str = "", linter: str = ""):
        self.file_path = file_path
        self.line = line
        self.column = column
        self.message = message
        self.severity = severity  # error, warning, info
        self.rule = rule
        self.linter = linter
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'file_path': self.file_path,
            'line': self.line,
            'column': self.column,
            'message': self.message,
            'severity': self.severity,
            'rule': self.rule,
            'linter': self.linter
        }


def detect_language(file_path: Path) -> Optional[str]:
    """Detect programming language from file extension"""
    suffix = file_path.suffix.lower()
    
    for language, config in LINTER_CONFIGS.items():
        if suffix in config['extensions']:
            return language
    
    return None


def get_available_linters(language: str) -> List[Dict[str, Any]]:
    """Get list of available linters for a language"""
    if language not in LINTER_CONFIGS:
        return []
    
    available = []
    for linter in LINTER_CONFIGS[language]['linters']:
        if is_linter_available(linter['name']):
            available.append(linter)
    
    return available


def is_linter_available(linter_name: str) -> bool:
    """Check if a linter is available in the system"""
    try:
        # Try to run the linter with --version or --help
        result = subprocess.run(
            [linter_name, '--version'], 
            capture_output=True, 
            timeout=5,
            text=True
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return False


async def run_linter(linter_config: Dict[str, Any], file_path: Path, 
                    timeout: int = 30) -> List[LintResult]:
    """Run a specific linter on a file"""
    results = []
    
    try:
        # Replace {file} placeholder in command
        command = linter_config['command'].format(file=str(file_path))
        
        # Split command into parts
        cmd_parts = command.split()
        
        # Run the linter
        process = await asyncio.create_subprocess_exec(
            *cmd_parts,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=file_path.parent
        )
        
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )
        
        stdout = stdout_bytes.decode('utf-8', errors='replace')
        stderr = stderr_bytes.decode('utf-8', errors='replace')
        
        # Parse output based on linter
        results = parse_linter_output(
            stdout, stderr, str(file_path), 
            linter_config['name'], process.returncode
        )
        
    except asyncio.TimeoutExpired:
        # Linter timed out
        results.append(LintResult(
            file_path=str(file_path),
            line=0,
            column=0,
            message=f"Linter {linter_config['name']} timed out after {timeout} seconds",
            severity="error",
            linter=linter_config['name']
        ))
    except Exception as e:
        # Linter failed to run
        results.append(LintResult(
            file_path=str(file_path),
            line=0,
            column=0,
            message=f"Failed to run linter {linter_config['name']}: {str(e)}",
            severity="error",
            linter=linter_config['name']
        ))
    
    return results


def parse_linter_output(stdout: str, stderr: str, file_path: str, 
                       linter_name: str, return_code: int) -> List[LintResult]:
    """Parse linter output into LintResult objects"""
    results = []
    
    # Handle different output formats
    if linter_name == 'ruff' and stdout.strip():
        try:
            data = json.loads(stdout)
            for violation in data.get('violations', []):
                results.append(LintResult(
                    file_path=file_path,
                    line=violation.get('location', {}).get('row', 0),
                    column=violation.get('location', {}).get('column', 0),
                    message=violation.get('message', ''),
                    severity='error' if violation.get('fix', None) is None else 'warning',
                    rule=violation.get('code', ''),
                    linter=linter_name
                ))
        except json.JSONDecodeError:
            pass
    
    elif linter_name == 'eslint' and stdout.strip():
        try:
            data = json.loads(stdout)
            for file_data in data:
                for message in file_data.get('messages', []):
                    results.append(LintResult(
                        file_path=file_path,
                        line=message.get('line', 0),
                        column=message.get('column', 0),
                        message=message.get('message', ''),
                        severity=message.get('severity', 1),  # 1=warning, 2=error
                        rule=message.get('ruleId', ''),
                        linter=linter_name
                    ))
        except json.JSONDecodeError:
            pass
    
    elif linter_name == 'flake8':
        # Parse flake8 format: file:line:col: code message
        for line in stdout.split('\n'):
            if ':' in line and file_path in line:
                parts = line.split(':', 3)
                if len(parts) >= 4:
                    try:
                        line_num = int(parts[1])
                        col_num = int(parts[2])
                        message_part = parts[3].strip()
                        code = message_part.split()[0] if message_part else ''
                        message = ' '.join(message_part.split()[1:]) if len(message_part.split()) > 1 else message_part
                        
                        results.append(LintResult(
                            file_path=file_path,
                            line=line_num,
                            column=col_num,
                            message=message,
                            severity='error',
                            rule=code,
                            linter=linter_name
                        ))
                    except (ValueError, IndexError):
                        continue
    
    elif linter_name == 'gofmt':
        # gofmt outputs lines that need formatting
        for line in stdout.split('\n'):
            if line.strip():
                results.append(LintResult(
                    file_path=file_path,
                    line=0,
                    column=0,
                    message=f"Formatting issue: {line.strip()}",
                    severity='warning',
                    linter=linter_name
                ))
    
    elif linter_name == 'tsc':
        # TypeScript compiler errors
        for line in stdout.split('\n'):
            if 'error TS' in line:
                # Parse TypeScript error format
                parts = line.split('(', 1)
                if len(parts) >= 2:
                    location_part = parts[1].split(')', 1)[0]
                    if ',' in location_part:
                        try:
                            line_num, col_num = location_part.split(',')
                            line_num = int(line_num.strip())
                            col_num = int(col_num.strip())
                            
                            message = parts[1].split(')', 1)[1].strip() if ')' in parts[1] else ''
                            
                            results.append(LintResult(
                                file_path=file_path,
                                line=line_num,
                                column=col_num,
                                message=message,
                                severity='error',
                                linter=linter_name
                            ))
                        except (ValueError, IndexError):
                            continue
    
    # If no specific parser handled it, try to extract basic info from stderr
    if not results and stderr.strip():
        results.append(LintResult(
            file_path=file_path,
            line=0,
            column=0,
            message=f"Linter output: {stderr.strip()}",
            severity='error' if return_code != 0 else 'info',
            linter=linter_name
        ))
    
    return results


async def lint_file(file_path: Path, languages: Optional[List[str]] = None, 
                   timeout: int = 30) -> List[LintResult]:
    """Lint a single file"""
    results = []
    
    # Detect language if not specified
    if not languages:
        detected_lang = detect_language(file_path)
        languages = [detected_lang] if detected_lang else []
    
    # Run linters for each language
    for language in languages:
        if language not in LINTER_CONFIGS:
            continue
        
        available_linters = get_available_linters(language)
        
        # Run the highest priority available linter
        if available_linters:
            linter = min(available_linters, key=lambda x: x['priority'])
            linter_results = await run_linter(linter, file_path, timeout)
            results.extend(linter_results)
    
    return results


async def lint_directory(directory: Path, languages: Optional[List[str]] = None,
                        timeout: int = 30, recursive: bool = True) -> List[LintResult]:
    """Lint all files in a directory"""
    results = []
    
    # Find all files to lint
    files_to_lint = []
    
    if recursive:
        # Recursive search
        for ext in ['.py', '.java', '.js', '.ts', '.tsx', '.go', '.rs', '.cpp', '.cc', '.hpp', '.h']:
            files_to_lint.extend(directory.rglob(f'*{ext}'))
    else:
        # Non-recursive search
        for ext in ['.py', '.java', '.js', '.ts', '.tsx', '.go', '.rs', '.cpp', '.cc', '.hpp', '.h']:
            files_to_lint.extend(directory.glob(f'*{ext}'))
    
    # Lint each file
    for file_path in files_to_lint:
        file_results = await lint_file(file_path, languages, timeout)
        results.extend(file_results)
    
    return results


async def read_lints(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Read linter errors from the workspace.
    
    Parameters:
        params: Dictionary containing:
            - paths: List of file/directory paths to check (optional, defaults to current directory)
            - languages: List of languages to check (optional, auto-detect if not provided)
            - timeout: Linter timeout in seconds (optional, defaults to 30)
            - recursive: Whether to search recursively in directories (optional, defaults to True)
    
    Returns:
        Dictionary with linting results
    """
    # Validate params structure
    if not isinstance(params, dict):
        raise ValidationError("Parameters must be a dictionary")
    
    # Get parameters
    paths = params.get('paths', ['.'])
    languages = params.get('languages')
    timeout = params.get('timeout', 30)
    recursive = params.get('recursive', True)
    
    # Validate timeout
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ValidationError("Timeout must be a positive number")
    
    if timeout > 300:  # Max 5 minutes
        raise ValidationError("Timeout too long (max 300 seconds)")
    
    # Validate paths
    if not isinstance(paths, list):
        raise ValidationError("Paths must be a list")
    
    all_results = []
    
    try:
        for path_str in paths:
            path = Path(path_str).resolve()
            
            if not path.exists():
                all_results.append(LintResult(
                    file_path=str(path),
                    line=0,
                    column=0,
                    message=f"Path does not exist: {path}",
                    severity="error",
                    linter="system"
                ))
                continue
            
            if path.is_file():
                # Lint single file
                file_results = await lint_file(path, languages, timeout)
                all_results.extend(file_results)
            elif path.is_dir():
                # Lint directory
                dir_results = await lint_directory(path, languages, timeout, recursive)
                all_results.extend(dir_results)
            else:
                all_results.append(LintResult(
                    file_path=str(path),
                    line=0,
                    column=0,
                    message=f"Path is neither file nor directory: {path}",
                    severity="error",
                    linter="system"
                ))
        
        # Convert results to dictionaries
        results_dict = [result.to_dict() for result in all_results]
        
        # Group by severity
        errors = [r for r in results_dict if r['severity'] == 'error']
        warnings = [r for r in results_dict if r['severity'] == 'warning']
        info = [r for r in results_dict if r['severity'] == 'info']
        
        return {
            "success": True,
            "total_issues": len(results_dict),
            "errors": len(errors),
            "warnings": len(warnings),
            "info": len(info),
            "results": results_dict,
            "summary": {
                "errors": errors,
                "warnings": warnings,
                "info": info
            }
        }
        
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Failed to read lints: {str(e)}")
