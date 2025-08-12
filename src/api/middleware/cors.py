from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings


def setup_cors_middleware(app: FastAPI) -> None:
    """Setup CORS middleware for the FastAPI application."""
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # React development server
            "http://localhost:3001",  # Alternative React port
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            # Add production origins here
            # "https://yourdomain.com",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
