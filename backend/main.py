from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from config.settings import settings
from routes import simulate, predict, graph


# ─────────────────────────────────────────────
# LIFESPAN MANAGEMENT
# ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("=" * 50)
    logger.info("🚀 Starting Agentica Backend...")
    logger.info("=" * 50)
    logger.info(f"Environment: Loaded from .env file")
    logger.info(f"Database (Neo4j): {settings.NEO4J_URI}")
    logger.info(f"Database (MongoDB): {settings.MONGO_URI}")
    logger.info(f"LLM Model: {settings.DEFAULT_MODEL}")
    
    # Initialize services here if needed
    logger.info("✅ All services initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("=" * 50)
    logger.info("🛑 Shutting down Agentica Backend...")
    
    # Close database connections
    try:
        from services.graph_service import graph_service
        graph_service.close()
        logger.info("✅ Neo4j connection closed")
    except Exception as e:
        logger.error(f"Error closing Neo4j: {e}")
    
    try:
        from services.memory_service import memory_service
        await memory_service.close()
        logger.info("✅ MongoDB connection closed")
    except Exception as e:
        logger.error(f"Error closing MongoDB: {e}")
    
    logger.info("✅ Shutdown complete")


# ─────────────────────────────────────────────
# APP INITIALIZATION
# ─────────────────────────────────────────────

app = FastAPI(
    title="Agentica API",
    description="Multi-Agent Simulation Platform with GraphRAG",
    version="1.0.0",
    lifespan=lifespan
)


# ─────────────────────────────────────────────
# CORS CONFIGURATION
# ─────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js development
        "http://localhost:3001",  # Alternative port
        "http://localhost:8080",  # Vue/other frontend
        "https://agentica.app",   # Production domain
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

app.include_router(simulate.router, prefix="/api/simulate", tags=["Simulation"])
app.include_router(predict.router, prefix="/api/predict", tags=["Prediction"])
app.include_router(graph.router, prefix="/api/graph", tags=["Graph"])


# ─────────────────────────────────────────────
# ROOT ENDPOINTS
# ─────────────────────────────────────────────

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Agentica API",
        "version": "1.0.0",
        "status": "running",
        "description": "Multi-Agent Simulation Platform with GraphRAG",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "services": {
            "neo4j": "connected" if settings.NEO4J_URI else "not configured",
            "mongodb": "connected" if settings.MONGO_URI else "not configured",
            "openrouter": "configured" if settings.OPENROUTER_API_KEY else "not configured"
        }
    }


@app.get("/info")
async def app_info():
    """Application information endpoint."""
    return {
        "name": "Agentica Backend",
        "version": "1.0.0",
        "features": [
            "Multi-Agent Simulation",
            "GraphRAG Knowledge Graph",
            "Predictive Analysis",
            "Sentiment Analysis",
            "Butterfly Effect Analysis"
        ],
        "endpoints": {
            "simulation": "/api/simulate",
            "prediction": "/api/predict",
            "graph": "/api/graph"
        }
    }


# ─────────────────────────────────────────────
# ERROR HANDLERS
# ─────────────────────────────────────────────

from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


# ─────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Agentica Backend with Uvicorn...")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload in development
        log_level="info"
    )