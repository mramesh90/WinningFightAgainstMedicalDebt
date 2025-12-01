"""
Test Runner Script
==================

Run all tests for the Medical Bill Processing System.
"""

import sys
import unittest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests import test_main, test_integration


def run_all_tests():
    """Run all test suites"""

    print("MEDICAL BILL PROCESSING SYSTEM - TEST SUITE")
    print()

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    print("Loading unit tests...")
    suite.addTests(loader.loadTestsFromModule(test_main))

    print("Loading integration tests...")
    suite.addTests(loader.loadTestsFromModule(test_integration))

    print(f"\nTotal tests loaded: {suite.countTestCases()}")
    print()

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print()
    print("TEST SUMMARY")
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print()

    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED!")
        return 0
    else:
        print("❌ SOME TESTS FAILED!")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)

