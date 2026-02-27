"""
Modulo Brand Mentions Italia
Analizza la presenza del brand su piattaforme italiane e internazionali
citate dalle AI. Le brand mention correlano 3x più dei backlink
per la visibilità sui motori di ricerca AI.

Piattaforme monitorate:
- Wikipedia Italia
- YouTube
- LinkedIn
- Reddit (r/italy + subreddit di settore)
- Trustpilot Italia
- Pagine Gialle / Pagine Bianche
- Google Business Profile (segnali)
- Facebook
- Instagram
- Testate giornalistiche italiane
"""

import httpx
import re
from bs4 import BeautifulSoup
from loguru import logger
from urllib.parse import quote, urlparse


# Piattaforme monitorate con peso per visibilità AI
PIATTAFORME_IT = {
    "wikipedia_it": {
        "nome": "Wikipedia Italia",
        "peso": 25,
        "url_check": "https://it.wikipedia.org/w/api.php",
        "tipo": "enciclopedia",
        "importanza_ai": "CRITICA",
    },
    "wikipedia_en": {
        "nome": "Wikipedia Inglese",
        "peso": 20,
        "url_check": "https://en.wikipedia.org/w/api.php",
        "tipo": "enciclopedia",
        "importanza_ai": "CRITICA",
    },
    "youtube": {
        "nome": "YouTube",
        "peso": 15,
        "url_check": "https://www.youtube.com/results?search_query=",
        "tipo": "video",
        "importanza_ai": "ALTA",
    },
    "linkedin": {
        "nome": "LinkedIn",
        "peso": 15,
        "url_check": "https://www.linkedin.com/search/results/companies/?keywords=",
        "tipo": "professionale",
        "importanza_ai": "ALTA",
    },
    "trustpilot_it": {
        "nome": "Trustpilot Italia",
        "peso": 10,
        "url_check": "https://it.trustpilot.com/search?query=",
        "tipo": "recensioni",
        "importanza_ai": "MEDIA",
    },
    "paginegialle": {
        "nome": "Pagine Gialle",
        "peso": 8,
        "url_check": "https://www.paginegialle.it/ricerca/",
        "tipo": "directory_it",
        "importanza_ai": "MEDIA",
    },
    "facebook": {
        "nome": "Facebook",
        "peso": 7,
        "url_check": "https://www.facebook.com/search/pages/?q=",
        "tipo": "social",
        "importanza_ai": "BASSA",
    },
}

# Testate giornalistiche italiane autorevoli (citate spesso dalle AI)
TESTATE_IT = [
    "corriere.it",
    "repubblica.it",
    "sole24ore.com",
    "ansa.it",
    "lastampa.it",
    "ilsole24ore.com",
    "adnkronos.com",
    "agenzie.ansa.it",
]

HEADERS = {
    "User-Agent": "GEOAuditItalia/1.0 (brand-scanner; +https://geo-audit.it)",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
}


async def analizza_brand_mention(url: str) -> dict:
    """
    Analizza la presenza del brand sulle principali piattaforme
    italiane e internazionali citate dalle AI
    """
    logger.info(f"🏷️  Analisi brand mention: {url}")

    # Estrai nome brand dall'URL
    brand = estrai_nome_brand(url)
    logger.info(f"🔍 Brand rilevato: '{brand}'")

    risultati_piattaforme = {}
    score_totale = 0
    peso_totale = 0

    async with httpx.AsyncClient(
        timeout=20,
        follow_redirects=True,
        headers=HEADERS
    ) as client:

        # Wikipedia Italia
        risultati_piattaforme["wikipedia_it"] = await _check_wikipedia(
            client, brand, lingua="it"
        )

        # Wikipedia Inglese
        risultati_piattaforme["wikipedia_en"] = await _check_wikipedia(
            client, brand, lingua="en"
        )

        # Trustpilot Italia
        risultati_piattaforme["trustpilot_it"] = await _check_trustpilot(
            client, brand
        )

        # Pagine Gialle
        risultati_piattaforme["paginegialle"] = await _check_paginegialle(
            client, brand
        )

        # sameAs URL check (LinkedIn, YouTube, Facebook dal sito)
        risultati_piattaforme["social"] = await _check_social_dal_sito(
            client, url
        )

    # Calcolo score
    for piattaforma, dati_piattaforma in PIATTAFORME_IT.items():
        peso = dati_piattaforma["peso"]
        peso_totale += peso

        nome_chiave = piattaforma
        presente = risultati_piattaforme.get(nome_chiave, {}).get("presente", False)

        if presente:
            score_totale += peso

    # Normalizza score su 100
    score_finale = round((score_totale / peso_totale) * 100) if peso_totale > 0 else 0

    # Aggiungi bonus per presenza testate italiane
    n_social = risultati_piattaforme.get("social", {}).get("n_profili_trovati", 0)
    if n_social >= 3:
        score_finale = min(score_finale + 10, 100)
    elif n_social >= 1:
        score_finale = min(score_finale + 5, 100)

    return {
        "score": score_finale,
        "modulo": "brand_mentions",
        "brand_rilevato": brand,
        "piattaforme": risultati_piattaforme,
        "raccomandazioni": _genera_raccomandazioni_brand(
            score_finale, risultati_piattaforme, brand
        ),
    }


def estrai_nome_brand(url: str) -> str:
    """
    Estrae il nome del brand dall'URL del sito
    Esempio: https://www.digidentityagency.it → digidentity agency
    """
    try:
        parsed = urlparse(url if url.startswith("http") else "https://" + url)
        dominio = parsed.netloc or parsed.path
        # Rimuovi www. e TLD
        dominio = re.sub(r'^www\.', '', dominio)
        dominio = re.sub(r'\.(it|com|eu|net|org|io|co\.uk)$', '', dominio)
        # Converti trattini/underscore in spazi
        brand = dominio.replace("-", " ").replace("_", " ")
        return brand.strip()
    except Exception:
        return url


async def _check_wikipedia(client: httpx.AsyncClient, brand: str, lingua: str = "it") -> dict:
    """Verifica presenza su Wikipedia tramite API"""
    try:
        params = {
            "action": "query",
            "list": "search",
            "srsearch": brand,
            "format": "json",
            "srlimit": 3,
        }
        base_url = f"https://{lingua}.wikipedia.org/w/api.php"
        risposta = await client.get(base_url, params=params)
        dati = risposta.json()

        risultati = dati.get("query", {}).get("search", [])
        presente = len(risultati) > 0

        # Verifica corrispondenza esatta
        match_esatto = any(
            brand.lower() in r.get("title", "").lower()
            for r in risultati
        )

        return {
            "presente": presente,
            "match_esatto": match_esatto,
            "n_risultati": len(risultati),
            "primo_risultato": risultati[0].get("title") if risultati else None,
            "url": f"https://{lingua}.wikipedia.org/wiki/{quote(risultati[0]['title'])}" if risultati else None,
        }
    except Exception as e:
        logger.warning(f"⚠️ Wikipedia {lingua} check fallito: {e}")
        return {"presente": False, "errore": str(e)}


async def _check_trustpilot(client: httpx.AsyncClient, brand: str) -> dict:
    """Verifica presenza su Trustpilot Italia"""
    try:
        url = f"https://it.trustpilot.com/search?query={quote(brand)}"
        risposta = await client.get(url)
        soup = BeautifulSoup(risposta.text, "lxml")

        # Cerca risultati azienda
        risultati = soup.find_all("div", {"class": re.compile("businessUnit|search-result")})
        presente = len(risultati) > 0

        return {
            "presente": presente,
            "n_risultati": len(risultati),
            "url_ricerca": url,
        }
    except Exception as e:
        logger.warning(f"⚠️ Trustpilot check fallito: {e}")
        return {"presente": False, "errore": str(e)}


async def _check_paginegialle(client: httpx.AsyncClient, brand: str) -> dict:
    """Verifica presenza su Pagine Gialle"""
    try:
        url = f"https://www.paginegialle.it/{quote(brand)}/italia"
        risposta = await client.get(url)
        soup = BeautifulSoup(risposta.text, "lxml")

        # Cerca schede azienda
        schede = soup.find_all("div", {"class": re.compile("item|result|listing")})
        presente = risposta.status_code == 200 and len(schede) > 0

        return {
            "presente": presente,
            "n_schede": len(schede),
            "url_ricerca": url,
        }
    except Exception as e:
        logger.warning(f"⚠️ Pagine Gialle check fallito: {e}")
        return {"presente": False, "errore": str(e)}


async def _check_social_dal_sito(client: httpx.AsyncClient, url: str) -> dict:
    """
    Analizza il sito alla ricerca di link ai profili social
    (sameAs signals per le AI)
    """
    profili_trovati = []
    social_patterns = {
        "LinkedIn": r'linkedin\.com/company/',
        "YouTube": r'youtube\.com/@|youtube\.com/channel/',
        "Facebook": r'facebook\.com/',
        "Instagram": r'instagram\.com/',
        "Twitter/X": r'twitter\.com/|x\.com/',
        "Wikipedia": r'wikipedia\.org/wiki/',
        "TikTok": r'tiktok\.com/@',
    }

    try:
        risposta = await client.get(
            url if url.startswith("http") else "https://" + url
        )
        html = risposta.text

        for social, pattern in social_patterns.items():
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                profili_trovati.append(social)

        return {
            "presente": len(profili_trovati) > 0,
            "profili_trovati": profili_trovati,
            "n_profili_trovati": len(profili_trovati),
        }
    except Exception as e:
        logger.warning(f"⚠️ Social check dal sito fallito: {e}")
        return {"presente": False, "profili_trovati": [], "n_profili_trovati": 0}


def _genera_raccomandazioni_brand(
    score: int,
    piattaforme: dict,
    brand: str
) -> list:
    raccomandazioni = []

    wiki_it = piattaforme.get("wikipedia_it", {})
    wiki_en = piattaforme.get("wikipedia_en", {})
    trustpilot = piattaforme.get("trustpilot_it", {})
    social = piattaforme.get("social", {})

    if score < 30:
        raccomandazioni.append(
            f"🔴 CRITICO: Il brand '{brand}' ha una presenza minima sulle piattaforme "
            f"citate dalle AI. Le AI non hanno fonti autorevoli da cui attingere informazioni "
            f"su di te. Inizia con una scheda Google Business e profili LinkedIn e YouTube."
        )

    if not wiki_it.get("presente") and not wiki_en.get("presente"):
        raccomandazioni.append(
            f"📖 Wikipedia: Nessuna pagina Wikipedia trovata per '{brand}'. "
            f"Se il brand ha sufficiente notorietà, valuta la creazione di una voce Wikipedia IT. "
            f"Le AI citano Wikipedia come fonte primaria nel 67% dei casi."
        )

    if not trustpilot.get("presente"):
        raccomandazioni.append(
            f"⭐ Trustpilot: Nessuna scheda trovata su Trustpilot Italia. "
            f"Crea e verifica il profilo Trustpilot — è una delle fonti più citate "
            f"dalle AI per valutare l'affidabilità di un brand."
        )

    n_social = social.get("n_profili_trovati", 0)
    if n_social < 3:
        raccomandazioni.append(
            f"🔗 sameAs: Solo {n_social} profili social rilevati nel codice del sito. "
            f"Aggiungi i link ai profili social nel footer e implementa il campo 'sameAs' "
            f"nello schema JSON-LD Organization per rafforzare i segnali di entità per le AI."
        )

    if score >= 70:
        raccomandazioni.append(
            f"✅ Brand authority solida. Continua a costruire presenza su piattaforme "
            f"di settore italiane (blog di categoria, associazioni di categoria, "
            f"testate giornalistiche locali) per consolidare ulteriormente."
        )

    return raccomandazioni
