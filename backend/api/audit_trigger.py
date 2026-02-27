"""
Orchestratore Audit GEO
Avvia i 5 moduli di analisi in parallelo e consegna il report
"""

import asyncio
from fastapi import APIRouter
from loguru import logger
from datetime import datetime

from backend.engine.geo_audit import esegui_audit_completo
from backend.engine.report_generator import genera_pdf_report
from backend.api.email_sender import invia_report_cliente

router = APIRouter()


async def avvia_audit_completo(
    url_sito: str,
    email_cliente: str,
    piano: str,
    session_id: str,
):
    """
    Flusso completo: audit → PDF → email
    Chiamato in background dopo conferma pagamento Stripe
    """
    logger.info(f"🔍 Avvio audit per: {url_sito}")
    inizio = datetime.now()

    try:
        # Step 1: Esegui i 5 moduli in parallelo
        risultati = await esegui_audit_completo(url_sito)

        # Step 2: Genera PDF report in italiano
        percorso_pdf = await genera_pdf_report(
            risultati=risultati,
            url_sito=url_sito,
            email_cliente=email_cliente,
            session_id=session_id,
        )

        # Step 3: Invia report via email
        await invia_report_cliente(
            email=email_cliente,
            url_sito=url_sito,
            percorso_pdf=percorso_pdf,
            piano=piano,
        )

        durata = (datetime.now() - inizio).seconds
        logger.success(f"✅ Audit completato per {url_sito} in {durata}s → inviato a {email_cliente}")

    except Exception as e:
        logger.error(f"❌ Errore audit per {url_sito}: {e}")
        # TODO: notifica errore al cliente + retry logic
