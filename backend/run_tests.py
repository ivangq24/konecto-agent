#!/usr/bin/env python3
"""
Test Runner Script for Konecto AI Agent

This script provides convenient commands to run the test suite with various
options and configurations.

Usage:
    python run_tests.py [command] [options]

Commands:
    all          Run all tests (default)
    unit         Run only unit tests
    coverage     Run tests with coverage report
    verbose      Run tests with verbose output
    specific     Run specific test file or test function
    watch        Run tests in watch mode (requires pytest-watch)
    clean        Clean test artifacts (coverage, cache, etc.)
    help         Show this help message
"""

import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional


class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def print_info(message: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ{Colors.NC} {message}")


def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓{Colors.NC} {message}")


def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠{Colors.NC} {message}")


def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}✗{Colors.NC} {message}")


def check_pytest() -> bool:
    """Check if pytest is installed"""
    try:
        subprocess.run(
            ["pytest", "--version"],
            capture_output=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("pytest is not installed. Please install it first:")
        print("  pip install pytest pytest-asyncio pytest-cov")
        return False


def check_pytest_cov() -> bool:
    """Check if pytest-cov is installed"""
    try:
        result = subprocess.run(
            ["pytest", "--help"],
            capture_output=True,
            text=True,
            check=True
        )
        if "--cov" in result.stdout:
            return True
        else:
            print_warning("pytest-cov is not installed. Coverage features will be disabled.")
            print("  Install with: pip install pytest-cov")
            return False
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def run_command(cmd: List[str], description: str) -> int:
    """Run a pytest command"""
    print_info(description)
    try:
        result = subprocess.run(["pytest"] + cmd, cwd=Path(__file__).parent)
        return result.returncode
    except KeyboardInterrupt:
        print_warning("\nTests interrupted by user")
        return 130
    except Exception as e:
        print_error(f"Error running tests: {e}")
        return 1


def run_all() -> int:
    """Run all tests"""
    return run_command(["tests/", "-v"], "Running all tests...")


def run_unit() -> int:
    """Run only unit tests"""
    return run_command(
        ["tests/", "-v", "-m", "unit or not integration"],
        "Running unit tests..."
    )


def run_coverage() -> int:
    """Run tests with coverage"""
    if not check_pytest_cov():
        print_error("Cannot run coverage tests. Please install pytest-cov first:")
        print("  pip install pytest-cov")
        return 1
    
    print_info("Running tests with coverage...")
    result = run_command([
        "tests/",
        "--cov=app",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-report=xml",
        "-v"
    ], "Running tests with coverage...")
    
    if result == 0:
        print_success("Coverage report generated!")
        print_info("HTML report: htmlcov/index.html")
        print_info("XML report: coverage.xml")
    
    return result


def run_verbose() -> int:
    """Run tests with verbose output"""
    return run_command(["tests/", "-vv", "-s"], "Running tests with verbose output...")


def run_specific(test_path: str) -> int:
    """Run specific test file or function"""
    if not test_path:
        print_error("Please specify a test file or test function")
        print("Usage: python run_tests.py specific tests/test_config.py")
        print("   or: python run_tests.py specific tests/test_config.py::TestSettings")
        return 1
    
    return run_command([test_path, "-v"], f"Running specific test: {test_path}")


def run_watch() -> int:
    """Run tests in watch mode"""
    try:
        subprocess.run(["ptw", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_warning("pytest-watch is not installed. Installing...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pytest-watch"], check=True)
        except subprocess.CalledProcessError:
            print_error("Failed to install pytest-watch")
            return 1
    
    print_info("Running tests in watch mode (press Ctrl+C to stop)...")
    try:
        subprocess.run(["ptw", "tests/", "--", "-v"], cwd=Path(__file__).parent)
        return 0
    except KeyboardInterrupt:
        print_warning("\nWatch mode stopped by user")
        return 130
    except Exception as e:
        print_error(f"Error in watch mode: {e}")
        return 1


def clean_artifacts() -> int:
    """Clean test artifacts"""
    print_info("Cleaning test artifacts...")
    
    script_dir = Path(__file__).parent
    cleaned = False
    
    # Remove coverage files
    htmlcov = script_dir / "htmlcov"
    if htmlcov.exists():
        shutil.rmtree(htmlcov)
        print_success("Removed htmlcov/")
        cleaned = True
    
    coverage_xml = script_dir / "coverage.xml"
    if coverage_xml.exists():
        coverage_xml.unlink()
        print_success("Removed coverage.xml")
        cleaned = True
    
    coverage_file = script_dir / ".coverage"
    if coverage_file.exists():
        coverage_file.unlink()
        print_success("Removed .coverage")
        cleaned = True
    
    # Remove pytest cache
    pytest_cache = script_dir / ".pytest_cache"
    if pytest_cache.exists():
        shutil.rmtree(pytest_cache)
        print_success("Removed .pytest_cache/")
        cleaned = True
    
    # Remove __pycache__ directories
    for pycache in script_dir.rglob("__pycache__"):
        shutil.rmtree(pycache)
        cleaned = True
    
    for pyc in script_dir.rglob("*.pyc"):
        pyc.unlink()
        cleaned = True
    
    if cleaned:
        print_success("Cleanup complete!")
    else:
        print_info("No artifacts to clean")
    
    return 0


def show_help():
    """Show help message"""
    print(__doc__)
    print("\nExamples:")
    print("  python run_tests.py                    # Run all tests")
    print("  python run_tests.py coverage           # Run with coverage")
    print("  python run_tests.py specific tests/test_config.py")
    print("  python run_tests.py specific tests/test_config.py::TestSettings::test_settings_default_values")
    print("  python run_tests.py clean              # Clean test artifacts")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        command = "all"
    else:
        command = sys.argv[1].lower()
    
    if command in ["help", "--help", "-h"]:
        show_help()
        return 0
    
    if command == "all":
        if not check_pytest():
            return 1
        return run_all()
    elif command == "unit":
        if not check_pytest():
            return 1
        return run_unit()
    elif command == "coverage":
        if not check_pytest():
            return 1
        return run_coverage()
    elif command == "verbose":
        if not check_pytest():
            return 1
        return run_verbose()
    elif command == "specific":
        if not check_pytest():
            return 1
        test_path = sys.argv[2] if len(sys.argv) > 2 else ""
        return run_specific(test_path)
    elif command == "watch":
        if not check_pytest():
            return 1
        return run_watch()
    elif command == "clean":
        return clean_artifacts()
    else:
        print_error(f"Unknown command: {command}")
        print()
        show_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

