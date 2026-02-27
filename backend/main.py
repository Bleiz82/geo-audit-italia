"""
GEO Audit Italia — FastAPI Entry Point
Powered by DigIdentity Agency
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger
import os

from backend.api.stripe_webhook import router as stripe_router
from backend.api.audit_trigger import router as audit_router

app = FastAPI(
    title="GEO Audit Italia",
    description="Il primo motore di audit GEO in italiano — by DigIdentity Agency",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (frontend)
app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets")

# API Routers
app.include_router(stripe_router, prefix="/api/stripe", tags=["Stripe"])
app.include_router(audit_router, prefix="/api/audit", tags=["Audit"])


@app.get("/", include_in_schema=False)
async def serve_landing():
    return FileResponse("frontend/index.html")


@app.get("/checkout", include_in_schema=False)
async def serve_checkout():
    return FileResponse("frontend/checkout.html")


@app.get("/success", include_in_schema=False)
async def serve_success():
    return FileResponse("frontend/success.html")


@app.on_event("startup")
async def startup_event():
    os.makedirs("reports/output", exist_ok=True)
    logger.info("🚀 GEO Audit Italia avviato correttamente")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "GEO Audit Italia", "version": "1.0.0"}
