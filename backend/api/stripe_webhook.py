"""
Gestione Webhook Stripe
Trigger dell'audit GEO dopo pagamento confermato
"""

import stripe
import json
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from loguru import logger
from pydantic_settings import BaseSettings

from backend.api.audit_trigger import avvia_audit_completo


class Settings(BaseSettings):
    stripe_secret_key: str
    stripe_webhook_secret: str

    class Config:
        env_file = ".env"


settings = Settings()
stripe.api_key = settings.stripe_secret_key
router = APIRouter()


@router.post("/webhook")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Riceve eventi Stripe e avvia l'audit GEO dopo checkout.session.completed
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        logger.error("❌ Webhook Stripe: payload non valido")
        raise HTTPException(status_code=400, detail="Payload non valido")
    except stripe.error.SignatureVerificationError:
        logger.error("❌ Webhook Stripe: firma non valida")
        raise HTTPException(status_code=400, detail="Firma non valida")

    # Gestione evento pagamento completato
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        
        email_cliente = session.get("customer_email") or \
                        session.get("customer_details", {}).get("email")
        url_sito = session.get("metadata", {}).get("url_sito", "")
        piano = session.get("metadata", {}).get("piano", "singolo")
        session_id = session.get("id", "")

        if not email_cliente or not url_sito:
            logger.warning(f"⚠️ Dati mancanti nel webhook: email={email_cliente}, url={url_sito}")
            raise HTTPException(status_code=422, detail="Dati ordine incompleti")

        logger.info(f"✅ Pagamento confermato: {email_cliente} | {url_sito} | Piano: {piano}")

        # Avvio audit in background (non blocca la risposta a Stripe)
        background_tasks.add_task(
            avvia_audit_completo,
            url_sito=url_sito,
            email_cliente=email_cliente,
            piano=piano,
            session_id=session_id,
        )

    return {"status": "ricevuto"}


@router.post("/create-checkout-session")
async def crea_sessione_checkout(request: Request):
    """
    Crea sessione Stripe Checkout con metadati URL sito e piano
    """
    data = await request.json()
    url_sito = data.get("url_sito", "").strip()
    email = data.get("email", "").strip()
    piano = data.get("piano", "singolo")  # singolo | agency_monthly | agency_annual

    if not url_sito or not email:
        raise HTTPException(status_code=422, detail="URL sito ed email obbligatori")

    # Mappa piano → price_id Stripe
    prezzi = {
        "singolo": "price_SINGOLO_ID",
        "agency_monthly": "price_AGENCY_MONTHLY_ID",
        "agency_annual": "price_AGENCY_ANNUAL_ID",
    }

    price_id = prezzi.get(piano, prezzi["singolo"])

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            customer_email=email,
            line_items=[{"price": price_id, "quantity": 1}],
            mode="payment" if piano == "singolo" else "subscription",
            success_url=f"https://geo-audit.it/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url="https://geo-audit.it/?canceled=true",
            metadata={
                "url_sito": url_sito,
                "piano": piano,
            },
        )
        return {"checkout_url": checkout_session.url}

    except stripe.error.StripeError as e:
        logger.error(f"❌ Errore Stripe: {e}")
        raise HTTPException(status_code=500, detail="Errore nella creazione del pagamento")
