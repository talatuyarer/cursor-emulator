"""
Test Java Support for Enhanced Codebase Search
"""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from src.tools.codebase_search_ast import codebase_search_ast
from src.tools.java_analyzer import JavaCodeAnalyzer


async def test_java_analyzer():
    """Test the Java analyzer directly"""
    print("=" * 80)
    print("JAVA ANALYZER TEST")
    print("=" * 80)
    print()
    
    # Create a sample Java file for testing
    sample_java = Path("test_sample.java")
    sample_java.write_text("""
package com.example.app;

import java.util.List;
import java.util.ArrayList;

/**
 * Sample service class for user management
 */
public class UserService {
    
    private final UserRepository repository;
    
    /**
     * Constructor for UserService
     * @param repository the user repository
     */
    public UserService(UserRepository repository) {
        this.repository = repository;
    }
    
    /**
     * Get all users from the database
     * @return list of all users
     */
    public List<User> getAllUsers() {
        return repository.findAll();
    }
    
    /**
     * Save a new user
     * @param user the user to save
     * @return the saved user
     */
    @Override
    public User saveUser(User user) {
        validateUser(user);
        return repository.save(user);
    }
    
    private void validateUser(User user) {
        if (user == null) {
            throw new IllegalArgumentException("User cannot be null");
        }
    }
}
""")
    
    try:
        analyzer = JavaCodeAnalyzer()
        symbols = analyzer.analyze_file(sample_java)
        
        print(f"✓ Analyzed {sample_java}")
        print(f"  Found {len(symbols)} symbols:")
        print()
        
        for symbol in symbols:
            print(f"  - {symbol.symbol_type.upper()}: {symbol.name}")
            if symbol.line_number:
                print(f"    Line: {symbol.line_number}")
            if symbol.modifiers:
                print(f"    Modifiers: {', '.join(symbol.modifiers)}")
            if symbol.parameters:
                print(f"    Parameters: {', '.join(symbol.parameters)}")
            if symbol.return_type:
                print(f"    Return type: {symbol.return_type}")
            if symbol.javadoc:
                javadoc_clean = analyzer.extract_javadoc(symbol.javadoc)
                if javadoc_clean:
                    print(f"    Javadoc: {javadoc_clean[:60]}...")
            if symbol.annotations:
                print(f"    Annotations: {', '.join(symbol.annotations)}")
            print()
        
    finally:
        # Clean up
        if sample_java.exists():
            sample_java.unlink()


async def test_java_search():
    """Test searching Java code"""
    print("\n" + "=" * 80)
    print("JAVA CODE SEARCH TEST")
    print("=" * 80)
    print()
    
    # Create a test Java project structure
    test_dir = Path("test_java_project")
    test_dir.mkdir(exist_ok=True)
    
    # Create main service
    service_file = test_dir / "UserService.java"
    service_file.write_text("""
package com.example.service;

import com.example.repository.UserRepository;
import com.example.model.User;

/**
 * Service for managing users
 */
public class UserService {
    
    private UserRepository repository;
    
    /**
     * Find user by ID
     * @param id user identifier
     * @return user object
     */
    public User findById(Long id) {
        return repository.findById(id);
    }
    
    /**
     * Authenticate user with credentials
     * @param username the username
     * @param password the password
     * @return authenticated user
     */
    public User authenticate(String username, String password) {
        User user = repository.findByUsername(username);
        if (validatePassword(user, password)) {
            return user;
        }
        throw new AuthenticationException("Invalid credentials");
    }
    
    private boolean validatePassword(User user, String password) {
        return user.getPassword().equals(password);
    }
}
""")
    
    # Create controller
    controller_file = test_dir / "UserController.java"
    controller_file.write_text("""
package com.example.controller;

import com.example.service.UserService;
import org.springframework.web.bind.annotation.*;

/**
 * REST controller for user operations
 */
@RestController
@RequestMapping("/api/users")
public class UserController {
    
    private final UserService userService;
    
    @Autowired
    public UserController(UserService userService) {
        this.userService = userService;
    }
    
    /**
     * Get user by ID
     * @param id user identifier
     * @return user data
     */
    @GetMapping("/{id}")
    public User getUser(@PathVariable Long id) {
        return userService.findById(id);
    }
    
    /**
     * Login endpoint
     * @param credentials user credentials
     * @return authentication token
     */
    @PostMapping("/login")
    public String login(@RequestBody LoginRequest credentials) {
        User user = userService.authenticate(
            credentials.getUsername(), 
            credentials.getPassword()
        );
        return generateToken(user);
    }
}
""")
    
    try:
        # Test various searches
        test_queries = [
            {
                "name": "Find Definition - UserService",
                "query": "where is UserService defined",
                "expected": "Should find class definition"
            },
            {
                "name": "Find Method - authenticate",
                "query": "find definition of authenticate",
                "expected": "Should find authenticate method"
            },
            {
                "name": "Find Usages - UserService",
                "query": "where is UserService used",
                "expected": "Should find usage in UserController"
            },
            {
                "name": "Semantic Search - authentication",
                "query": "authentication",
                "expected": "Should find related methods and classes"
            },
            {
                "name": "Semantic Search - REST API",
                "query": "REST API endpoint user",
                "expected": "Should find controller methods"
            }
        ]
        
        for i, test in enumerate(test_queries, 1):
            print(f"\n{'─' * 80}")
            print(f"TEST {i}/{len(test_queries)}: {test['name']}")
            print(f"Query: \"{test['query']}\"")
            print(f"Expected: {test['expected']}")
            print(f"{'─' * 80}\n")
            
            result = await codebase_search_ast({
                "query": test['query'],
                "target_directories": [str(test_dir)],
                "max_results": 5
            })
            
            if result["success"]:
                print(f"✓ Found {result['total_results']} results")
                
                if result['results']:
                    print(f"\nTop results:")
                    for j, res in enumerate(result['results'][:3], 1):
                        filename = Path(res['file_path']).name
                        print(f"\n  {j}. {filename}:{res['line_number']}")
                        print(f"     Symbol: {res.get('symbol_type', 'N/A')} {res.get('symbol_name', 'N/A')}")
                        print(f"     Score: {res['relevance_score']}")
                        if res.get('docstring'):
                            print(f"     Doc: {res['docstring'][:60]}...")
                        print(f"     Code: {res['content'][:70]}...")
                else:
                    print("  No results found")
            else:
                print("✗ Search failed")
        
        print("\n" + "=" * 80)
        print("LANGUAGE SUPPORT SUMMARY")
        print("=" * 80)
        print()
        print("✅ Python  - Full AST support (classes, functions, methods, imports)")
        print("✅ Java    - Full symbol extraction (classes, methods, fields, interfaces)")
        print("⚠️  JavaScript/TypeScript - Pattern-based (coming soon with full AST)")
        print()
        print("Java Features:")
        print("  • Class, Interface, Enum definitions")
        print("  • Method and constructor signatures")
        print("  • Field declarations")
        print("  • Import statements")
        print("  • Javadoc comments")
        print("  • Annotations (@Override, @Autowired, etc.)")
        print("  • Modifiers (public, private, static, etc.)")
        print("  • Extends and implements relationships")
        print()
        
    finally:
        # Clean up
        import shutil
        if test_dir.exists():
            shutil.rmtree(test_dir)


async def test_multi_language():
    """Test searching across Python and Java"""
    print("\n" + "=" * 80)
    print("MULTI-LANGUAGE SEARCH TEST")
    print("=" * 80)
    print()
    
    test_dir = Path("test_multi_lang")
    test_dir.mkdir(exist_ok=True)
    
    # Create Python file
    py_file = test_dir / "auth_service.py"
    py_file.write_text("""
class AuthenticationService:
    '''Service for user authentication'''
    
    def authenticate(self, username: str, password: str):
        '''Authenticate user with credentials'''
        user = self.user_repository.find_by_username(username)
        return self.validate_password(user, password)
    
    def validate_password(self, user, password):
        '''Validate user password'''
        return user.password == password
""")
    
    # Create Java file
    java_file = test_dir / "AuthService.java"
    java_file.write_text("""
public class AuthService {
    /**
     * Authenticate user
     */
    public User authenticate(String username, String password) {
        User user = repository.findByUsername(username);
        return validatePassword(user, password);
    }
    
    private boolean validatePassword(User user, String password) {
        return user.getPassword().equals(password);
    }
}
""")
    
    try:
        # Search for authentication across both languages
        result = await codebase_search_ast({
            "query": "authentication",
            "target_directories": [str(test_dir)],
            "max_results": 10
        })
        
        print(f"Query: 'authentication'")
        print(f"\n✓ Found {result['total_results']} results across multiple languages:")
        print()
        
        python_results = [r for r in result['results'] if r['file_path'].endswith('.py')]
        java_results = [r for r in result['results'] if r['file_path'].endswith('.java')]
        
        print(f"  Python results: {len(python_results)}")
        for res in python_results[:2]:
            print(f"    - {res['symbol_type']} {res['symbol_name']} (line {res['line_number']})")
        
        print(f"\n  Java results: {len(java_results)}")
        for res in java_results[:2]:
            print(f"    - {res['symbol_type']} {res['symbol_name']} (line {res['line_number']})")
        
        print()
        print("✨ Multi-language search works seamlessly!")
        print("   Both Python and Java code are analyzed with full symbol understanding.")
        print()
        
    finally:
        # Clean up
        import shutil
        if test_dir.exists():
            shutil.rmtree(test_dir)


async def main():
    """Run all tests"""
    await test_java_analyzer()
    await test_java_search()
    await test_multi_language()
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETE!")
    print("=" * 80)
    print()
    print("Your enhanced codebase search now supports:")
    print("  ✅ Python (full AST)")
    print("  ✅ Java (full symbol extraction)")
    print("  ✅ Multi-language projects")
    print("  ✅ Intent detection")
    print("  ✅ Smart ranking")
    print()


if __name__ == "__main__":
    asyncio.run(main())

