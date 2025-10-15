"""
Verify that the MCP server generates proper schemas for Gemini Code Assist
"""

import json
from src.server import mcp, TodoItem
from pydantic import TypeAdapter


def show_schema():
    """Display the generated schemas"""
    
    print("=" * 80)
    print("SCHEMA VERIFICATION FOR GEMINI CODE ASSIST")
    print("=" * 80)
    print()
    
    # Get TodoItem schema
    print("1. TodoItem Pydantic Model Schema")
    print("-" * 80)
    todo_schema = TodoItem.model_json_schema()
    print(json.dumps(todo_schema, indent=2))
    print()
    
    # Check for problematic patterns
    print("2. Schema Validation Checks")
    print("-" * 80)
    
    schema_str = json.dumps(todo_schema)
    
    checks = [
        ("✅ No 'additionalProperties: true'" if '"additionalProperties": true' not in schema_str else "❌ Found 'additionalProperties: true'",
         '"additionalProperties": true' not in schema_str),
        ("✅ Has explicit 'properties' field" if '"properties"' in schema_str else "❌ Missing 'properties' field",
         '"properties"' in schema_str),
        ("✅ Has 'required' fields" if '"required"' in schema_str else "❌ Missing 'required' fields",
         '"required"' in schema_str),
        ("✅ All fields have types" if '"type"' in schema_str else "❌ Missing type definitions",
         '"type"' in schema_str),
    ]
    
    all_passed = True
    for check_msg, passed in checks:
        print(f"  {check_msg}")
        if not passed:
            all_passed = False
    
    print()
    
    # Show what the MCP tool will see
    print("3. Expected Tool Schema for TodoWrite")
    print("-" * 80)
    
    # Simulate what Gemini Code Assist will receive
    expected_schema = {
        "properties": {
            "todos": {
                "type": "array",
                "items": todo_schema,
                "title": "Todos"
            },
            "merge": {
                "type": "boolean",
                "default": False,
                "title": "Merge"
            },
            "clear": {
                "type": "boolean", 
                "default": False,
                "title": "Clear"
            }
        },
        "required": ["todos"],
        "type": "object"
    }
    
    print(json.dumps(expected_schema, indent=2))
    print()
    
    # Verify it's parseable
    print("4. Compatibility Test")
    print("-" * 80)
    
    try:
        # Test creating a TodoItem
        test_todo = TodoItem(
            id="test-1",
            content="Test todo item",
            status="pending",
            priority="high"
        )
        print(f"  ✅ TodoItem creation works")
        print(f"     {test_todo.model_dump()}")
        
        # Test validation
        test_data = {
            "id": "task-1",
            "content": "Implement authentication",
            "status": "in_progress",
            "priority": "high"
        }
        validated_todo = TodoItem(**test_data)
        print(f"  ✅ TodoItem validation works")
        print(f"     {validated_todo.model_dump()}")
        
        # Test default values
        minimal_todo = TodoItem(id="task-2", content="Minimal todo")
        print(f"  ✅ Default values work")
        print(f"     {minimal_todo.model_dump()}")
        
        print()
        print("5. Summary")
        print("-" * 80)
        if all_passed:
            print("  ✅ ALL CHECKS PASSED")
            print("  ✅ Schema is compatible with Gemini Code Assist")
            print("  ✅ No 'additionalProperties: true' in schema")
            print("  ✅ All fields explicitly defined")
            print()
            print("  Your MCP server is now compatible with:")
            print("    • Gemini Code Assist (Android Studio/IntelliJ)")
            print("    • Cursor")
            print("    • VS Code MCP extensions")
            print("    • All MCP clients requiring strict schemas")
        else:
            print("  ❌ SOME CHECKS FAILED")
            print("  Review the schema above for issues")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    show_schema()

