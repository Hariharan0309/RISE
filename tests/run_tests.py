#!/usr/bin/env python3
"""
Test Runner for RISE Lambda Function Unit Tests
Runs all unit tests with proper setup and reporting
"""

import unittest
import sys
import os
import time
from io import StringIO
import json

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import test configuration
from tests.test_config import setup_test_environment, teardown_test_environment


class ColoredTextTestResult(unittest.TextTestResult):
    """Test result with colored output"""
    
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.success_count = 0
        self.start_time = None
    
    def startTest(self, test):
        super().startTest(test)
        if self.start_time is None:
            self.start_time = time.time()
    
    def addSuccess(self, test):
        super().addSuccess(test)
        self.success_count += 1
        if self.verbosity > 1:
            self.stream.write(f"\033[92m✓\033[0m {test._testMethodName}\n")
    
    def addError(self, test, err):
        super().addError(test, err)
        if self.verbosity > 1:
            self.stream.write(f"\033[91m✗\033[0m {test._testMethodName} (ERROR)\n")
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        if self.verbosity > 1:
            self.stream.write(f"\033[91m✗\033[0m {test._testMethodName} (FAIL)\n")
    
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        if self.verbosity > 1:
            self.stream.write(f"\033[93m-\033[0m {test._testMethodName} (SKIP: {reason})\n")


class TestRunner:
    """Custom test runner for RISE Lambda tests"""
    
    def __init__(self, verbosity=2):
        self.verbosity = verbosity
        self.test_modules = [
            'tests.test_lambda_functions',
            'tests.test_authentication_lambda',
            'tests.test_data_validation',
            'tests.test_error_handling'
        ]
    
    def discover_tests(self):
        """Discover all test cases"""
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        for module_name in self.test_modules:
            try:
                module_suite = loader.loadTestsFromName(module_name)
                suite.addTest(module_suite)
                print(f"✓ Loaded tests from {module_name}")
            except ImportError as e:
                print(f"✗ Failed to load {module_name}: {e}")
            except Exception as e:
                print(f"✗ Error loading {module_name}: {e}")
        
        return suite
    
    def run_tests(self, test_pattern=None):
        """Run all tests or tests matching pattern"""
        print("=" * 70)
        print("RISE Lambda Function Unit Tests")
        print("=" * 70)
        
        # Set up test environment
        print("Setting up test environment...")
        setup_test_environment()
        
        try:
            # Discover tests
            print("Discovering tests...")
            suite = self.discover_tests()
            
            if test_pattern:
                # Filter tests by pattern
                filtered_suite = unittest.TestSuite()
                for test_group in suite:
                    for test_case in test_group:
                        if hasattr(test_case, '_testMethodName'):
                            if test_pattern.lower() in test_case._testMethodName.lower():
                                filtered_suite.addTest(test_case)
                        else:
                            # Handle test suites
                            for individual_test in test_case:
                                if test_pattern.lower() in individual_test._testMethodName.lower():
                                    filtered_suite.addTest(individual_test)
                suite = filtered_suite
            
            # Count total tests
            total_tests = suite.countTestCases()
            print(f"Found {total_tests} test cases")
            
            if total_tests == 0:
                print("No tests found!")
                return False
            
            print("\nRunning tests...")
            print("-" * 70)
            
            # Run tests
            runner = unittest.TextTestRunner(
                stream=sys.stdout,
                verbosity=self.verbosity,
                resultclass=ColoredTextTestResult
            )
            
            start_time = time.time()
            result = runner.run(suite)
            end_time = time.time()
            
            # Print summary
            self.print_summary(result, end_time - start_time)
            
            return result.wasSuccessful()
        
        finally:
            # Clean up test environment
            print("\nCleaning up test environment...")
            teardown_test_environment()
    
    def print_summary(self, result, duration):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        total = result.testsRun
        failures = len(result.failures)
        errors = len(result.errors)
        skipped = len(result.skipped)
        success = total - failures - errors - skipped
        
        print(f"Total Tests:    {total}")
        print(f"\033[92mPassed:         {success}\033[0m")
        
        if failures > 0:
            print(f"\033[91mFailed:         {failures}\033[0m")
        
        if errors > 0:
            print(f"\033[91mErrors:         {errors}\033[0m")
        
        if skipped > 0:
            print(f"\033[93mSkipped:        {skipped}\033[0m")
        
        print(f"Duration:       {duration:.2f}s")
        
        # Calculate success rate
        if total > 0:
            success_rate = (success / total) * 100
            print(f"Success Rate:   {success_rate:.1f}%")
        
        # Print detailed failures and errors
        if failures or errors:
            print("\n" + "-" * 70)
            print("DETAILED FAILURES AND ERRORS")
            print("-" * 70)
            
            for test, traceback in result.failures:
                print(f"\nFAILURE: {test}")
                print(traceback)
            
            for test, traceback in result.errors:
                print(f"\nERROR: {test}")
                print(traceback)
        
        print("=" * 70)
    
    def run_coverage_analysis(self):
        """Run tests with coverage analysis"""
        try:
            import coverage
        except ImportError:
            print("Coverage.py not installed. Install with: pip install coverage")
            return False
        
        print("Running tests with coverage analysis...")
        
        # Start coverage
        cov = coverage.Coverage()
        cov.start()
        
        # Run tests
        success = self.run_tests()
        
        # Stop coverage and generate report
        cov.stop()
        cov.save()
        
        print("\nCoverage Report:")
        print("-" * 50)
        cov.report()
        
        # Generate HTML report
        try:
            cov.html_report(directory='tests/coverage_html')
            print(f"\nHTML coverage report generated in: tests/coverage_html/")
        except Exception as e:
            print(f"Failed to generate HTML report: {e}")
        
        return success


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run RISE Lambda function unit tests')
    parser.add_argument('-v', '--verbosity', type=int, choices=[0, 1, 2], default=2,
                       help='Test output verbosity (0=quiet, 1=normal, 2=verbose)')
    parser.add_argument('-p', '--pattern', type=str,
                       help='Run only tests matching this pattern')
    parser.add_argument('-c', '--coverage', action='store_true',
                       help='Run tests with coverage analysis')
    parser.add_argument('--list', action='store_true',
                       help='List all available tests without running them')
    
    args = parser.parse_args()
    
    runner = TestRunner(verbosity=args.verbosity)
    
    if args.list:
        # List all tests
        print("Available test cases:")
        suite = runner.discover_tests()
        for test_group in suite:
            for test_case in test_group:
                if hasattr(test_case, '_testMethodName'):
                    print(f"  - {test_case.__class__.__name__}.{test_case._testMethodName}")
        return
    
    if args.coverage:
        success = runner.run_coverage_analysis()
    else:
        success = runner.run_tests(args.pattern)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()