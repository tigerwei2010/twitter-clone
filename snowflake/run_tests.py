#!/usr/bin/env python3
"""Simple test runner for snowflake generator tests"""

import sys
import traceback
from test_snowflake_generator import TestSnowflakeGenerator

def run_test_method(test_instance, method_name):
    """Run a single test method"""
    try:
        method = getattr(test_instance, method_name)
        method()
        print(f"✓ {method_name}")
        return True
    except Exception as e:
        print(f"✗ {method_name}: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    test_instance = TestSnowflakeGenerator()
    
    # Get all test methods
    test_methods = [method for method in dir(test_instance) if method.startswith('test_')]
    
    passed = 0
    failed = 0
    
    print("Running snowflake generator tests...\n")
    
    for method_name in test_methods:
        if run_test_method(test_instance, method_name):
            passed += 1
        else:
            failed += 1
        print()
    
    print(f"\nTest Results: {passed} passed, {failed} failed")
    
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()