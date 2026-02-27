"""
Generatore PDF report GEO in italiano
Usa Jinja2 + WeasyPrint
"""

import os
import json
from datetime import datetime
from loguru import logger
from jinja2 import Environment, FileSystemLoader

try:
    from weasyprint import HTML
except ImportError:
    HTML = None

LABELS_PATH = "data/copy/report_labels.json"
OUTPUT_DIR = "reports/output"

jinja_env = Environment(loader=FileSystemLoader("backend/templates"))


def _get_giudizio_score(score: int) -> dict:
    if score <= 30:
        return {"etichetta": "Invisibile alle AI", "colore": "#DC2626", "emoji": "🔴"}
    if score <= 50:
        return {"etichetta": "Visibilità minima", "colore": "#EA580C", "emoji": "🟠"}
    if score <= 70:
        return {"etichetta": "In sviluppo", "colore": "#CA8A04", "emoji": "🟡"}
    if score <= 85:
        return {"etichetta": "Buona visibilità", "colore": "#16A34A", "emoji": "🟢"}
    return {"etichetta": "Eccellente", "colore": "#0891B2", "emoji": "💎"}


def _formatta_data(iso_string: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_string)
        mesi = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
                "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
        return f"{dt.day} {mesi[dt.month-1]} {dt.year} ore {dt.hour:02d}:{dt.minute:02d}"
    except Exception:
        return iso_string


def _calcola_barra_progresso(score: int) -> str:
    perc = max(0, min(score, 100))
    return f"width: {perc}%"


async def genera_pdf_report(risultati: dict, url_sito: str, email_cliente: str, session_id: str) -> str:
    logger.info(f"📄 Generazione PDF report per {url_sito}")

    # Load labels
    try:
        with open(LABELS_PATH, "r", encoding="utf-8") as f:
            labels = json.load(f)
    except Exception as e:
        logger.error(f"❌ Impossibile caricare etichette report: {e}")
        labels = {}

    template = jinja_env.get_template("report_ita.html")

    data_analisi = risultati.get("data_analisi") or datetime.now().isoformat()

    context = {
        "labels": labels,
        "geo_score": risultati.get("geo_score"),
        "giudizio": _get_giudizio_score(risultati.get("geo_score", 0)),
        "url_sito": url_sito,
        "data_analisi": _formatta_data(data_analisi),
        "moduli": risultati.get("moduli", {}),
        "priorita": risultati.get("priorita", []),
        "email_cliente": email_cliente,
        "session_id": session_id,
        "calcola_barra": _calcola_barra_progresso,
    }

    html_rendered = template.render(**context)

    # prepare output file name
    dominio = url_sito.replace("https://", "").replace("http://", "").replace("/", "-")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"GEO-Report-{dominio}-{timestamp}.pdf"
    percorso = os.path.join(OUTPUT_DIR, filename)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if HTML:
        try:
            HTML(string=html_rendered, base_url="").write_pdf(percorso)
            logger.success(f"✅ PDF generato: {percorso}")
        except Exception as e:
            logger.error(f"❌ Errore generazione PDF: {e}")
            raise
    else:
        logger.warning("⚠️ WeasyPrint non disponibile, scrivo HTML come fallback")
        percorso_html = percorso.replace(".pdf", ".html")
        with open(percorso_html, "w", encoding="utf-8") as f:
            f.write(html_rendered)
        percorso = percorso_html

    return percorso
