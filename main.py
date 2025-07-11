from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from database import connect_to_mongo, close_mongo_connection
from routes import users, conversations, analysis
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """Application factory pattern"""
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_credentials,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )
    
    app.add_event_handler("startup", startup_event)
    app.add_event_handler("shutdown", shutdown_event)
    
    app.include_router(users.router)
    app.include_router(conversations.router)
    app.include_router(analysis.router)
    
    return app

async def startup_event():
    """Database connection startup"""
    await connect_to_mongo()
    logger.info("Connected to MongoDB")

async def shutdown_event():
    """Database connection shutdown"""
    await close_mongo_connection()
    logger.info("Disconnected from MongoDB")

app = create_app()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": settings.app_name, 
        "version": settings.app_version,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "app": settings.app_name,
        "version": settings.app_version
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host=settings.host, 
        port=settings.port, 
        reload=settings.reload, 
        log_level=settings.log_level
    )
