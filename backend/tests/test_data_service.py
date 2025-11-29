"""
Tests for DataService Module

Tests the DataService class for database operations.
"""

import pytest
import sqlite3
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from app.services.data_service import DataService
from app.config import Settings


class TestDataService:
    """Test cases for DataService class"""
    
    @pytest.mark.asyncio
    async def test_initialize_sqlite(self, test_settings, temp_db_path):
        """Test SQLite initialization"""
        test_settings.sqlite_db_path = temp_db_path
        test_settings.data_storage = "sqlite"
        
        service = DataService(test_settings)
        await service.initialize()
        
        assert service.sqlite_conn is not None
        assert service.vectorstore is None  # ChromaDB not initialized
        
        await service.cleanup()
        assert service.sqlite_conn is None
    
    @pytest.mark.asyncio
    async def test_initialize_chromadb(self, test_settings):
        """Test ChromaDB initialization when directory exists"""
        # Create a mock ChromaDB directory
        chroma_dir = Path(test_settings.chroma_persist_directory)
        chroma_dir.mkdir(parents=True, exist_ok=True)
        
        with patch('app.services.data_service.Chroma') as mock_chroma:
            with patch('app.services.data_service.OpenAIEmbeddings') as mock_embeddings:
                mock_vectorstore = MagicMock()
                mock_chroma.return_value = mock_vectorstore
                
                service = DataService(test_settings)
                await service.initialize()
                
                # ChromaDB should be initialized if directory exists
                # (actual behavior depends on directory existence)
                
                await service.cleanup()
    
    @pytest.mark.asyncio
    async def test_cleanup(self, test_settings, temp_db_path):
        """Test cleanup of resources"""
        test_settings.sqlite_db_path = temp_db_path
        service = DataService(test_settings)
        await service.initialize()
        
        assert service.sqlite_conn is not None
        
        await service.cleanup()
        
        assert service.sqlite_conn is None
        assert service.vectorstore is None
        assert service.embeddings is None
    
    def test_search_by_part_number_found(self, test_settings, temp_db_path, sample_actuator_data):
        """Test searching by part number when result is found"""
        # Create test database with sample data
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS actuators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                base_part_number TEXT NOT NULL,
                data_json TEXT NOT NULL,
                UNIQUE(base_part_number)
            )
        """)
        
        data_json = json.dumps(sample_actuator_data)
        cursor.execute(
            "INSERT INTO actuators (base_part_number, data_json) VALUES (?, ?)",
            (sample_actuator_data["base_part_number"], data_json)
        )
        conn.commit()
        conn.close()
        
        # Test search
        test_settings.sqlite_db_path = temp_db_path
        service = DataService(test_settings)
        service.sqlite_conn = sqlite3.connect(temp_db_path, check_same_thread=False)
        service.sqlite_conn.row_factory = sqlite3.Row
        
        results = service.search_by_part_number("763A00-11330C00/A")
        
        assert len(results) > 0
        assert results[0]["base_part_number"] == "763A00-11330C00/A"
        assert results[0]["context_type"] == "220V 3 Phase Power"
        
        service.sqlite_conn.close()
    
    def test_search_by_part_number_not_found(self, test_settings, temp_db_path):
        """Test searching by part number when no result is found"""
        test_settings.sqlite_db_path = temp_db_path
        service = DataService(test_settings)
        service.sqlite_conn = sqlite3.connect(temp_db_path, check_same_thread=False)
        service.sqlite_conn.row_factory = sqlite3.Row
        
        results = service.search_by_part_number("NONEXISTENT-123")
        
        assert len(results) == 0
        
        service.sqlite_conn.close()
    
    def test_search_by_part_number_no_connection(self, test_settings):
        """Test search when SQLite connection is not initialized"""
        service = DataService(test_settings)
        service.sqlite_conn = None
        
        results = service.search_by_part_number("763A00-11330C00/A")
        
        assert results == []
    
    def test_semantic_search_no_vectorstore(self, test_settings):
        """Test semantic search when vectorstore is not initialized"""
        service = DataService(test_settings)
        service.vectorstore = None
        
        results = service.semantic_search("high torque actuator")
        
        assert results == []
    
    def test_semantic_search_with_results(self, test_settings, sample_semantic_search_results):
        """Test semantic search with mock results"""
        service = DataService(test_settings)
        
        # Mock vectorstore
        mock_vectorstore = MagicMock()
        mock_docs = [
            (MagicMock(page_content=result["content"], metadata=result["metadata"]), result["score"])
            for result in sample_semantic_search_results
        ]
        mock_vectorstore.similarity_search_with_score.return_value = mock_docs
        service.vectorstore = mock_vectorstore
        
        results = service.semantic_search("high torque actuator", k=2)
        
        assert len(results) == 2
        assert results[0]["metadata"]["base_part_number"] == "763A00-11330C00/A"
        assert results[0]["score"] == 0.85

