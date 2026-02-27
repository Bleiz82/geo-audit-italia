"""
Modulo Schema Analyzer
Analizza i blocchi JSON-LD di una pagina e valuta qualità e completezza
per la visibilità AI (GEO) con focus sul mercato italiano.
"""

import httpx
from bs4 import BeautifulSoup
from loguru import logger
import json


TIPI_SCHEMA_OBBLIGATORI = {
    "Organization": ["name", "url"],
    "LocalBusiness": ["name", "address", "telephone"],
    "Article": ["headline", "author", "datePublished"],
    "Product": ["name", "offers"],
    "BreadcrumbList": ["itemListElement"],
    "FAQPage": ["mainEntity"],
    "Person": ["name"],
    "WebSite": ["url"],
}

CAMPI_AI_SPECIFICI = ["sameAs", "aggregateRating", "address"]


async def analizza_schema(url: str) -> dict:
    """
    Estrae e valuta i blocchi JSON-LD dalla pagina.
    """
    logger.info(f"🗂️ Analisi schema JSON-LD: {url}")

    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "GEOAuditItalia/1.0 (schema-analyzer)"})
            resp.raise_for_status()
            html = resp.text
    except Exception as e:
        logger.error(f"❌ Errore fetch schema {url}: {e}")
        return {"score": 0, "modulo": "schema", "errore": str(e)}

    soup = BeautifulSoup(html, "lxml")
    blocchi = soup.find_all("script", type="application/ld+json")

    schemi_rilevati = []
    campi_mancanti = {}
    sameAs_presente = False

    for script in blocchi:
        try:
            data = json.loads(script.string or "")
        except Exception:
            continue

        # supporta array di oggetti
        if isinstance(data, list):
            for item in data:
                _processa_blocco(item, schemi_rilevati, campi_mancanti)
        else:
            _processa_blocco(data, schemi_rilevati, campi_mancanti)

    # controlla sameAs in Organization/LocalBusiness
    for s in schemi_rilevati:
        if s["type"] in ["Organization", "LocalBusiness"] and "sameAs" in s["data"]:
            sameAs_presente = True

    # scoring
    score = _calcola_score(schemi_rilevati, campi_mancanti, sameAs_presente)

    raccomandazioni = _genera_raccomandazioni(schemi_rilevati, campi_mancanti, sameAs_presente)

    return {
        "score": score,
        "modulo": "schema",
        "schemi_rilevati": schemi_rilevati,
        "schemi_mancanti_consigliati": _schemi_mancanti_consigliati(schemi_rilevati),
        "campi_mancanti": campi_mancanti,
        "sameAs_presente": sameAs_presente,
        "raccomandazioni": raccomandazioni,
    }


def _processa_blocco(data, schemi_rilevati, campi_mancanti):
    tipo = data.get("@type")
    if not tipo:
        return
    if isinstance(tipo, list):
        tipo = tipo[0]

    entry = {"type": tipo, "data": data}
    schemi_rilevati.append(entry)

    # controlla campi obbligatori
    obblig = TIPI_SCHEMA_OBBLIGATORI.get(tipo, [])
    mancanti = []
    for campo in obblig:
        if campo not in data:
            mancanti.append(campo)
    if mancanti:
        campi_mancanti[tipo] = mancanti

    # verifica indirizzo IT
    if "address" in data:
        indirizzo = data.get("address", {})
        paese = indirizzo.get("addressCountry")
        if paese and paese != "IT":
            campi_mancanti.setdefault(tipo, []).append("addressCountry!=IT")


def _schemi_mancanti_consigliati(rilevati):
    consigliati = []
    tipi = [s["type"] for s in rilevati]
    for t in ["Organization", "LocalBusiness"]:
        if t not in tipi:
            consigliati.append(t)
    return consigliati


def _calcola_score(schemi, campi_mancanti, sameAs):
    peso_schema = 40 if schemi else 0
    peso_completezza = 35
    totale_campi = sum(len(v) for v in campi_mancanti.values())
    completezza = max(0, 100 - totale_campi * 5)
    peso_sameas = 15 if sameAs else 0
    peso_ai = 10

    score = peso_schema + (completezza * peso_completezza / 100) + peso_sameas + peso_ai
    return round(min(score, 100))


def _genera_raccomandazioni(schemi, campi_mancanti, sameAs):
    recs = []
    if not schemi:
        recs.append("🔴 CRITICO: Nessun blocco JSON-LD trovato. Aggiungi dati strutturati al sito.")
        return recs

    if campi_mancanti:
        for tipo, manc in campi_mancanti.items():
            priorita = "ALTA" if "sameAs" in manc or "addressCountry!=IT" in manc else "MEDIA"
            recs.append(f"⚠️ {priorita}: Schema {tipo} mancano i campi {', '.join(manc)}.")

    if not sameAs:
        recs.append("⚠️ ALTA: Manca campo sameAs in Organization/LocalBusiness. Aggiungi riferimenti ai profili social.")

    return recs
