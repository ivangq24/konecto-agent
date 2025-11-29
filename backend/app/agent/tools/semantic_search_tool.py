"""
Semantic Search Tool Module

This module provides a LangChain tool for performing semantic similarity searches
in ChromaDB using vector embeddings. The tool enables the AI agent to find actuators
based on natural language descriptions of requirements, even when exact keywords
don't match.

The tool:
- Accepts natural language queries describing actuator requirements
- Uses ChromaDB vector similarity search to find semantically related actuators
- Returns formatted results with relevance scores
- Handles errors gracefully and provides informative messages

Use Cases:
- User describes requirements (e.g., "high torque 110V actuator")
- User asks vague questions (e.g., "What actuators work with single phase?")
- User requests recommendations based on specifications
- User asks about technical characteristics without exact part numbers
"""

from typing import TYPE_CHECKING
from langchain_core.tools import tool
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.services.data_service import DataService


class SemanticSearchInput(BaseModel):
    """
    Input schema for semantic search tool.
    
    Defines the parameters required for performing semantic similarity searches
    in the ChromaDB vector database.
    
    Attributes:
        query: Natural language description of actuator requirements
        k: Number of results to return (1-10, default: 3)
    """
    query: str = Field(
        description="A natural language query describing the actuator requirements or specifications"
    )
    k: int = Field(
        default=3,
        description="Number of results to return (default: 3, max: 10)"
    )


def create_semantic_search_tool(data_service: "DataService"):
    """
    Create a semantic search tool with data_service injected.
    
    This factory function creates a LangChain tool that performs semantic similarity
    searches in ChromaDB. The tool is configured with the provided DataService instance
    which handles the actual database queries.
    
    Args:
        data_service: DataService instance for accessing ChromaDB vectorstore
        
    Returns:
        LangChain tool function configured for semantic search
    """
    
    @tool("semantic_search", args_schema=SemanticSearchInput)
    def semantic_search(query: str, k: int = 3) -> str:
        """
        Search for actuators using natural language queries and semantic similarity.
        
        This tool performs semantic similarity search in ChromaDB using vector embeddings.
        It understands the meaning and context of queries, not just exact keyword matches.
        Use this tool when the user asks for recommendations, describes requirements,
        or asks vague questions about actuators.
        
        Examples of good queries:
        - "I need an actuator with high torque"
        - "Recommend something for 24V with fast operating speed"
        - "What actuators have duty cycle above 50%?"
        - "Find actuators suitable for industrial applications"
        - "110V single phase actuator"
        
        Args:
            query: Natural language description of what you're looking for
            k: Number of results to return (1-10, default: 3)
            
        Returns:
            A formatted string with matching actuator specifications, ordered by relevance.
            Each result includes:
            - Base Part Number
            - Context Type (voltage/power configuration)
            - Full specifications from the database
            - Relevance score (higher is better)
            
        Raises:
            No explicit exceptions, but returns error messages as strings if:
            - Data service is not available
            - No results are found
            - Database query fails
        """
        if not data_service:
            return "Error: Data service not available"
        
        try:
            # Limit k to reasonable range
            k = min(max(1, k), 10)
            
            results = data_service.semantic_search(query, k=k)
            
            if not results:
                return f"No actuators found matching: {query}"
            
            # Format the results
            formatted_results = []
            for i, result in enumerate(results, 1):
                metadata = result.get("metadata", {})
                content = result.get("content", "")
                score = result.get("score", 0.0)
                
                base_part = metadata.get("base_part_number") or metadata.get("identifier", "N/A")
                context_type = metadata.get("context_type", "N/A")
                
                # Calculate relevance percentage (lower score = higher similarity)
                relevance = max(0, min(100, (1 - score) * 100))
                
                description = f"Result {i} (Relevance: {relevance:.1f}%):\n"
                description += f"Base Part Number: {base_part}\n"
                description += f"Context Type: {context_type}\n"
                description += f"\nSpecifications:\n{content}\n"
                
                formatted_results.append(description.strip())
            
            return "\n\n---\n\n".join(formatted_results)
            
        except Exception as e:
            return f"Error performing semantic search: {str(e)}"
    
    return semantic_search

