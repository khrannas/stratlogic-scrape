from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
import logging


def setup_cors_middleware(app: FastAPI) -> None:
    """Setup CORS middleware for the FastAPI application."""

    allowed_origins = [
        "http://localhost:3000",  # React development server
        "http://localhost:3001",  # Alternative React port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://0.0.0.0:3000",    # Alternative localhost format
        "http://0.0.0.0:3001",    # Alternative localhost format
        # Add production origins here
        # "https://yourdomain.com",
    ]

    logger = logging.getLogger(__name__)
    logger.info(f"Setting up CORS middleware with allowed origins: {allowed_origins}")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
