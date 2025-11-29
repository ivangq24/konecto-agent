"""
Tests for Application Configuration Module

Tests the Settings class and configuration loading functionality.
"""

import os
import pytest
from unittest.mock import patch

from app.config import Settings, get_settings


class TestSettings:
    """Test cases for Settings class"""
    
    def test_settings_default_values(self):
        """Test that Settings has correct default values"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            settings = Settings()
            
            assert settings.app_name == "Konecto AI Agent"
            assert settings.app_version == "1.0.0"
            assert settings.debug is False
            assert settings.openai_model == "gpt-4.1-mini"  
            assert settings.openai_embedding_model == "text-embedding-3-small"
            assert settings.data_storage == "sqlite"
            assert settings.agent_temperature == 0.0
            assert settings.agent_max_iterations == 3
    
    def test_settings_required_fields(self):
        """Test that required fields are enforced"""
        # Pydantic Settings reads from both environment variables and .env file
        # To test required field validation, we need to prevent reading from .env
        # and remove the key from environment
        
        # Temporarily remove OPENAI_API_KEY from environment
        original_key = os.environ.pop("OPENAI_API_KEY", None)
        
        try:
            # Clear cache to ensure fresh settings
            from app.config import get_settings
            get_settings.cache_clear()
            
            # Create Settings instance without env_file to avoid reading .env
            with pytest.raises(Exception):  # Pydantic validation error
                Settings(_env_file=None)  # Don't read from .env file
        finally:
            # Restore original key if it existed
            if original_key:
                os.environ["OPENAI_API_KEY"] = original_key
            
            # Restore cache
            from app.config import get_settings
            get_settings.cache_clear()
    
    def test_settings_from_env(self):
        """Test loading settings from environment variables"""
        env_vars = {
            "OPENAI_API_KEY": "test-key-123",
            "OPENAI_MODEL": "gpt-4",
            "DATA_STORAGE": "chroma",
            "AGENT_TEMPERATURE": "0.5",
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            
            assert settings.openai_api_key == "test-key-123"
            assert settings.openai_model == "gpt-4"
            assert settings.data_storage == "chroma"
            assert settings.agent_temperature == 0.5
    
    def test_settings_data_storage_validation(self):
        """Test that data_storage only accepts valid values"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            # Valid values
            settings = Settings(data_storage="sqlite")
            assert settings.data_storage == "sqlite"
            
            settings = Settings(data_storage="chroma")
            assert settings.data_storage == "chroma"
            
            settings = Settings(data_storage="memory")
            assert settings.data_storage == "memory"
            
            # Invalid value should raise validation error
            with pytest.raises(Exception):
                Settings(data_storage="invalid")
    
    def test_get_settings_caching(self):
        """Test that get_settings uses caching"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            settings1 = get_settings()
            settings2 = get_settings()
            
            # Should return the same instance (cached)
            assert settings1 is settings2
    
    def test_get_settings_cache_clear(self):
        """Test that cache can be cleared"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            settings1 = get_settings()
            
            get_settings.cache_clear()
            
            settings2 = get_settings()
            
            # Should be different instances after cache clear
            assert settings1 is not settings2
    
    def test_langfuse_configuration(self):
        """Test Langfuse configuration settings"""
        env_vars = {
            "OPENAI_API_KEY": "test-key",
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
            "LANGFUSE_HOST": "https://custom.langfuse.com",
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            
            assert settings.langfuse_enabled is True
            assert settings.langfuse_public_key == "pk-test"
            assert settings.langfuse_secret_key == "sk-test"
            assert settings.langfuse_host == "https://custom.langfuse.com"

