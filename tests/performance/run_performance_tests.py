"""
Main performance test runner for RISE.

Executes all performance tests and generates comprehensive reports:
- Load testing
- Response time validation
- Network simulation
- Offline functionality
- Bundle size analysis
"""

import sys
import os
import unittest
import argparse
import time
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


class PerformanceTestRunner:
    """Orchestrate performance testing."""
    
    def __init__(self, args):
        self.args = args
        self.results = {
            'start_time': time.time(),
            'test_results': {},
            'summary': {}
        }
        self.test_dir = Path(__file__).parent
    
    def run_response_time_tests(self):
        """Run response time validation tests."""
        print(f"\n{'='*70}")
        print(f"RUNNING RESPONSE TIME TESTS")
        print(f"{'='*70}\n")
        
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Load voice response time tests
        voice_tests = loader.discover(
            str(self.test_dir / 'response_time'),
            pattern='test_voice_response_time.py'
        )
        suite.addTests(voice_tests)
        
        # Load image response time tests
        image_tests = loader.discover(
            str(self.test_dir / 'response_time'),
            pattern='test_image_response_time.py'
        )
        suite.addTests(image_tests)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        self.results['test_results']['response_time'] = {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success': result.wasSuccessful()
        }
        
        return result.wasSuccessful()
    
    def run_network_simulation_tests(self):
        """Run network simulation tests."""
        print(f"\n{'='*70}")
        print(f"RUNNING NETWORK SIMULATION TESTS")
        print(f"{'='*70}\n")
        
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Load 2G performance tests
        network_tests = loader.discover(
            str(self.test_dir / 'network_simulation'),
            pattern='test_2g_performance.py'
        )
        suite.addTests(network_tests)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        self.results['test_results']['network_simulation'] = {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success': result.wasSuccessful()
        }
        
        return result.wasSuccessful()
    
    def run_offline_tests(self):
        """Run offline functionality tests."""
        print(f"\n{'='*70}")
        print(f"RUNNING OFFLINE FUNCTIONALITY TESTS")
        print(f"{'='*70}\n")
        
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Load offline tests
        offline_tests = loader.discover(
            str(self.test_dir / 'offline_testing'),
            pattern='test_offline_functionality.py'
        )
        suite.addTests(offline_tests)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        self.results['test_results']['offline'] = {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success': result.wasSuccessful()
        }
        
        return result.wasSuccessful()
    
    def run_bundle_analysis(self):
        """Run bundle size analysis."""
        print(f"\n{'='*70}")
        print(f"RUNNING BUNDLE SIZE ANALYSIS")
        print(f"{'='*70}\n")
        
        try:
            # Import and run bundle analyzer
            sys.path.insert(0, str(self.test_dir / 'bundle_analysis'))
            from analyze_bundle_size import BundleAnalyzer
            
            project_root = self.test_dir.parent.parent
            analyzer = BundleAnalyzer(project_root)
            analyzer.generate_report()
            
            self.results['test_results']['bundle_analysis'] = {
                'success': True,
                'results': analyzer.results
            }
            
            return True
            
        except Exception as e:
            print(f"❌ Bundle analysis failed: {e}")
            self.results['test_results']['bundle_analysis'] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    def run_load_tests(self):
        """Run load tests with Locust."""
        print(f"\n{'='*70}")
        print(f"LOAD TESTING")
        print(f"{'='*70}\n")
        
        print("ℹ️  Load tests require Locust to be run separately:")
        print(f"\n  locust -f {self.test_dir}/load_testing/locustfile.py \\")
        print(f"    --host=https://api.rise.example.com \\")
        print(f"    --users 100000 --spawn-rate 1000 --run-time 5m --headless\n")
        
        print("For interactive load testing:")
        print(f"  locust -f {self.test_dir}/load_testing/locustfile.py \\")
        print(f"    --host=https://api.rise.example.com\n")
        
        print("Then open http://localhost:8089 in your browser\n")
        
        self.results['test_results']['load_testing'] = {
            'note': 'Load tests must be run separately with Locust'
        }
        
        return True
    
    def print_summary(self):
        """Print test summary."""
        print(f"\n{'='*70}")
        print(f"PERFORMANCE TEST SUMMARY")
        print(f"{'='*70}\n")
        
        total_time = time.time() - self.results['start_time']
        
        print(f"Total execution time: {total_time:.2f}s\n")
        
        # Print results for each category
        all_success = True
        for category, result in self.results['test_results'].items():
            if isinstance(result, dict) and 'success' in result:
                status = "✅ PASS" if result['success'] else "❌ FAIL"
                print(f"{category.replace('_', ' ').title()}: {status}")
                
                if 'tests_run' in result:
                    print(f"  Tests run: {result['tests_run']}")
                    print(f"  Failures: {result['failures']}")
                    print(f"  Errors: {result['errors']}")
                
                if not result['success']:
                    all_success = False
            else:
                print(f"{category.replace('_', ' ').title()}: ℹ️  {result.get('note', 'N/A')}")
        
        print(f"\n{'='*70}")
        if all_success:
            print(f"✅ ALL PERFORMANCE TESTS PASSED")
        else:
            print(f"❌ SOME PERFORMANCE TESTS FAILED")
        print(f"{'='*70}\n")
        
        # Save results
        self.save_results()
    
    def save_results(self):
        """Save test results to file."""
        self.results['end_time'] = time.time()
        self.results['total_duration'] = self.results['end_time'] - self.results['start_time']
        
        output_file = self.test_dir / 'performance_test_results.json'
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"📊 Results saved to: {output_file}\n")
    
    def run_all(self):
        """Run all performance tests."""
        print(f"\n{'='*70}")
        print(f"RISE PERFORMANCE TEST SUITE")
        print(f"{'='*70}\n")
        
        # Run test categories based on arguments
        if self.args.all or self.args.response_time:
            self.run_response_time_tests()
        
        if self.args.all or self.args.network:
            self.run_network_simulation_tests()
        
        if self.args.all or self.args.offline:
            self.run_offline_tests()
        
        if self.args.all or self.args.bundle:
            self.run_bundle_analysis()
        
        if self.args.all or self.args.load:
            self.run_load_tests()
        
        # Print summary
        self.print_summary()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Run RISE performance tests',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all performance tests
  python run_performance_tests.py --all
  
  # Run specific test categories
  python run_performance_tests.py --response-time
  python run_performance_tests.py --network
  python run_performance_tests.py --offline
  python run_performance_tests.py --bundle
  python run_performance_tests.py --load
  
  # Run multiple categories
  python run_performance_tests.py --response-time --network
        """
    )
    
    parser.add_argument('--all', action='store_true',
                       help='Run all performance tests')
    parser.add_argument('--response-time', action='store_true',
                       help='Run response time validation tests')
    parser.add_argument('--network', action='store_true',
                       help='Run network simulation tests')
    parser.add_argument('--offline', action='store_true',
                       help='Run offline functionality tests')
    parser.add_argument('--bundle', action='store_true',
                       help='Run bundle size analysis')
    parser.add_argument('--load', action='store_true',
                       help='Show load testing instructions')
    
    args = parser.parse_args()
    
    # If no specific tests selected, show help
    if not any([args.all, args.response_time, args.network, 
                args.offline, args.bundle, args.load]):
        parser.print_help()
        sys.exit(1)
    
    # Run tests
    runner = PerformanceTestRunner(args)
    runner.run_all()


if __name__ == '__main__':
    main()
