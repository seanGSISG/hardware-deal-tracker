from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import router as api_router
from app.core.config import settings

app = FastAPI(
    title="Hardware Deal Tracker",
    description="AI-Powered Enterprise Hardware Deal Tracking API",
    version="0.2.0",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "Hardware Deal Tracker API", "docs": "/api/v1/docs", "version": "0.2.0"}
