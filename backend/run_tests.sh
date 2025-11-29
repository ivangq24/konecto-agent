#!/bin/bash

# =============================================================================
# Test Runner Script for Konecto AI Agent
# =============================================================================
# This script provides convenient commands to run the test suite with various
# options and configurations.
#
# The script can run tests locally or in Docker. By default, it detects if
# Docker is available and uses it if the project is containerized.
#
# Usage:
#   ./run_tests.sh [command] [options]
#   ./run_tests.sh docker [command] [options]  # Force Docker execution
#   ./run_tests.sh local [command] [options]   # Force local execution
#
# Commands:
#   all          Run all tests (default)
#   unit         Run only unit tests
#   coverage     Run tests with coverage report
#   verbose      Run tests with verbose output
#   specific     Run specific test file or test function
#   watch        Run tests in watch mode (requires pytest-watch)
#   clean        Clean test artifacts (coverage, cache, etc.)
#   help         Show this help message
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SCRIPT_DIR"

# Detect execution mode
EXEC_MODE="auto"  # auto, docker, local
COMMAND="all"

# Parse execution mode
if [ "$1" == "docker" ]; then
    EXEC_MODE="docker"
    COMMAND="${2:-all}"
elif [ "$1" == "local" ]; then
    EXEC_MODE="local"
    COMMAND="${2:-all}"
else
    COMMAND="${1:-all}"
fi

# Function to check if Docker is available
check_docker() {
    if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
        if [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
            return 0
        fi
    fi
    return 1
}

# Function to detect if we should use Docker
should_use_docker() {
    if [ "$EXEC_MODE" == "docker" ]; then
        return 0
    elif [ "$EXEC_MODE" == "local" ]; then
        return 1
    else
        # Auto-detect: use Docker if available and docker-compose.yml exists
        check_docker
    fi
}

# Function to run command in Docker
run_in_docker() {
    local cmd_args=("$@")
    print_info "Running tests in Docker container..."
    cd "$PROJECT_ROOT"
    docker-compose exec -T backend pytest "${cmd_args[@]}"
}

# Function to run command locally
run_locally() {
    local cmd_args=("$@")
    print_info "Running tests locally..."
    pytest "${cmd_args[@]}"
}

# Function to execute pytest command
run_pytest() {
    local cmd_args=("$@")
    if should_use_docker; then
        if ! check_docker; then
            print_error "Docker is not available. Falling back to local execution."
            run_locally "${cmd_args[@]}"
        else
            run_in_docker "${cmd_args[@]}"
        fi
    else
        run_locally "${cmd_args[@]}"
    fi
}

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to check if pytest is installed
check_pytest() {
    if ! command -v pytest &> /dev/null; then
        print_error "pytest is not installed. Please install it first:"
        echo "  pip install pytest pytest-asyncio pytest-cov"
        exit 1
    fi
}

# Function to check if pytest-cov is installed
check_pytest_cov() {
    if ! pytest --help | grep -q "\-\-cov"; then
        print_warning "pytest-cov is not installed. Coverage features will be disabled."
        echo "  Install with: pip install pytest-cov"
        return 1
    fi
    return 0
}

# Function to run all tests
run_all() {
    run_pytest tests/ -v
}

# Function to run unit tests only
run_unit() {
    run_pytest tests/ -v -m "unit or not integration"
}

# Function to run tests with coverage
run_coverage() {
    if should_use_docker; then
        # In Docker, pytest-cov should be installed
        print_info "Running tests with coverage in Docker..."
        run_pytest tests/ \
            --cov=app \
            --cov-report=term-missing \
            --cov-report=html \
            --cov-report=xml \
            -v
        
        if [ $? -eq 0 ]; then
            print_success "Coverage report generated in Docker container!"
            print_info "To view HTML report, copy from container:"
            print_info "  docker-compose exec backend cat htmlcov/index.html"
        fi
    else
        if ! check_pytest_cov; then
            print_error "Cannot run coverage tests. Please install pytest-cov first:"
            echo "  pip install pytest-cov"
            echo "  Or run in Docker: ./run_tests.sh docker coverage"
            exit 1
        fi
        
        print_info "Running tests with coverage..."
        run_pytest tests/ \
            --cov=app \
            --cov-report=term-missing \
            --cov-report=html \
            --cov-report=xml \
            -v
        
        if [ $? -eq 0 ]; then
            print_success "Coverage report generated!"
            print_info "HTML report: htmlcov/index.html"
            print_info "XML report: coverage.xml"
        fi
    fi
}

# Function to run tests with verbose output
run_verbose() {
    run_pytest tests/ -vv -s
}

# Function to run specific test
run_specific() {
    local test_path
    if should_use_docker; then
        test_path="${2:-${COMMAND}}"
    else
        test_path="${2:-${COMMAND}}"
    fi
    
    if [ -z "$test_path" ] || [ "$test_path" == "specific" ]; then
        print_error "Please specify a test file or test function"
        echo "Usage: ./run_tests.sh specific tests/test_config.py"
        echo "   or: ./run_tests.sh docker specific tests/test_config.py::TestSettings"
        exit 1
    fi
    
    run_pytest "$test_path" -v
}

# Function to run tests in watch mode
run_watch() {
    if should_use_docker; then
        print_info "Running tests in watch mode in Docker (press Ctrl+C to stop)..."
        cd "$PROJECT_ROOT"
        docker-compose exec backend ptw tests/ -- -v
    else
        if ! command -v ptw &> /dev/null; then
            print_warning "pytest-watch is not installed. Installing..."
            pip install pytest-watch
        fi
        
        print_info "Running tests in watch mode (press Ctrl+C to stop)..."
        ptw tests/ -- -v
    fi
}

# Function to clean test artifacts
clean_artifacts() {
    if should_use_docker; then
        print_info "Cleaning test artifacts in Docker container..."
        cd "$PROJECT_ROOT"
        docker-compose exec backend sh -c "
            rm -rf htmlcov coverage.xml .coverage .pytest_cache
            find . -type d -name '__pycache__' -exec rm -r {} + 2>/dev/null || true
            find . -type f -name '*.pyc' -delete 2>/dev/null || true
        "
        print_success "Cleanup complete in Docker container!"
    else
        print_info "Cleaning test artifacts..."
        
        # Remove coverage files
        if [ -d "htmlcov" ]; then
            rm -rf htmlcov
            print_success "Removed htmlcov/"
        fi
        
        if [ -f "coverage.xml" ]; then
            rm -f coverage.xml
            print_success "Removed coverage.xml"
        fi
        
        if [ -f ".coverage" ]; then
            rm -f .coverage
            print_success "Removed .coverage"
        fi
        
        # Remove pytest cache
        if [ -d ".pytest_cache" ]; then
            rm -rf .pytest_cache
            print_success "Removed .pytest_cache/"
        fi
        
        # Remove __pycache__ directories
        find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
        find . -type f -name "*.pyc" -delete 2>/dev/null || true
        
        print_success "Cleanup complete!"
    fi
}

# Function to show help
show_help() {
    echo "============================================================================="
    echo "Test Runner Script for Konecto AI Agent"
    echo "============================================================================="
    echo ""
    echo "Usage:"
    echo "  ./run_tests.sh [command] [options]"
    echo "  ./run_tests.sh docker [command] [options]  # Force Docker execution"
    echo "  ./run_tests.sh local [command] [options]   # Force local execution"
    echo ""
    echo "Commands:"
    echo "  all          Run all tests (default)"
    echo "  unit         Run only unit tests"
    echo "  coverage     Run tests with coverage report"
    echo "  verbose      Run tests with verbose output"
    echo "  specific     Run specific test file or test function"
    echo "  watch        Run tests in watch mode (requires pytest-watch)"
    echo "  clean        Clean test artifacts (coverage, cache, etc.)"
    echo "  help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run_tests.sh                    # Run all tests (auto-detect Docker/local)"
    echo "  ./run_tests.sh docker all         # Run all tests in Docker"
    echo "  ./run_tests.sh local coverage     # Run with coverage locally"
    echo "  ./run_tests.sh docker specific tests/test_config.py"
    echo "  ./run_tests.sh docker coverage    # Run with coverage in Docker"
    echo "  ./run_tests.sh clean              # Clean test artifacts"
    echo ""
    echo "Options:"
    echo "  -h, --help   Show this help message"
    echo ""
}

# Main execution
case "$COMMAND" in
    all)
        check_pytest
        run_all
        ;;
    unit)
        check_pytest
        run_unit
        ;;
    coverage)
        check_pytest
        run_coverage
        ;;
    verbose)
        check_pytest
        run_verbose
        ;;
    specific)
        check_pytest
        run_specific "$@"
        ;;
    watch)
        check_pytest
        run_watch
        ;;
    clean)
        clean_artifacts
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        echo ""
        show_help
        exit 1
        ;;
esac

