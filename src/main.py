import logging
from fastapi import FastAPI
from src.core.config import settings
from src.api.routers import users
from src.core.logging import setup_logging

setup_logging()

app = FastAPI(
    title="StratLogic Scraper API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.include_router(users.router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    logging.info("Starting up StratLogic Scraper API...")

@app.get("/")
def read_root():
    return {"message": "Welcome to StratLogic Scraper API"}
