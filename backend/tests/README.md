# Test Suite Documentation

This directory contains the complete test suite for the Konecto AI Agent backend.

## Test Structure

### Test Files

- **`conftest.py`**: Shared fixtures and test configuration
- **`test_config.py`**: Tests for application configuration and settings
- **`test_schemas.py`**: Tests for Pydantic request/response schemas
- **`test_data_service.py`**: Tests for DataService (SQLite and ChromaDB operations)
- **`test_tools.py`**: Tests for LangChain tools (part number search, semantic search)
- **`test_agent.py`**: Tests for ActuatorAgent class and message processing
- **`test_conversation.py`**: Tests for FastAPI conversation endpoint

## Running Tests

### Using Test Scripts (Recommended)

The easiest way to run tests is using the provided scripts:

```bash
# From backend/ directory

# Run all tests (auto-detects Docker/local)
./run_tests.sh

# Force Docker execution
./run_tests.sh docker all

# Force local execution
./run_tests.sh local all

# Run with coverage (in Docker)
./run_tests.sh docker coverage

# Run specific test
./run_tests.sh docker specific tests/test_config.py

# Or use the dedicated Docker script
./run_tests_docker.sh coverage
```

### Direct pytest Commands

#### In Docker (Recommended)

```bash
# Run all tests
docker-compose exec backend pytest

# Run with verbose output
docker-compose exec backend pytest -v

# Run specific test file
docker-compose exec backend pytest tests/test_config.py

# Run with coverage
docker-compose exec backend pytest --cov=app --cov-report=term-missing
```

#### Locally (requires all dependencies)

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_config.py

# Run specific test class
pytest tests/test_config.py::TestSettings

# Run specific test function
pytest tests/test_config.py::TestSettings::test_settings_default_values
```

### With Coverage

```bash
# In Docker (recommended - all dependencies available)
docker-compose exec backend pytest --cov=app --cov-report=term-missing

# Generate HTML coverage report
docker-compose exec backend pytest --cov=app --cov-report=html

# View coverage report (copy from container or use volume mount)
docker-compose exec backend cat htmlcov/index.html
```

### Async Tests

All async tests are automatically handled by `pytest-asyncio` with `asyncio-mode=auto`.

## Test Fixtures

### Available Fixtures (from `conftest.py`)

- **`test_settings`**: Test Settings instance with minimal configuration
- **`mock_data_service`**: Mocked DataService for testing
- **`sample_actuator_data`**: Sample actuator record for testing
- **`sample_semantic_search_results`**: Sample semantic search results
- **`temp_db_path`**: Temporary database path for SQLite tests
- **`reset_conversation_history`**: Auto-reset conversation history between tests

## Writing New Tests

### Example Test Structure

```python
import pytest
from unittest.mock import Mock

class TestMyFeature:
    """Test cases for MyFeature"""
    
    def test_basic_functionality(self, test_settings):
        """Test basic functionality"""
        # Arrange
        # Act
        # Assert
        pass
    
    @pytest.mark.asyncio
    async def test_async_functionality(self, mock_data_service):
        """Test async functionality"""
        # Test async code
        pass
```

### Best Practices

1. **Use descriptive test names**: Test names should clearly describe what they test
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Use fixtures**: Leverage shared fixtures from `conftest.py`
4. **Mock external dependencies**: Mock API calls, database operations, etc.
5. **Test edge cases**: Include tests for error conditions and edge cases
6. **Keep tests isolated**: Each test should be independent and not rely on others

## Test Coverage Goals

- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test component interactions
- **API Tests**: Test HTTP endpoints and request/response handling

## Continuous Integration

Tests should be run automatically in CI/CD pipelines. Ensure all tests pass before merging code.

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure you're running tests from the project root
2. **Async test failures**: Ensure `pytest-asyncio` is installed and configured
3. **Database errors**: Tests use temporary databases, but ensure SQLite is available
4. **Mock issues**: Verify mocks are properly configured for async functions

### Debug Mode

```bash
# Run tests with debug output
pytest -v -s

# Run with pdb on failure
pytest --pdb
```

