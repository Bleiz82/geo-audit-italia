"""
Modulo Analisi AI Crawler
Verifica se i principali crawler delle AI possono accedere al sito.
Analizza robots.txt e verifica presenza del file llms.txt.
"""

import httpx
import re
from loguru import logger
from urllib.parse import urljoin


# I 15 principali crawler AI da monitorare nel 2026
CRAWLER_AI = {
    "GPTBot": "OpenAI / ChatGPT",
    "ChatGPT-User": "OpenAI / ChatGPT (browsing)",
    "OAI-SearchBot": "OpenAI Search",
    "ClaudeBot": "Anthropic / Claude",
    "anthropic-ai": "Anthropic AI",
    "PerplexityBot": "Perplexity AI",
    "Googlebot": "Google (AI Overviews)",
    "Google-Extended": "Google AI (Gemini training)",
    "Gemini": "Google Gemini",
    "Bingbot": "Microsoft / Copilot",
    "bingbot": "Microsoft / Copilot",
    "FacebookBot": "Meta AI",
    "Meta-ExternalAgent": "Meta AI",
    "Applebot-Extended": "Apple Intelligence",
    "YouBot": "You.com AI",
    "cohere-ai": "Cohere AI",
}


async def analizza_crawler(url: str) -> dict:
    """
    Analizza robots.txt per accesso AI crawler e verifica llms.txt
    """
    logger.info(f"🤖 Analisi crawler AI: {url}")

    # Normalizza URL base
    if not url.startswith("http"):
        url = "https://" + url
    base_url = "/".join(url.split("/")[:3])

    robots_url = urljoin(base_url, "/robots.txt")
    llmstxt_url = urljoin(base_url, "/llms.txt")

    risultato = {
        "score": 0,
        "modulo": "crawler",
        "robots_url": robots_url,
        "llmstxt_url": llmstxt_url,
        "crawler_consentiti": [],
        "crawler_bloccati": [],
        "crawler_non_specificati": [],
        "ai_bloccati": False,
        "llmstxt_presente": False,
        "llmstxt_valido": False,
        "raccomandazioni": [],
    }

    # Analisi robots.txt
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(robots_url)

            if resp.status_code == 200:
                robots_content = resp.text
                risultato.update(
                    _analizza_robots_txt(robots_content)
                )
            else:
                risultato["raccomandazioni"].append(
                    "ℹ️ File robots.txt non trovato. Crea un robots.txt esplicito che consenta i crawler AI."
                )

    except Exception as e:
        logger.warning(f"⚠️ Impossibile leggere robots.txt: {e}")

    # Verifica llms.txt
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp_llms = await client.get(llmstxt_url)
            if resp_llms.status_code == 200 and len(resp_llms.text) > 50:
                risultato["llmstxt_presente"] = True
                risultato["llmstxt_valido"] = _valida_llmstxt(resp_llms.text)
                if risultato["llmstxt_valido"]:
                    risultato["raccomandazioni"].append(
                        "✅ File llms.txt presente e valido. Ottimo per la visibilità AI."
                    )
                else:
                    risultato["raccomandazioni"].append(
                        "⚠️ File llms.txt presente ma incompleto. Migliora la struttura."
                    )
            else:
                risultato["raccomandazioni"].append(
                    "❌ File llms.txt assente. Generalo per migliorare la comprensione "
                    "del tuo sito da parte dei crawler AI."
                )
    except Exception:
        pass

    # Calcolo score
    risultato["score"] = _calcola_score_crawler(risultato)

    return risultato


def _analizza_robots_txt(contenuto: str) -> dict:
    """Analizza il contenuto del robots.txt per ogni crawler AI"""
    consentiti = []
    bloccati = []
    non_specificati = []

    righe = contenuto.lower().split("\n")
    user_agent_corrente = None
    regole = {}  # user_agent → {"disallow": [...], "allow": []}

    for riga in righe:
        riga = riga.strip()
        if riga.startswith("user-agent:"):
            user_agent_corrente = riga.split(":", 1)[1].strip()
            if user_agent_corrente not in regole:
                regole[user_agent_corrente] = {"disallow": [], "allow": []}
        elif riga.startswith("disallow:") and user_agent_corrente:
            path = riga.split(":", 1)[1].strip()
            regole[user_agent_corrente]["disallow"].append(path)
        elif riga.startswith("allow:") and user_agent_corrente:
            path = riga.split(":", 1)[1].strip()
            regole[user_agent_corrente]["allow"].append(path)

    ai_bloccati = False

    for crawler, descrizione in CRAWLER_AI.items():
        crawler_lower = crawler.lower()
        regole_specifiche = regole.get(crawler_lower, None)
        regole_globali = regole.get("*", {"disallow": [], "allow": []})

        if regole_specifiche is not None:
            if "/" in regole_specifiche.get("disallow", []):
                bloccati.append({"crawler": crawler, "piattaforma": descrizione, "fonte": "regola specifica"})
                ai_bloccati = True
            else:
                consentiti.append({"crawler": crawler, "piattaforma": descrizione})
        elif "/" in regole_globali.get("disallow", []):
            bloccati.append({"crawler": crawler, "piattaforma": descrizione, "fonte": "regola globale *"})
            ai_bloccati = True
        else:
            non_specificati.append({"crawler": crawler, "piattaforma": descrizione})

    return {
        "crawler_consentiti": consentiti,
        "crawler_bloccati": bloccati,
        "crawler_non_specificati": non_specificati,
        "ai_bloccati": ai_bloccati,
    }


def _valida_llmstxt(contenuto: str) -> bool:
    """Verifica che llms.txt abbia i campi fondamentali"""
    campi_richiesti = ["# ", "## ", "http"]
    return all(campo in contenuto for campo in campi_richiesti)


def _calcola_score_crawler(r: dict) -> int:
    score = 100

    if r["ai_bloccati"]:
        score -= 40
    n_bloccati = len(r["crawler_bloccati"])
    score -= min(n_bloccati * 5, 30)

    if not r["llmstxt_presente"]:
        score -= 15
    elif not r["llmstxt_valido"]:
        score -= 7

    return max(score, 0)
