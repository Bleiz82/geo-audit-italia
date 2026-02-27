"""
Invio Email con Report GEO allegato
Powered by Resend.com
"""

import resend
import os
from loguru import logger
from jinja2 import Environment, FileSystemLoader


resend.api_key = os.getenv("RESEND_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@geo-audit.it")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "GEO Audit Italia")

jinja_env = Environment(loader=FileSystemLoader("backend/templates/email"))


async def invia_report_cliente(
    email: str,
    url_sito: str,
    percorso_pdf: str,
    piano: str,
):
    """
    Invia il PDF del report GEO al cliente con email professionale in italiano
    """
    # Leggi PDF come bytes
    with open(percorso_pdf, "rb") as f:
        pdf_bytes = f.read()

    # Renderizza template email HTML
    template = jinja_env.get_template("report_email.html")
    corpo_html = template.render(
        url_sito=url_sito,
        piano=piano,
        nome_prodotto="GEO Audit Italia",
    )

    nome_file = f"GEO-Report-{url_sito.replace('https://', '').replace('/', '-')}.pdf"

    try:
        params = {
            "from": f"{EMAIL_FROM_NAME} <{EMAIL_FROM}>",
            "to": [email],
            "subject": f"🎯 Il tuo GEO Audit è pronto — {url_sito}",
            "html": corpo_html,
            "attachments": [
                {
                    "filename": nome_file,
                    "content": list(pdf_bytes),
                }
            ],
        }
        resend.Emails.send(params)
        logger.success(f"📧 Report inviato a {email}")

    except Exception as e:
        logger.error(f"❌ Errore invio email a {email}: {e}")
        raise
