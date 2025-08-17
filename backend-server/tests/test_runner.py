#!/usr/bin/env python3
"""
Test runner for JobSwitch.ai testing framework
"""
import sys
import os
import subprocess
import argparse
import time
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


def run_unit_tests(verbose=False, coverage=True):
    """Run unit tests"""
    print("🧪 Running Unit Tests...")
    
    cmd = ["python", "-m", "pytest", "tests/unit/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=app", "--cov-report=term-missing"])
    
    cmd.append("--tb=short")
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode == 0


def run_integration_tests(verbose=False):
    """Run integration tests"""
    print("🔗 Running Integration Tests...")
    
    cmd = ["python", "-m", "pytest", "tests/integration/"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.append("--tb=short")
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode == 0


def run_e2e_tests(verbose=False):
    """Run end-to-end tests"""
    print("🎯 Running End-to-End Tests...")
    
    cmd = ["python", "-m", "pytest", "tests/e2e/"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.append("--tb=short")
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode == 0


def run_performance_tests(verbose=False):
    """Run performance tests"""
    print("⚡ Running Performance Tests...")
    
    cmd = ["python", "-m", "pytest", "tests/performance/", "-m", "performance"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.append("--tb=short")
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode == 0


def run_frontend_tests(verbose=False):
    """Run frontend tests"""
    print("🎨 Running Frontend Tests...")
    
    frontend_path = Path(__file__).parent.parent.parent / "jobswitch-ui" / "jobswitch-ui"
    
    if not frontend_path.exists():
        print("❌ Frontend directory not found")
        return False
    
    cmd = ["npm", "test", "--", "--watchAll=false"]
    
    if verbose:
        cmd.append("--verbose")
    
    result = subprocess.run(cmd, cwd=frontend_path)
    return result.returncode == 0


def run_all_tests(verbose=False, coverage=True, include_performance=False):
    """Run all test suites"""
    print("🚀 Running All Tests...")
    
    results = []
    start_time = time.time()
    
    # Run unit tests
    results.append(("Unit Tests", run_unit_tests(verbose, coverage)))
    
    # Run integration tests
    results.append(("Integration Tests", run_integration_tests(verbose)))
    
    # Run end-to-end tests
    results.append(("End-to-End Tests", run_e2e_tests(verbose)))
    
    # Run performance tests if requested
    if include_performance:
        results.append(("Performance Tests", run_performance_tests(verbose)))
    
    # Run frontend tests
    results.append(("Frontend Tests", run_frontend_tests(verbose)))
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_type, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_type:<20} {status}")
        if not passed:
            all_passed = False
    
    print(f"\nTotal execution time: {total_time:.2f} seconds")
    
    if all_passed:
        print("\n🎉 All tests passed!")
        return True
    else:
        print("\n💥 Some tests failed!")
        return False


def generate_test_report():
    """Generate comprehensive test report"""
    print("📋 Generating Test Report...")
    
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "--cov=app",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "--junitxml=test-results.xml",
        "--tb=short"
    ]
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    
    if result.returncode == 0:
        print("✅ Test report generated successfully!")
        print("📁 HTML coverage report: htmlcov/index.html")
        print("📄 XML coverage report: coverage.xml")
        print("📄 JUnit XML report: test-results.xml")
    else:
        print("❌ Failed to generate test report")
    
    return result.returncode == 0


def check_test_dependencies():
    """Check if all test dependencies are installed"""
    print("🔍 Checking Test Dependencies...")
    
    required_packages = [
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
        "httpx",
        "psutil"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    else:
        print("✅ All test dependencies are installed")
        return True


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="JobSwitch.ai Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--frontend", action="store_true", help="Run frontend tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-coverage", action="store_true", help="Disable coverage reporting")
    parser.add_argument("--include-performance", action="store_true", help="Include performance tests in --all")
    parser.add_argument("--report", action="store_true", help="Generate comprehensive test report")
    parser.add_argument("--check-deps", action="store_true", help="Check test dependencies")
    
    args = parser.parse_args()
    
    # Check dependencies first
    if args.check_deps:
        return 0 if check_test_dependencies() else 1
    
    if not check_test_dependencies():
        return 1
    
    coverage = not args.no_coverage
    
    # Run specific test suites
    if args.unit:
        return 0 if run_unit_tests(args.verbose, coverage) else 1
    elif args.integration:
        return 0 if run_integration_tests(args.verbose) else 1
    elif args.e2e:
        return 0 if run_e2e_tests(args.verbose) else 1
    elif args.performance:
        return 0 if run_performance_tests(args.verbose) else 1
    elif args.frontend:
        return 0 if run_frontend_tests(args.verbose) else 1
    elif args.report:
        return 0 if generate_test_report() else 1
    elif args.all:
        return 0 if run_all_tests(args.verbose, coverage, args.include_performance) else 1
    else:
        # Default: run all tests except performance
        return 0 if run_all_tests(args.verbose, coverage, False) else 1


if __name__ == "__main__":
    sys.exit(main())