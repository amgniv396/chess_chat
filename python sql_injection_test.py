import sys
import os
from SQLL_database import UserDatabase


def test_sql_injection():
    """Test the UserDatabase class for SQL injection vulnerabilities"""
    print("===== SQL INJECTION PROTECTION TEST =====")

    # Create a test database
    test_db = UserDatabase("test_injection.db")

    # Add a test user
    test_db.add_user("testuser", "test@example.com", "password123")

    # Test cases - list of potential SQL injection attempts
    test_cases = [
        "' OR '1'='1",  # Basic SQL injection
        "testuser' --",  # Comment-based injection
        "test@example.com' OR 1=1; --",  # More complex injection with comments
        "testuser' UNION SELECT 1,2,3,4,5,6,7 --",  # Union-based injection
        "testuser'; DROP TABLE users; --",  # Destructive injection attempt
        "'; UPDATE users SET password_hash='hacked'; --",  # Modification attempt
        "x' OR username LIKE '%'; --",  # Wildcard-based injection
        "test@example.com\"; executeSQL(\"DROP TABLE users\")",  # Attempting code execution
        "' OR username IS NOT NULL; --"  # Always true condition
    ]

    print("\n1. Testing authenticate_user method:")
    for test_case in test_cases:
        print(f"\nTesting injection: {test_case}")
        result, message = test_db.authenticate_user(test_case, "anypassword")
        print(f"Result: {'VULNERABLE ❌' if result else 'Protected ✓'}")
        print(f"Message: {message}")

    print("\n2. Testing email_exists method:")
    for test_case in test_cases:
        print(f"\nTesting injection: {test_case}")
        result = test_db.email_exists(test_case)
        print(f"Result: {'VULNERABLE ❌' if result else 'Protected ✓'}")

    print("\n3. Testing username_exists method:")
    for test_case in test_cases:
        print(f"\nTesting injection: {test_case}")
        result = test_db.username_exists(test_case)
        print(f"Result: {'VULNERABLE ❌' if result else 'Protected ✓'}")

    print("\n4. Testing verify_reset_code method:")
    for test_case in test_cases:
        print(f"\nTesting injection: {test_case}")
        result, message = test_db.verify_reset_code(test_case, "anycode")
        print(f"Result: {'VULNERABLE ❌' if result else 'Protected ✓'}")

    print("\n5. Testing get_pending_user_email method:")
    for test_case in test_cases:
        print(f"\nTesting injection: {test_case}")
        result = test_db.get_pending_user_email(test_case)
        print(f"Result: {'VULNERABLE ❌' if result else 'Protected ✓'}")

    print("\n===== TEST COMPLETED =====")

    # Clean up - delete test database
    try:
        os.remove("test_injection.db")
        print("Test database removed")
    except:
        print("Could not remove test database")


if __name__ == "__main__":
    test_sql_injection()