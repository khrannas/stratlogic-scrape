import logging
from datetime import datetime
from fastapi import FastAPI
from src.core.config import settings
from src.api.routers import users, jobs, artifacts, auth, web_scraper, paper_scraper, government_scraper
from src.core.logging import setup_logging
from src.api.middleware.cors import setup_cors_middleware
from src.api.middleware.error_handling import setup_error_handling_middleware

setup_logging()

app = FastAPI(
    title="StratLogic Scraper API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Setup middleware
setup_cors_middleware(app)
setup_error_handling_middleware(app)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(jobs.router, prefix=settings.API_V1_STR)
app.include_router(artifacts.router, prefix=settings.API_V1_STR)
app.include_router(web_scraper.router, prefix=settings.API_V1_STR)
app.include_router(paper_scraper.router, prefix=settings.API_V1_STR)
app.include_router(government_scraper.router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    logging.info("Starting up StratLogic Scraper API...")

@app.get("/")
def read_root():
    return {"message": "Welcome to StratLogic Scraper API"}

@app.get("/health")
def health_check():
    """
    Health check endpoint to verify API is running.
    """
    return {
        "status": "healthy",
        "message": "StratLogic Scraper API is running",
        "timestamp": datetime.utcnow().isoformat()
    }
