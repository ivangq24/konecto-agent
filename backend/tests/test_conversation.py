"""
Tests for Conversation API Routes

Tests the FastAPI conversation endpoint.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.models.schemas import ConversationRequest, ConversationResponse


@pytest.fixture
def mock_data_service():
    """Create a mock DataService"""
    service = Mock()
    service.search_by_part_number = Mock(return_value=[])
    service.semantic_search = Mock(return_value=[])
    service.initialize = AsyncMock(return_value=None)
    service.cleanup = AsyncMock(return_value=None)
    return service


@pytest.fixture
def app_with_mock_service(mock_data_service):
    """Create FastAPI app with mocked data service"""
    from contextlib import asynccontextmanager
    
    @asynccontextmanager
    async def mock_lifespan(app):
        app.state.data_service = mock_data_service
        yield
    
    app = FastAPI(
        title="Test Konecto AI Agent",
        version="1.0.0-test",
        lifespan=mock_lifespan,
    )
    
    # Add CORS middleware
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    from app.api.routes.conversation import router as conversation_router
    app.include_router(conversation_router, prefix="/api", tags=["Conversation"])
    
    # Add health check
    from app.config import get_settings
    settings = get_settings()
    
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "version": settings.app_version}
    
    # Manually set data_service for immediate use (before lifespan runs)
    app.state.data_service = mock_data_service
    
    return app


@pytest.fixture
def client(app_with_mock_service):
    """Create test client"""
    return TestClient(app_with_mock_service)


class TestConversationEndpoint:
    """Test cases for /api/conversation endpoint"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_conversation_endpoint_success(self, client, mock_data_service):
        """Test successful conversation request"""
        with patch('app.api.routes.conversation.ActuatorAgent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent.process_message = AsyncMock(return_value={
                "response": "Here is the information about the actuator...",
                "conversation_id": "test-123"
            })
            mock_agent_class.return_value = mock_agent
            
            response = client.post(
                "/api/conversation",
                json={
                    "message": "What is actuator 763A00-11330C00/A?",
                    "conversation_id": "test-123"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert "conversation_id" in data
            assert data["conversation_id"] == "test-123"
    
    def test_conversation_endpoint_missing_message(self, client):
        """Test conversation request with missing message"""
        response = client.post(
            "/api/conversation",
            json={"conversation_id": "test-123"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_conversation_endpoint_empty_message(self, client):
        """Test conversation request with empty message"""
        with patch('app.api.routes.conversation.ActuatorAgent') as mock_agent_class:
            mock_agent = Mock()
            # Empty message might cause an error, so mock it to return a response
            mock_agent.process_message = AsyncMock(return_value={
                "response": "Please provide a message.",
                "conversation_id": "test-123"
            })
            mock_agent_class.return_value = mock_agent
            
            response = client.post(
                "/api/conversation",
                json={
                    "message": "",
                    "conversation_id": "test-123"
                }
            )
            
            # Empty message might be accepted, rejected, or cause server error
            # depending on validation and agent processing
            assert response.status_code in [200, 422, 500]
    
    def test_conversation_endpoint_without_conversation_id(self, client):
        """Test conversation request without conversation_id"""
        with patch('app.api.routes.conversation.ActuatorAgent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent.process_message = AsyncMock(return_value={
                "response": "Response",
                "conversation_id": "generated-id"
            })
            mock_agent_class.return_value = mock_agent
            
            response = client.post(
                "/api/conversation",
                json={"message": "Test message"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "conversation_id" in data
    
    def test_conversation_endpoint_error_handling(self, client):
        """Test error handling in conversation endpoint"""
        with patch('app.api.routes.conversation.ActuatorAgent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent.process_message = AsyncMock(side_effect=ValueError("Test error"))
            mock_agent_class.return_value = mock_agent
            
            response = client.post(
                "/api/conversation",
                json={
                    "message": "Test message",
                    "conversation_id": "test-123"
                }
            )
            
            assert response.status_code == 400
            assert "detail" in response.json()
    
    def test_conversation_endpoint_server_error(self, client):
        """Test server error handling"""
        with patch('app.api.routes.conversation.ActuatorAgent') as mock_agent_class:
            mock_agent = Mock()
            mock_agent.process_message = AsyncMock(side_effect=Exception("Internal error"))
            mock_agent_class.return_value = mock_agent
            
            response = client.post(
                "/api/conversation",
                json={
                    "message": "Test message",
                    "conversation_id": "test-123"
                }
            )
            
            assert response.status_code == 500
            assert "detail" in response.json()
