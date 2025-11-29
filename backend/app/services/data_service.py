"""
Data Service Module

This module provides a unified interface for accessing actuator data from
multiple storage backends: SQLite (for exact part number searches) and
ChromaDB (for semantic similarity searches).

The DataService class:
- Manages connections to both SQLite and ChromaDB
- Provides exact search by part number (SQLite)
- Provides semantic search by natural language queries (ChromaDB)
- Handles connection lifecycle (initialize/cleanup)
- Supports thread-safe SQLite access with WAL mode

Architecture:
- SQLite: Fast exact matches by Base Part Number
- ChromaDB: Semantic search using vector embeddings
- Both can be used simultaneously for hybrid search
"""

import os
import json
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional
import sqlite3

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from app.config import Settings


class DataService:
    """
    Service for managing data access to SQLite and ChromaDB.
    
    Provides a unified interface for accessing actuator data from multiple
    storage backends. Supports both exact searches (SQLite) and semantic
    searches (ChromaDB) simultaneously for hybrid search capabilities.
    
    Attributes:
        settings: Application settings configuration
        sqlite_conn: SQLite database connection (for exact searches)
        vectorstore: ChromaDB vectorstore instance (for semantic searches)
        embeddings: OpenAI embeddings model instance
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize DataService with application settings.
        
        Args:
            settings: Application settings containing database paths and configuration
        """
        self.settings = settings
        self.sqlite_conn: Optional[sqlite3.Connection] = None
        self.vectorstore: Optional[Chroma] = None
        self.embeddings: Optional[OpenAIEmbeddings] = None
    
    async def initialize(self):
        """
        Initialize database connections.
        
        Sets up connections to SQLite and ChromaDB based on configuration.
        SQLite is initialized with WAL mode for better concurrency.
        ChromaDB is initialized if the persist directory exists.
        
        Returns:
            None
        """
        # Initialize SQLite for exact searches
        sqlite_path = Path(self.settings.sqlite_db_path)
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        # Use check_same_thread=False to allow thread-safe access
        self.sqlite_conn = sqlite3.connect(str(sqlite_path), check_same_thread=False)
        self.sqlite_conn.row_factory = sqlite3.Row  # Return dict-like rows
        # Enable WAL mode for better concurrency
        self.sqlite_conn.execute("PRAGMA journal_mode=WAL")
        
        # Initialize ChromaDB for semantic searches if directory exists
        if os.path.exists(self.settings.chroma_persist_directory):
            # Force reload settings to get latest embedding model
            from app.config import get_settings
            get_settings.cache_clear()
            current_settings = get_settings()
            
            self.embeddings = OpenAIEmbeddings(
                model=current_settings.openai_embedding_model,
                openai_api_key=current_settings.openai_api_key,
            )
            self.vectorstore = Chroma(
                persist_directory=self.settings.chroma_persist_directory,
                embedding_function=self.embeddings,
            )
    
    async def cleanup(self):
        """
        Cleanup database connections.
        
        Closes SQLite connection and clears ChromaDB references.
        Should be called when the service is no longer needed.
        
        Returns:
            None
        """
        if self.sqlite_conn:
            self.sqlite_conn.close()
            self.sqlite_conn = None
        
        self.vectorstore = None
        self.embeddings = None
    
    def search_by_part_number(self, part_number: str) -> List[Dict[str, Any]]:
        """
        Search for actuator by Base Part Number in SQLite.
        
        Performs exact and partial match searches on the Base Part Number field.
        Returns all matching records with their JSON data parsed into dictionaries.
        
        Args:
            part_number: Base Part Number to search for (exact or partial match)
            
        Returns:
            List of dictionaries containing actuator data. Each dictionary includes:
            - base_part_number: The part number
            - identifier: Alias for base_part_number (for compatibility)
            - All other fields from the JSON data (context_type, specifications, etc.)
            
        Example:
            >>> results = service.search_by_part_number("763A00-11330C00/A")
            >>> print(results[0]["context_type"])
            "220V 3 Phase Power"
        """
        if not self.sqlite_conn:
            return []
        
        try:
            cursor = self.sqlite_conn.cursor()
            
            # Search in the actuators table (with JSON structure)
            query = """
                SELECT base_part_number, data_json
                FROM actuators
                WHERE base_part_number = ? OR base_part_number LIKE ?
                LIMIT 10
            """
            
            # Try exact match and partial match
            search_term = f"%{part_number}%"
            cursor.execute(query, (part_number, search_term))
            rows = cursor.fetchall()
            
            # Convert to list of dicts with JSON parsed
            results = []
            for row in rows:
                base_part, data_json = row
                
                # Parse JSON data
                try:
                    data_dict = json.loads(data_json) if data_json else {}
                except json.JSONDecodeError:
                    data_dict = {}
                
                # Combine all fields into one result dict
                result = {
                    "base_part_number": base_part,
                    "identifier": base_part,  # Alias for compatibility
                }
                
                # Add all JSON fields (includes context_type, source_table, and all other fields)
                result.update(data_dict)
                
                results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Error searching SQLite: {e}")
            traceback.print_exc()
            return []
    
    def semantic_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform semantic search in ChromaDB using vector similarity.
        
        Searches for actuators that are semantically similar to the query,
        even if they don't contain exact keywords. Uses embeddings to find
        conceptually related results.
        
        Args:
            query: Natural language query describing desired actuator specifications
            k: Number of results to return (default: 5)
            
        Returns:
            List of dictionaries containing search results. Each dictionary includes:
            - content: Text content of the matching document
            - metadata: Document metadata (base_part_number, context_type, etc.)
            - score: Similarity score (lower is better/more similar)
            
        Example:
            >>> results = service.semantic_search("high torque 110V actuator", k=3)
            >>> print(results[0]["metadata"]["base_part_number"])
            "764B00-11300000/A"
        """
        if not self.vectorstore:
            return []
        
        try:
            # Perform similarity search
            docs = self.vectorstore.similarity_search_with_score(query, k=k)
            
            results = []
            for doc, score in docs:
                result = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score),
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Error in semantic search: {e}")
            return []
