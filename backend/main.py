"""
GEO Audit Italia — FastAPI Entry Point
Powered by DigIdentity Agency
"""

from fastapi import FastAPI, Request
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



@app.get("/report/{session_id}", include_in_schema=False)
async def serve_report(session_id: str):
    from pathlib import Path
    from fastapi import HTTPException
    output_dir = Path("reports/output")
    
    # Cerca file che contiene il session_id nel nome
    matches = list(output_dir.glob(f"*{session_id}*.html"))
    
    # Fallback: cerca per slug pulito
    if not matches:
        slug = session_id.replace("-", "").replace("_", "").lower()
        matches = [
            f for f in output_dir.glob("*.html")
            if slug in f.stem.lower().replace("-", "").replace("_", "")
        ]
    
    # Fallback finale: prendi il piu recente
    if not matches:
        all_files = list(output_dir.glob("*.html"))
        if all_files:
            matches = [sorted(all_files, key=lambda f: f.stat().st_mtime, reverse=True)[0]]
    
    if not matches:
        raise HTTPException(status_code=404, detail=f"Report non trovato: {session_id}")
    
    report_file = sorted(matches, key=lambda f: f.stat().st_mtime, reverse=True)[0]
    logger.info(f"Serving report: {report_file.name}")
    return FileResponse(report_file, media_type="text/html")

@app.on_event("startup")
async def startup_event():
    os.makedirs("reports/output", exist_ok=True)
    logger.info("🚀 GEO Audit Italia avviato correttamente")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "GEO Audit Italia", "version": "1.0.0"}

@app.get("/download-pdf/{session_id}")
async def download_pdf(session_id: str):
    import glob, os
    from fastapi.responses import FileResponse
    pattern = f"reports/output/GEO-Report-*{session_id}*.html"
    files = glob.glob(pattern)
    if not files:
        files = sorted(glob.glob("reports/output/GEO-Report-*.html"))
    if not files:
        return {"error": "Report non trovato"}
    latest = max(files, key=os.path.getmtime)
    return FileResponse(
        latest,
        media_type="text/html",
        filename="GEO-Audit-Report.html",
        headers={"Content-Disposition": "attachment; filename=GEO-Audit-Report.html"}
    )

@app.get("/genera-pdf/{session_id}")
async def genera_pdf(session_id: str):
    import glob, os
    from fastapi.responses import FileResponse
    from pathlib import Path
    import asyncio
    
    # Stessa logica di /report/{session_id}
    output_dir = Path("reports/output")
    matches = list(output_dir.glob(f"*{session_id}*.html"))
    if not matches:
        slug = session_id.replace("-", "").replace("_", "").lower()
        matches = [f for f in output_dir.glob("*.html") if slug in f.stem.replace("-","").replace("_","").lower()]
    if not matches:
        matches = sorted(output_dir.glob("*.html"))
    if not matches:
        return {"error": "Nessun report HTML trovato"}
    
    html_file = str(max(matches, key=os.path.getmtime))
    html_abs = os.path.abspath(html_file)
    file_url = f"file:///{html_abs.replace(chr(92), '/')}"
    
    output_path = f"reports/output/GEO-Audit-{session_id}.pdf"
    
    # Genera PDF con Puppeteer dal file locale
    import concurrent.futures
    import subprocess
    def run_puppeteer():
        return subprocess.run(
            ["node", "pdf_generator.js", file_url, output_path],
            capture_output=True, text=True, timeout=90
        )
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, run_puppeteer)
    if result.returncode != 0:
        return {"error": result.stderr}
    
    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename="GEO-Audit-Report.pdf"
    )
