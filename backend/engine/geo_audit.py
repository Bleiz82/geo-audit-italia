"""
Orchestratore Principale GEO Audit
Lancia 5 moduli di analisi in parallelo con asyncio
"""

import asyncio
from loguru import logger
from datetime import datetime

from backend.engine.citability import analizza_citabilita
from backend.engine.crawlers import analizza_crawler
from backend.engine.brand_mentions import analizza_brand_mention
from backend.engine.schema_analyzer import analizza_schema
from backend.engine.content_quality import analizza_contenuto


# Pesi scoring GEO (totale = 100%)
PESI_SCORING = {
    "citabilita_ai": 0.25,
    "autorita_brand": 0.20,
    "qualita_contenuto": 0.20,
    "fondamenta_tecniche": 0.15,
    "dati_strutturati": 0.10,
    "ottimizzazione_piattaforme": 0.10,
}


async def esegui_audit_completo(url: str) -> dict:
    """
    Esegue i 5 moduli di analisi in parallelo e calcola il GEO Score finale
    """
    logger.info(f"🔍 Avvio analisi parallela per: {url}")
    inizio = datetime.now()

    # Esecuzione parallela dei 5 moduli
    risultati_grezzi = await asyncio.gather(
        analizza_citabilita(url),           # Modulo 1: Citabilità AI (25%)
        analizza_crawler(url),              # Modulo 2: Crawler + llms.txt (15%)
        analizza_brand_mention(url),        # Modulo 3: Brand mention (20%)
        analizza_schema(url),               # Modulo 4: Dati strutturati (10%)
        analizza_contenuto(url),            # Modulo 5: Contenuto & E-E-A-T (20%)
        return_exceptions=True,
    )

    # Mapping risultati
    chiavi = [
        "citabilita",
        "crawler",
        "brand",
        "schema",
        "contenuto",
    ]
    risultati = {}
    for i, chiave in enumerate(chiavi):
        if isinstance(risultati_grezzi[i], Exception):
            logger.warning(f"⚠️ Modulo '{chiave}' fallito: {risultati_grezzi[i]}")
            risultati[chiave] = {"score": 0, "errore": str(risultati_grezzi[i])}
        else:
            risultati[chiave] = risultati_grezzi[i]

    # Calcolo GEO Score composito
    geo_score = calcola_geo_score(risultati)

    durata = (datetime.now() - inizio).seconds
    logger.success(f"✅ Analisi completata in {durata}s — GEO Score: {geo_score}/100")

    return {
        "url": url,
        "geo_score": geo_score,
        "data_analisi": datetime.now().isoformat(),
        "durata_secondi": durata,
        "moduli": risultati,
        "priorita": genera_priorita(risultati, geo_score),
    }


def calcola_geo_score(risultati: dict) -> int:
    """
    Calcola il GEO Score ponderato 0-100
    """
    score_citabilita = risultati.get("citabilita", {}).get("score", 0)
    score_brand = risultati.get("brand", {}).get("score", 0)
    score_contenuto = risultati.get("contenuto", {}).get("score", 0)
    score_tecnico = risultati.get("crawler", {}).get("score", 0)
    score_schema = risultati.get("schema", {}).get("score", 0)

    geo_score = (
        score_citabilita * PESI_SCORING["citabilita_ai"] +
        score_brand * PESI_SCORING["autorita_brand"] +
        score_contenuto * PESI_SCORING["qualita_contenuto"] +
        score_tecnico * PESI_SCORING["fondamenta_tecniche"] +
        score_schema * PESI_SCORING["dati_strutturati"]
    )

    return round(min(max(geo_score, 0), 100))


def genera_priorita(risultati: dict, geo_score: int) -> list:
    """
    Genera lista priorità di intervento ordinata per impatto
    """
    priorita = []

    if risultati.get("citabilita", {}).get("score", 100) < 50:
        priorita.append({
            "priorita": "ALTA",
            "categoria": "Citabilità AI",
            "problema": "I contenuti non sono ottimizzati per essere citati dalle AI",
            "azione": "Ristruttura i contenuti in blocchi di 134-167 parole, autonomi e ricchi di fatti",
            "impatto_stimato": "+15-25 punti GEO Score",
        })

    if risultati.get("crawler", {}).get("ai_bloccati", False):
        priorita.append({
            "priorita": "CRITICA",
            "categoria": "Accesso Crawler AI",
            "problema": "Il robots.txt blocca i principali crawler AI",
            "azione": "Consenti GPTBot, ClaudeBot, PerplexityBot nel robots.txt",
            "impatto_stimato": "+10-20 punti GEO Score",
        })

    if not risultati.get("crawler", {}).get("llmstxt_presente", False):
        priorita.append({
            "priorita": "MEDIA",
            "categoria": "llms.txt",
            "problema": "File llms.txt assente",
            "azione": "Genera e pubblica il file llms.txt per guidare i crawler AI",
            "impatto_stimato": "+5-10 punti GEO Score",
        })

    if risultati.get("schema", {}).get("score", 100) < 40:
        priorita.append({
            "priorita": "ALTA",
            "categoria": "Dati Strutturati",
            "problema": "Schema markup insufficiente o assente",
            "azione": "Implementa JSON-LD per Organization, LocalBusiness e BreadcrumbList",
            "impatto_stimato": "+8-15 punti GEO Score",
        })

    if risultati.get("brand", {}).get("score", 100) < 40:
        priorita.append({
            "priorita": "MEDIA",
            "categoria": "Autorità Brand",
            "problema": "Poche menzioni del brand su piattaforme AI-cited",
            "azione": "Aumenta presenza su Wikipedia, YouTube, LinkedIn, siti di settore italiani",
            "impatto_stimato": "+10-20 punti GEO Score",
        })

    # Ordina per priorità
    ordine = {"CRITICA": 0, "ALTA": 1, "MEDIA": 2, "BASSA": 3}
    priorita.sort(key=lambda x: ordine.get(x["priorita"], 99))

    return priorita
