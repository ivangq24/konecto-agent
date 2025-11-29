"""
Tests for ActuatorAgent Module

Tests the ActuatorAgent class and its message processing functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch

from app.agent.agent import ActuatorAgent
from app.config import Settings
from app.services.data_service import DataService


class TestActuatorAgent:
    """Test cases for ActuatorAgent class"""
    
    def test_agent_initialization(self, test_settings, mock_data_service):
        """Test agent initialization"""
        with patch('app.agent.agent.ChatOpenAI') as mock_llm:
            with patch('app.agent.agent.create_openai_tools_agent') as mock_create_agent:
                with patch('app.agent.agent.AgentExecutor') as mock_executor_class:
                    # Create a proper mock agent that passes validation
                    from langchain_core.runnables import Runnable
                    mock_agent = MagicMock(spec=Runnable)
                    mock_create_agent.return_value = mock_agent
                    
                    mock_executor = MagicMock()
                    mock_executor_class.return_value = mock_executor
                    
                    agent = ActuatorAgent(settings=test_settings, data_service=mock_data_service)
                    
                    assert agent.settings == test_settings
                    assert agent.data_service == mock_data_service
                    assert len(agent.tools) == 2
                    assert agent.agent_executor is not None
    
    @pytest.mark.asyncio
    async def test_process_message_exact_search(self, test_settings, mock_data_service, sample_actuator_data):
        """Test processing a message that triggers exact part number search"""
        mock_data_service.search_by_part_number.return_value = [sample_actuator_data]
        
        # Mock agent executor
        mock_executor = AsyncMock()
        mock_executor.invoke.return_value = {
            "output": "The actuator 763A00-11330C00/A has the following specifications...",
        }
        
        with patch('app.agent.agent.ChatOpenAI'):
            with patch('app.agent.agent.create_openai_tools_agent') as mock_create_agent:
                with patch('app.agent.agent.AgentExecutor') as mock_executor_class:
                    from langchain_core.runnables import Runnable
                    mock_agent = MagicMock(spec=Runnable)
                    mock_create_agent.return_value = mock_agent
                    mock_executor_class.return_value = mock_executor
                    
                    agent = ActuatorAgent(settings=test_settings, data_service=mock_data_service)
                    
                    response = await agent.process_message(
                        message="What is actuator 763A00-11330C00/A?",
                        conversation_id="test-123"
                    )
                    
                    assert "response" in response
                    assert "conversation_id" in response
                    assert response["conversation_id"] == "test-123"
                    mock_executor.invoke.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_message_semantic_search(self, test_settings, mock_data_service):
        """Test processing a message that triggers semantic search"""
        mock_data_service.semantic_search.return_value = []
        
        mock_executor = AsyncMock()
        mock_executor.invoke.return_value = {
            "output": "Here are some actuators that match your requirements...",
        }
        
        with patch('app.agent.agent.ChatOpenAI'):
            with patch('app.agent.agent.create_openai_tools_agent') as mock_create_agent:
                with patch('app.agent.agent.AgentExecutor') as mock_executor_class:
                    from langchain_core.runnables import Runnable
                    mock_agent = MagicMock(spec=Runnable)
                    mock_create_agent.return_value = mock_agent
                    mock_executor_class.return_value = mock_executor
                    
                    agent = ActuatorAgent(settings=test_settings, data_service=mock_data_service)
                    
                    response = await agent.process_message(
                        message="I need a high torque actuator",
                        conversation_id="test-456"
                    )
                    
                    assert "response" in response
                    assert response["conversation_id"] == "test-456"
    
    @pytest.mark.asyncio
    async def test_process_message_conversation_history(self, test_settings, mock_data_service):
        """Test that conversation history is maintained"""
        mock_invoke = Mock(return_value={"output": "Response"})
        
        with patch('app.agent.agent.ChatOpenAI'):
            with patch('app.agent.agent.create_openai_tools_agent') as mock_create_agent:
                with patch('app.agent.agent.AgentExecutor') as mock_executor_class:
                    with patch('asyncio.to_thread') as mock_to_thread:
                        from langchain_core.runnables import Runnable
                        mock_agent = MagicMock(spec=Runnable)
                        mock_create_agent.return_value = mock_agent
                        
                        mock_executor = MagicMock()
                        mock_executor.invoke = mock_invoke
                        mock_executor_class.return_value = mock_executor
                        mock_to_thread.side_effect = lambda fn, *args: fn(*args)
                        
                        agent = ActuatorAgent(settings=test_settings, data_service=mock_data_service)
                        
                        # First message
                        await agent.process_message(
                            message="I need single phase",
                            conversation_id="conv-1"
                        )
                        
                        # Second message - should include history
                        await agent.process_message(
                            message="110V",
                            conversation_id="conv-1"
                        )
                        
                        # Verify that invoke was called with history
                        assert mock_invoke.call_count == 2
                        # Check that second call includes conversation history
                        second_call_args = mock_invoke.call_args_list[1]
                        assert "chat_history" in second_call_args[0][0]
                        assert len(second_call_args[0][0]["chat_history"]) > 0
    
    @pytest.mark.asyncio
    async def test_process_message_new_conversation(self, test_settings, mock_data_service):
        """Test that new conversation_id starts fresh history"""
        mock_invoke = Mock(return_value={"output": "Response"})
        
        with patch('app.agent.agent.ChatOpenAI'):
            with patch('app.agent.agent.create_openai_tools_agent') as mock_create_agent:
                with patch('app.agent.agent.AgentExecutor') as mock_executor_class:
                    with patch('asyncio.to_thread') as mock_to_thread:
                        from langchain_core.runnables import Runnable
                        mock_agent = MagicMock(spec=Runnable)
                        mock_create_agent.return_value = mock_agent
                        
                        mock_executor = MagicMock()
                        mock_executor.invoke = mock_invoke
                        mock_executor_class.return_value = mock_executor
                        mock_to_thread.side_effect = lambda fn, *args: fn(*args)
                        
                        agent = ActuatorAgent(settings=test_settings, data_service=mock_data_service)
                        
                        # First conversation
                        await agent.process_message(
                            message="Message 1",
                            conversation_id="conv-1"
                        )
                        
                        # New conversation
                        await agent.process_message(
                            message="Message 2",
                            conversation_id="conv-2"
                        )
                        
                        # Verify both conversations exist separately
                        from app.agent.agent import conversation_history
                        assert "conv-1" in conversation_history
                        assert "conv-2" in conversation_history
    
    @pytest.mark.asyncio
    async def test_process_message_error_handling(self, test_settings, mock_data_service):
        """Test error handling in process_message"""
        mock_invoke = Mock(side_effect=Exception("Test error"))
        
        with patch('app.agent.agent.ChatOpenAI'):
            with patch('app.agent.agent.create_openai_tools_agent') as mock_create_agent:
                with patch('app.agent.agent.AgentExecutor') as mock_executor_class:
                    with patch('asyncio.to_thread') as mock_to_thread:
                        from langchain_core.runnables import Runnable
                        mock_agent = MagicMock(spec=Runnable)
                        mock_create_agent.return_value = mock_agent
                        
                        mock_executor = MagicMock()
                        mock_executor.invoke = mock_invoke
                        mock_executor_class.return_value = mock_executor
                        mock_to_thread.side_effect = lambda fn, *args: fn(*args)
                        
                        agent = ActuatorAgent(settings=test_settings, data_service=mock_data_service)
                        
                        # process_message should catch the exception and return error message
                        response = await agent.process_message(
                            message="Test message",
                            conversation_id="test-123"
                        )
                        
                        # Should return error message, not raise exception
                        assert "response" in response
                        assert "error" in response["response"].lower() or "occurred" in response["response"].lower()
