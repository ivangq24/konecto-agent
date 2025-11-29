"""
Tests Module

This package contains all test cases for the Konecto AI Agent backend.

Test Structure:
- conftest.py: Shared fixtures and configuration
- test_config.py: Configuration and settings tests
- test_schemas.py: Pydantic schema validation tests
- test_data_service.py: DataService database operation tests
- test_tools.py: LangChain tools tests
- test_agent.py: ActuatorAgent tests
- test_conversation.py: API endpoint tests

Run tests with:
    pytest                    # Run all tests
    pytest -v                # Verbose output
    pytest --cov=app         # With coverage
    pytest tests/test_config.py  # Run specific test file
"""

