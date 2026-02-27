"""
Modulo Qualità Contenuto & E-E-A-T
Valuta EXPERIENCE, EXPERTISE, AUTHORITATIVENESS, TRUSTWORTHINESS
con orientamento per visibilità AI (GEO) e mercato italiano.
"""

import httpx
from bs4 import BeautifulSoup
from loguru import logger
from langdetect import detect
import textstat
import re


async def analizza_contenuto(url: str) -> dict:
    logger.info(f"✍️ Analisi qualità contenuto: {url}")

    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "GEOAuditItalia/1.0 (content-quality)"})
            resp.raise_for_status()
            html = resp.text
    except Exception as e:
        logger.error(f"❌ Errore fetch contenuto {url}: {e}")
        return {"score": 0, "modulo": "contenuto", "errore": str(e)}

    soup = BeautifulSoup(html, "lxml")

    testo = ' '.join(p.get_text(separator=' ', strip=True') for p in soup.find_all('p'))
    n_parole = len(testo.split())
    lingua = None
    try:
        lingua = detect(testo) if testo else None
    except Exception:
        lingua = None

    # freshnesse: date patterns
    dates = re.findall(r"(20\d{2}[-/\.]\d{1,2}[-/\.]\d{1,2})", html)
    freshness = max(dates) if dates else None

    # EXPERIENCE
    exp_score = 0
    rec_exp = []
    # date di pubblicazione/aggiornamento
    if re.search(r"(pubblicat[ao]|aggiornato)[^\d]{0,20}(20\d{2})", html, re.IGNORECASE):
        exp_score += 25
    else:
        rec_exp.append("Manca data di pubblicazione o aggiornamento visibile.")

    if re.search(r"aut(ore|rice)?", html, re.IGNORECASE):
        exp_score += 25
    else:
        rec_exp.append("Autore non indicato nel contenuto.")

    if re.search(r"bio|chi sono|esperienza", html, re.IGNORECASE):
        exp_score += 25
    else:
        rec_exp.append("Nessuna bio o pagina autore trovata.")

    if re.search(r"caso studio|esempio concreto|clienti", html, re.IGNORECASE):
        exp_score += 25
    else:
        rec_exp.append("Mancano casi studio o esempi pratici.")

    # EXPERTISE
    expet_score = 0
    rec_expet = []
    tecnici = re.findall(r"\b(SEO|GEO|analytics|intelligenza artificiale|AI|machine learning)\b", testo, re.IGNORECASE)
    if tecnici:
        expet_score += 25
    else:
        rec_expet.append("Scarso uso di termini tecnici di settore.")

    if re.search(r"https?://(www\.)?(gov|edu|corriere\.it|repubblica\.it)", html, re.IGNORECASE):
        expet_score += 25
    else:
        rec_expet.append("Nessuna citazione di fonti autorevoli (.gov/.edu/testate IT).")

    headers = soup.find_all(re.compile(r'^h[1-6]$'))
    if headers:
        expet_score += 25
    else:
        rec_expet.append("Mancano heading strutturati (H1/H2/H3).")

    if expet_score == 75 and re.search(r"\b(FAQ|Domande frequenti)\b", html, re.IGNORECASE):
        expet_score += 25  # bonus
    elif expet_score < 75:
        rec_expet.append("Contenuto potrebbe essere più strutturato con heading adeguati.")

    # AUTHORITATIVENESS
    auth_score = 0
    rec_auth = []
    if re.search(r"chi siamo|about", html, re.IGNORECASE):
        auth_score += 25
    else:
        rec_auth.append("Pagina About/Chi siamo non rilevata.")

    if re.search(r"linkedin\.com", html, re.IGNORECASE):
        auth_score += 25
    else:
        rec_auth.append("Link a profilo LinkedIn non trovato.")

    if re.search(r"premi|certificazioni|\banni\b", html, re.IGNORECASE):
        auth_score += 25
    else:
        rec_auth.append("Poche menzioni di premi, certificazioni o anni di esperienza.")

    if re.search(r"\b(testimonianze|clienti soddisfatti)\b", html, re.IGNORECASE):
        auth_score += 25
    else:
        rec_auth.append("Mancano testimonianze o recensioni.")

    # TRUSTWORTHINESS
    trust_score = 0
    rec_trust = []
    if url.startswith("https://"):
        trust_score += 25
    else:
        rec_trust.append("Il sito non usa HTTPS.")

    if re.search(r"privacy policy", html, re.IGNORECASE):
        trust_score += 25
    else:
        rec_trust.append("Privacy policy non trovata.")

    if re.search(r"cookie policy", html, re.IGNORECASE):
        trust_score += 25
    else:
        rec_trust.append("Cookie policy non trovata.")

    if re.search(r"P\.IVA|partita iva", html, re.IGNORECASE):
        trust_score += 25
    else:
        rec_trust.append("Partita IVA non visibile.")

    # riconoscimenti bonus
    if lingua == "it":
        bonus_lang = 5
    else:
        bonus_lang = 0
    if n_parole > 800:
        bonus_len = 5
    else:
        bonus_len = 0
    if re.search(r"(FAQ|Domande frequenti)", html, re.IGNORECASE):
        bonus_faq = 5
    else:
        bonus_faq = 0

    # punteggio finale
    score = round((exp_score + expet_score + auth_score + trust_score) / 4)
    score = min(score + bonus_lang + bonus_len + bonus_faq, 100)

    raccomandazioni = []
    raccomandazioni.extend([f"EXPERIENCE: {r}" for r in rec_exp])
    raccomandazioni.extend([f"EXPERTISE: {r}" for r in rec_expet])
    raccomandazioni.extend([f"AUTHORITATIVENESS: {r}" for r in rec_auth])
    raccomandazioni.extend([f"TRUSTWORTHINESS: {r}" for r in rec_trust])

    return {
        "score": score,
        "modulo": "contenuto",
        "punteggi_eeeat": {
            "experience": exp_score,
            "expertise": expet_score,
            "authoritativeness": auth_score,
            "trustworthiness": trust_score,
        },
        "n_parole": n_parole,
        "lingua_rilevata": lingua,
        "freshness": freshness,
        "raccomandazioni": raccomandazioni,
    }
