"""
Conversation API Route Module

This module provides the main conversation endpoint for the Konecto AI Agent API.
It handles user queries about Series 76 Electric Actuators and returns intelligent
responses from the AI agent.

The endpoint:
- Accepts user messages and optional conversation IDs for context
- Initializes the ActuatorAgent with data service dependencies
- Processes queries using the agent's tools (SQLite exact search, ChromaDB semantic search)
- Returns structured responses with conversation tracking

Flow:
1. User sends message via POST /conversation
2. Agent analyzes query and selects appropriate tool(s)
3. Agent searches SQLite (exact part numbers) or ChromaDB (semantic queries)
4. Agent formulates response based on search results
5. Response returned with conversation ID for context tracking
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Annotated

from app.agent.agent import ActuatorAgent
from app.config import Settings, get_settings
from app.models.schemas import ConversationRequest, ConversationResponse
from app.services.data_service import DataService

router = APIRouter()


def get_data_service(request: Request) -> DataService:
    """
    Dependency function to retrieve DataService from application state.
    
    The DataService is initialized during application startup and stored in
    app.state.data_service. This dependency injects it into route handlers.
    
    Args:
        request: FastAPI Request object containing application state
        
    Returns:
        DataService: Initialized data service instance
        
    Raises:
        HTTPException: If data service is not available (500 status)
    """
    data_service = getattr(request.app.state, "data_service", None)
    if data_service is None:
        raise HTTPException(
            status_code=500,
            detail="Data service not initialized. Please check application startup."
        )
    return data_service


@router.post("/conversation", response_model=ConversationResponse)
async def conversation(
    request: ConversationRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    data_service: Annotated[DataService, Depends(get_data_service)],
) -> ConversationResponse:
    """
    Process user query and return agent response.
    
    This endpoint handles natural language queries about Series 76 Electric Actuators.
    The agent intelligently selects the appropriate search method:
    - Exact search (SQLite): When user provides a Base Part Number
    - Semantic search (ChromaDB): When user describes requirements or asks questions
    
    The agent can:
    - Answer questions about specific actuators by Base Part Number
    - Recommend actuators based on technical requirements (voltage, torque, speed, etc.)
    - Ask clarifying questions when requirements are incomplete
    - Maintain conversation context across multiple messages
    
    Args:
        request: Conversation request containing user message and optional conversation ID
        settings: Application settings (injected via dependency)
        data_service: Data service for database access (injected via dependency)
        
    Returns:
        ConversationResponse: Contains agent's response and conversation ID
        
    Raises:
        HTTPException: 
            - 400: Invalid request parameters or malformed query
            - 500: Internal server error during agent processing or database access
    """
    try:
        # Initialize the agent with the data service
        agent = ActuatorAgent(settings=settings, data_service=data_service)
        
        # Process the conversation
        response = await agent.process_message(
            message=request.message,
            conversation_id=request.conversation_id,
        )
        
        return ConversationResponse(
            response=response["response"],
            conversation_id=response["conversation_id"],
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        # Re-raise HTTP exceptions 
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your request: {str(e)}"
        )

