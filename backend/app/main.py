"""
FastAPI Application Entry Point Module

This module serves as the main entry point for the Konecto AI Agent FastAPI application.
It initializes the application, configures middleware, sets up routes, and manages
the application lifecycle (startup and shutdown).

The application provides:
- REST API endpoints for conversation with the AI agent
- Health check endpoint for monitoring
- CORS middleware for cross-origin requests
- Application lifecycle management (database connections, resource cleanup)

Architecture:
- FastAPI application with async lifespan management
- DataService initialization on startup
- Resource cleanup on shutdown
- Modular routing structure

Entry Point:
- The `app` instance is created at module level and used by ASGI server (uvicorn)
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.conversation import router as conversation_router
from app.config import get_settings
from app.services.data_service import DataService

# Configure logging
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    
    This context manager handles:
    - Startup: Initializes DataService and stores it in app.state
    - Shutdown: Cleans up database connections and resources
    
    Args:
        app: FastAPI application instance
        
    Yields:
        None: Control is yielded to the application runtime
        
    Raises:
        Exception: If DataService initialization fails, the application startup will fail
    """
    # Startup: Initialize data service
    try:
        logger.info("Initializing application...")
        settings = get_settings()
        data_service = DataService(settings)
        await data_service.initialize()
        app.state.data_service = data_service
        logger.info("Application initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    
    yield
    
    # Shutdown: Cleanup resources
    try:
        logger.info("Shutting down application...")
        await data_service.cleanup()
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Error during application shutdown: {e}")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    This factory function creates a fully configured FastAPI application instance
    with all necessary middleware, routes, and lifecycle management.
    
    Configuration includes:
    - Application metadata (title, version, description)
    - CORS middleware for cross-origin requests
    - API routes (conversation endpoint)
    - Health check endpoint
    - Application lifespan management
    
    Returns:
        FastAPI: Fully configured FastAPI application instance
        
    Example:
        >>> app = create_app()
        >>> # Use with uvicorn: uvicorn app.main:app --reload
    """
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Intelligent AI Agent for Series 76 Electric Actuators",
        lifespan=lifespan,
    )
    
    # Configure CORS middleware for cross-origin requests
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routers
    app.include_router(conversation_router, prefix="/api", tags=["Conversation"])
    
    @app.get("/health", tags=["Health"])
    async def health_check():
        """
        Health check endpoint for monitoring and load balancers.
        
        Returns the current status and version of the application.
        Useful for health checks, monitoring systems, and load balancers.
        
        Returns:
            dict: Health status information containing:
                - status: "healthy" if application is running
                - version: Application version string
        """
        return {"status": "healthy", "version": settings.app_version}
    
    return app


app = create_app()

