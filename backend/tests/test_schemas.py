"""
Tests for Pydantic Schemas

Tests the request and response schemas for API endpoints.
"""

import pytest
from pydantic import ValidationError

from app.models.schemas import ConversationRequest, ConversationResponse


class TestConversationRequest:
    """Test cases for ConversationRequest schema"""
    
    def test_valid_request(self):
        """Test creating a valid conversation request"""
        request = ConversationRequest(
            message="What is actuator 763A00-11330C00/A?",
            conversation_id="test-conv-123"
        )
        
        assert request.message == "What is actuator 763A00-11330C00/A?"
        assert request.conversation_id == "test-conv-123"
    
    def test_request_without_conversation_id(self):
        """Test request without optional conversation_id"""
        request = ConversationRequest(message="Hello")
        
        assert request.message == "Hello"
        assert request.conversation_id is None
    
    def test_request_missing_message(self):
        """Test that message is required"""
        with pytest.raises(ValidationError):
            ConversationRequest()
    
    def test_request_empty_message(self):
        """Test that empty message is allowed (validation happens at API level)"""
        request = ConversationRequest(message="")
        assert request.message == ""


class TestConversationResponse:
    """Test cases for ConversationResponse schema"""
    
    def test_valid_response(self):
        """Test creating a valid conversation response"""
        response = ConversationResponse(
            response="Here is the information about actuator 763A00-11330C00/A...",
            conversation_id="test-conv-123"
        )
        
        assert "actuator 763A00-11330C00/A" in response.response
        assert response.conversation_id == "test-conv-123"
    
    def test_response_missing_fields(self):
        """Test that all fields are required"""
        with pytest.raises(ValidationError):
            ConversationResponse(response="Test")
        
        with pytest.raises(ValidationError):
            ConversationResponse(conversation_id="test-123")
    
    def test_response_empty_strings(self):
        """Test response with empty strings"""
        response = ConversationResponse(
            response="",
            conversation_id=""
        )
        
        assert response.response == ""
        assert response.conversation_id == ""

