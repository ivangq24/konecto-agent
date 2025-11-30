"""
Tests for LangChain Tools

Tests the part number search and semantic search tools.
"""

import pytest
from unittest.mock import Mock, MagicMock

from app.agent.tools.part_number_search_tool import (
    create_part_number_search_tool,
    PartNumberSearchInput,
)
from app.agent.tools.semantic_search_tool import (
    create_semantic_search_tool,
    SemanticSearchInput,
)


class TestPartNumberSearchTool:
    """Test cases for part number search tool"""
    
    def test_create_tool(self, mock_data_service):
        """Test creating the part number search tool"""
        tool = create_part_number_search_tool(mock_data_service)
        
        assert tool is not None
        assert hasattr(tool, "name")
        assert tool.name == "search_by_part_number"
    
    def test_tool_with_results(self, mock_data_service, sample_actuator_data):
        """Test tool execution with search results"""
        mock_data_service.search_by_part_number.return_value = [sample_actuator_data]
        
        tool = create_part_number_search_tool(mock_data_service)
        result = tool.invoke({"part_number": "763A00-11330C00/A"})
        
        assert "763A00-11330C00/A" in result
        assert "220V 3 Phase Power" in result
        assert "Output Torque" in result
        mock_data_service.search_by_part_number.assert_called_once_with("763A00-11330C00/A")
    
    def test_tool_no_results(self, mock_data_service):
        """Test tool execution when no results are found"""
        mock_data_service.search_by_part_number.return_value = []
        
        tool = create_part_number_search_tool(mock_data_service)
        result = tool.invoke({"part_number": "NONEXISTENT-123"})
        
        assert "No actuator found" in result
        assert "NONEXISTENT-123" in result
    
    def test_tool_no_data_service(self):
        """Test tool execution when data service is None"""
        tool = create_part_number_search_tool(None)
        result = tool.invoke({"part_number": "763A00-11330C00/A"})
        
        assert "Error" in result
        assert "not available" in result
    
    def test_part_number_search_input_schema(self):
        """Test PartNumberSearchInput schema"""
        schema = PartNumberSearchInput(part_number="763A00-11330C00/A")
        
        assert schema.part_number == "763A00-11330C00/A"


class TestSemanticSearchTool:
    """Test cases for semantic search tool"""
    
    def test_create_tool(self, mock_data_service):
        """Test creating the semantic search tool"""
        tool = create_semantic_search_tool(mock_data_service)
        
        assert tool is not None
        assert hasattr(tool, "name")
        assert tool.name == "semantic_search"
    
    def test_tool_with_results(self, mock_data_service, sample_semantic_search_results):
        """Test tool execution with search results"""
        mock_data_service.semantic_search.return_value = sample_semantic_search_results
        
        tool = create_semantic_search_tool(mock_data_service)
        result = tool.invoke({
            "query": "high torque actuator",
            "k": 2
        })
        
        assert "763A00-11330C00/A" in result
        assert "220V 3 Phase Power" in result
        assert "Relevance" in result
        mock_data_service.semantic_search.assert_called_once_with("high torque actuator", k=2)
    
    def test_tool_no_results(self, mock_data_service):
        """Test tool execution when no results are found"""
        mock_data_service.semantic_search.return_value = []
        
        tool = create_semantic_search_tool(mock_data_service)
        result = tool.invoke({
            "query": "nonexistent query",
            "k": 5
        })
        
        assert "No actuators found" in result
        assert "nonexistent query" in result
    
    def test_tool_default_k(self, mock_data_service, sample_semantic_search_results):
        """Test tool with default k value"""
        mock_data_service.semantic_search.return_value = sample_semantic_search_results
        
        tool = create_semantic_search_tool(mock_data_service)
        result = tool.invoke({"query": "test query"})
        
        # Should use default k=3
        mock_data_service.semantic_search.assert_called_once_with("test query", k=3)
    
    def test_tool_k_limits(self, mock_data_service):
        """Test that k is limited to valid range"""
        mock_data_service.semantic_search.return_value = []
        
        tool = create_semantic_search_tool(mock_data_service)
        
        # k=0 should be clamped to 1
        tool.invoke({"query": "test", "k": 0})
        mock_data_service.semantic_search.assert_called_with("test", k=1)
        
        # k=20 should be allowed (max is 20)
        tool.invoke({"query": "test", "k": 20})
        mock_data_service.semantic_search.assert_called_with("test", k=20)
        
        # k=25 should be clamped to 20
        tool.invoke({"query": "test", "k": 25})
        mock_data_service.semantic_search.assert_called_with("test", k=20)
    
    def test_tool_no_data_service(self):
        """Test tool execution when data service is None"""
        tool = create_semantic_search_tool(None)
        result = tool.invoke({"query": "test query"})
        
        assert "Error" in result
        assert "not available" in result
    
    def test_semantic_search_input_schema(self):
        """Test SemanticSearchInput schema"""
        schema = SemanticSearchInput(query="high torque", k=5)
        
        assert schema.query == "high torque"
        assert schema.k == 5
        
        # Test default k
        schema_default = SemanticSearchInput(query="test")
        assert schema_default.k == 3
