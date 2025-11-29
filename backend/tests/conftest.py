"""
Pytest Configuration and Shared Fixtures

This module provides shared fixtures and configuration for all tests.
"""

import os
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from pathlib import Path
import tempfile
import shutil

from app.config import Settings, get_settings
from app.services.data_service import DataService


@pytest.fixture
def test_settings():
    """
    Create test settings with minimal required configuration.
    
    Returns:
        Settings: Test settings instance
    """
    # Clear cache to ensure fresh settings
    get_settings.cache_clear()
    
    # Create temporary directories for test data
    temp_dir = tempfile.mkdtemp()
    
    settings = Settings(
        app_name="Test Konecto AI Agent",
        app_version="1.0.0-test",
        debug=True,
        openai_api_key="test-openai-key",
        openai_model="gpt-4o-mini",
        openai_embedding_model="text-embedding-3-small",
        data_storage="memory",
        sqlite_db_path=os.path.join(temp_dir, "test_actuators.db"),
        chroma_persist_directory=os.path.join(temp_dir, "test_chroma"),
        raw_data_path=os.path.join(temp_dir, "raw"),
        processed_data_path=os.path.join(temp_dir, "processed"),
        agent_temperature=0.0,
        agent_max_iterations=2,
        agent_verbose=False,
        langfuse_enabled=False,
    )
    
    yield settings
    
    # Cleanup
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    get_settings.cache_clear()


@pytest.fixture
def mock_data_service():
    """
    Create a mock DataService for testing.
    
    Returns:
        Mock: Mocked DataService instance
    """
    service = Mock(spec=DataService)
    service.search_by_part_number = Mock(return_value=[])
    service.semantic_search = Mock(return_value=[])
    service.initialize = AsyncMock(return_value=None)
    service.cleanup = AsyncMock(return_value=None)
    return service


@pytest.fixture
def sample_actuator_data():
    """
    Sample actuator data for testing.
    
    Returns:
        dict: Sample actuator record
    """
    return {
        "base_part_number": "763A00-11330C00/A",
        "identifier": "763A00-11330C00/A",
        "context_type": "220V 3 Phase Power",
        "output_torque_nm": 300,
        "duty_cycle_54pct": 70.0,
        "motor_power_watts": 40,
        "operating_speed_sec_60_hz": 26,
        "cycles_per_hour_cycles": 39,
        "source_table": "test_table",
    }


@pytest.fixture
def sample_semantic_search_results():
    """
    Sample semantic search results for testing.
    
    Returns:
        list: List of search result dictionaries
    """
    return [
        {
            "content": "Base Part Number: 763A00-11330C00/A. Output Torque (Nm): 300. Duty Cycle 54%: 70.0.",
            "metadata": {
                "base_part_number": "763A00-11330C00/A",
                "context_type": "220V 3 Phase Power",
            },
            "score": 0.85,
        },
        {
            "content": "Base Part Number: 764B00-11300000/A. Output Torque (Nm): 250. Duty Cycle 54%: 65.0.",
            "metadata": {
                "base_part_number": "764B00-11300000/A",
                "context_type": "110V Single Phase",
            },
            "score": 0.78,
        },
    ]


@pytest.fixture
def temp_db_path(tmp_path):
    """
    Create a temporary database path for testing.
    
    Args:
        tmp_path: Pytest temporary path fixture
        
    Returns:
        str: Path to temporary database file
    """
    db_path = tmp_path / "test_actuators.db"
    return str(db_path)


@pytest.fixture(autouse=True)
def reset_conversation_history():
    """
    Reset conversation history before each test.
    """
    try:
        from app.agent.agent import conversation_history
        conversation_history.clear()
        yield
        conversation_history.clear()
    except ImportError:
        # If agent module can't be imported (missing dependencies), skip
        yield

