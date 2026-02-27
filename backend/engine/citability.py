"""
Modulo Citabilità AI
Analizza quanto i contenuti sono ottimizzati per essere citati da ChatGPT,
Claude, Perplexity e Google AI Overviews.

Ricerca: i passaggi ideali per essere citati da una AI sono
134-167 parole, autonomi, ricchi di fatti, in risposta diretta a domande.
"""

import httpx
from bs4 import BeautifulSoup
from loguru import logger
import re


LUNGHEZZA_OTTIMALE_MIN = 134
LUNGHEZZA_OTTIMALE_MAX = 167

# Indicatori di fatto / citabilità
PATTERN_FATTI = [
    r'\d+%',                    # percentuali
    r'\d+[\.,]\d+',             # numeri decimali
    r'secondo\s+\w+',           # citazioni di fonte
    r'ricerca\s+(di|del)',      # riferimenti a ricerche
    r'studio\s+(di|del)',       # studi
    r'dati\s+(di|del)',         # dati
    r'nel\s+20\d\d',            # anni recenti
]

# Indicatori domanda/risposta diretta
PAROLE_CHIAVE_RISPOSTA = [
    "cos'è", "come funziona", "perché", "quando", "quale",
    "quali sono", "come si", "significa", "definizione",
    "vantaggi", "svantaggi", "differenza tra",
]


async def analizza_citabilita(url: str) -> dict:
    """
    Analizza la citabilità AI del contenuto della pagina
    """
    logger.info(f"📝 Analisi citabilità: {url}")

    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            risposta = await client.get(url, headers={
                "User-Agent": "GEOAuditItalia/1.0 (citability-analyzer)"
            })
            risposta.raise_for_status()
            html = risposta.text

    except Exception as e:
        logger.error(f"❌ Errore fetch {url}: {e}")
        return {"score": 0, "errore": str(e), "modulo": "citabilita"}

    soup = BeautifulSoup(html, "lxml")

    # Rimuovi nav, footer, script, style
    for tag in soup(["nav", "footer", "script", "style", "header", "aside"]):
        tag.decompose()

    # Estrai paragrafi di testo
    paragrafi = [
        p.get_text(strip=True)
        for p in soup.find_all("p")
        if len(p.get_text(strip=True)) > 50
    ]

    if not paragrafi:
        return {
            "score": 10,
            "modulo": "citabilita",
            "problema": "Nessun paragrafo di testo rilevante trovato",
            "raccomandazione": "Aggiungi contenuto testuale strutturato alla pagina",
        }

    # Analisi blocchi
    blocchi_ottimali = 0
    blocchi_ricchi_di_fatti = 0
    blocchi_risposta_diretta = 0
    score_per_blocco = []

    for par in paragrafi:
        parole = len(par.split())
        score_blocco = 0

        # Lunghezza ottimale
        if LUNGHEZZA_OTTIMALE_MIN <= parole <= LUNGHEZZA_OTTIMALE_MAX:
            blocchi_ottimali += 1
            score_blocco += 40

        # Ricchezza fattuale
        n_fatti = sum(
            len(re.findall(pattern, par.lower()))
            for pattern in PATTERN_FATTI
        )
        if n_fatti >= 2:
            blocchi_ricchi_di_fatti += 1
            score_blocco += 35

        # Risposta diretta a domanda
        if any(kw in par.lower() for kw in PAROLE_CHIAVE_RISPOSTA):
            blocchi_risposta_diretta += 1
            score_blocco += 25

        score_per_blocco.append(min(score_blocco, 100))

    # Score medio
    score_medio = sum(score_per_blocco) / len(score_per_blocco) if score_per_blocco else 0

    # Bonus struttura generale
    ha_heading = bool(soup.find_all(["h1", "h2", "h3"]))
    ha_liste = bool(soup.find_all(["ul", "ol"]))

    if ha_heading:
        score_medio = min(score_medio + 10, 100)
    if ha_liste:
        score_medio = min(score_medio + 5, 100)

    score_finale = round(score_medio)

    return {
        "score": score_finale,
        "modulo": "citabilita",
        "totale_paragrafi": len(paragrafi),
        "blocchi_lunghezza_ottimale": blocchi_ottimali,
        "blocchi_ricchi_di_fatti": blocchi_ricchi_di_fatti,
        "blocchi_risposta_diretta": blocchi_risposta_diretta,
        "ha_heading_strutturati": ha_heading,
        "ha_liste_strutturate": ha_liste,
        "raccomandazioni": _genera_raccomandazioni_citabilita(
            score_finale, blocchi_ottimali, len(paragrafi),
            blocchi_ricchi_di_fatti, blocchi_risposta_diretta
        ),
    }


def _genera_raccomandazioni_citabilita(
    score, ottimali, totale, fatti, risposte
) -> list:
    raccomandazioni = []

    if score < 40:
        raccomandazioni.append(
            "⚠️ CRITICO: Il contenuto non è strutturato per essere citato dalle AI. "
            "Riscrivi i paragrafi principali in blocchi autonomi di 134-167 parole."
        )
    if ottimali / max(totale, 1) < 0.3:
        raccomandazioni.append(
            "📏 Meno del 30% dei paragrafi ha lunghezza ottimale per le citazioni AI. "
            "Accorcia i paragrafi troppo lunghi e espandi quelli troppo brevi."
        )
    if fatti / max(totale, 1) < 0.2:
        raccomandazioni.append(
            "📊 Aggiungi più dati quantitativi, statistiche e riferimenti a fonti. "
            "Le AI citano preferibilmente contenuti con almeno 2 dati verificabili per paragrafo."
        )
    if risposte / max(totale, 1) < 0.2:
        raccomandazioni.append(
            "❓ Struttura i contenuti in formato domanda-risposta. "
            "Usa heading come domande (es. 'Cos'è il GEO?') e rispondi direttamente nel primo paragrafo."
        )

    return raccomandazioni
