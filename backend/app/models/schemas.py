"""Pydantic schemas for API requests and responses"""

from typing import Optional
from pydantic import BaseModel, Field


class ConversationRequest(BaseModel):
    """Request schema for conversation endpoint"""
    message: str = Field(..., description="User's message/query")
    conversation_id: Optional[str] = Field(
        None, 
        description="Optional conversation ID for maintaining context"
    )


class ConversationResponse(BaseModel):
    """Response schema for conversation endpoint"""
    response: str = Field(..., description="Agent's response")
    conversation_id: str = Field(..., description="Conversation ID")
