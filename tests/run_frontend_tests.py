"""
RISE Frontend Test Runner
Runs all frontend tests with coverage reporting
"""

import sys
import os
import unittest
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests(verbosity=2, pattern=None, coverage=False):
    """
    Run frontend tests with optional coverage
    
    Args:
        verbosity: Test output verbosity (0=quiet, 1=normal, 2=verbose)
        pattern: Pattern to match test files (e.g., 'app', 'voice', 'image')
        coverage: Whether to run with coverage analysis
    """
    
    # Start coverage if requested
    if coverage:
        try:
            import coverage as cov
            coverage_obj = cov.Coverage(source=['app', 'ui'])
            coverage_obj.start()
            print("Coverage analysis enabled")
        except ImportError:
            print("Warning: coverage package not installed. Install with: pip install coverage")
            coverage = False
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    
    if pattern:
        # Run tests matching pattern
        test_pattern = f"test_frontend*{pattern}*.py"
        print(f"Running tests matching pattern: {test_pattern}")
    else:
        # Run all frontend tests
        test_pattern = "test_frontend*.py"
        print("Running all frontend tests")
    
    suite = loader.discover(start_dir, pattern=test_pattern)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    # Stop coverage and generate report
    if coverage:
        coverage_obj.stop()
        coverage_obj.save()
        
        print("\n" + "="*70)
        print("COVERAGE REPORT")
        print("="*70)
        coverage_obj.report()
        
        # Generate HTML report
        html_dir = os.path.join(start_dir, 'coverage_html_frontend')
        coverage_obj.html_report(directory=html_dir)
        print(f"\nHTML coverage report generated in: {html_dir}")
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Run RISE frontend tests')
    parser.add_argument(
        '-v', '--verbosity',
        type=int,
        choices=[0, 1, 2],
        default=2,
        help='Test output verbosity (0=quiet, 1=normal, 2=verbose)'
    )
    parser.add_argument(
        '-p', '--pattern',
        type=str,
        help='Pattern to match test files (e.g., "app", "voice", "image")'
    )
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Run tests with coverage analysis'
    )
    
    args = parser.parse_args()
    
    print("="*70)
    print("RISE FRONTEND TEST SUITE")
    print("="*70)
    print()
    
    exit_code = run_tests(
        verbosity=args.verbosity,
        pattern=args.pattern,
        coverage=args.coverage
    )
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
