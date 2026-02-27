"""
GEO Audit Italia — Report Generator con Claude AI
Genera report HTML da 30-50 pagine con raccomandazioni personalizzate
Powered by DigIdentity Agency
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from loguru import logger
import anthropic

# Configurazione
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
REPORT_OUTPUT_DIR = os.getenv("REPORT_OUTPUT_DIR", "reports/output/")
REPORT_LOGO_PATH = os.getenv("REPORT_LOGO_PATH", "frontend/assets/images/logo-digidentity.png")

client_ai = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
jinja_env = Environment(loader=FileSystemLoader("backend/templates"))


# ============================================================
# FUNZIONI CLAUDE AI — Raccomandazioni personalizzate
# ============================================================

async def genera_analisi_claude(sezione: str, dati: dict, url_sito: str) -> str:
    """
    Usa Claude per generare analisi personalizzata in italiano
    per ogni sezione del report
    """
    prompts = {
        "executive_summary": f"""Sei un esperto di GEO (Generative Engine Optimization) italiano.
Analizza questi dati di audit GEO per il sito {url_sito} e scrivi un Executive Summary professionale in italiano.

Dati audit:
- GEO Score complessivo: {dati.get('geo_score', 0)}/100
- Citabilità AI: {dati.get('moduli', {}).get('citabilita', {}).get('score', 0)}/100
- Crawler AI: {dati.get('moduli', {}).get('crawler', {}).get('score', 0)}/100
- Brand Authority: {dati.get('moduli', {}).get('brand', {}).get('score', 0)}/100
- Schema Markup: {dati.get('moduli', {}).get('schema', {}).get('score', 0)}/100
- Qualità Contenuto E-E-A-T: {dati.get('moduli', {}).get('contenuto', {}).get('score', 0)}/100

Scrivi 3-4 paragrafi che:
1. Descrivono la situazione attuale del sito rispetto alla visibilità AI
2. Identificano i punti di forza principali
3. Identificano le criticità più urgenti
4. Danno una prospettiva di miglioramento realistica

Tono: professionale ma diretto, come un consulente senior italiano.
Lunghezza: 300-400 parole.""",

        "citabilita": f"""Sei un esperto di GEO italiano. Analizza questi dati di citabilità AI per {url_sito}:

{json.dumps(dati, ensure_ascii=False, indent=2)}

Scrivi un'analisi dettagliata in italiano che include:
1. Valutazione della struttura dei contenuti per la citabilità AI
2. Analisi specifica dei punti deboli trovati
3. 5 raccomandazioni concrete e prioritizzate
4. Esempi pratici di come riscrivere i contenuti per essere citati da ChatGPT/Perplexity
5. Template di paragrafo ottimale per la citabilità AI

Tono: tecnico ma comprensibile, con esempi pratici.
Lunghezza: 400-500 parole.""",

        "crawler": f"""Sei un esperto di GEO italiano. Analizza questi dati sui crawler AI per {url_sito}:

{json.dumps(dati, ensure_ascii=False, indent=2)}

Scrivi un'analisi dettagliata in italiano che include:
1. Stato attuale dell'accesso dei crawler AI al sito
2. Impatto di ogni crawler bloccato sulla visibilità AI
3. Istruzioni passo-passo per il robots.txt ottimizzato
4. Spiegazione del file llms.txt e come implementarlo
5. Priorità degli interventi con impatto stimato

Includi il codice robots.txt ottimizzato pronto all'uso.
Lunghezza: 400-500 parole.""",

        "brand": f"""Sei un esperto di GEO e brand authority italiano. Analizza questi dati per {url_sito}:

{json.dumps(dati, ensure_ascii=False, indent=2)}

Scrivi un'analisi dettagliata in italiano che include:
1. Valutazione della presenza del brand sulle piattaforme AI-cited
2. Impatto delle brand mention sulla visibilità AI (dati e ricerche)
3. Piano d'azione per costruire brand authority in Italia
4. Strategia Wikipedia: quando e come creare/migliorare la voce
5. Strategia LinkedIn, YouTube e piattaforme italiane di settore
6. Template outreach per ottenere citazioni da fonti autorevoli italiane

Lunghezza: 450-550 parole.""",

        "schema": f"""Sei un esperto di Schema Markup e dati strutturati per il mercato italiano. Analizza per {url_sito}:

{json.dumps(dati, ensure_ascii=False, indent=2)}

Scrivi un'analisi dettagliata in italiano che include:
1. Schema markup rilevati e valutazione della completezza
2. Schema mancanti critici per la visibilità AI
3. Spiegazione del perché ogni schema è importante per le AI
4. Istruzioni di implementazione per ogni schema consigliato
5. Errori comuni nel Schema Markup italiano da evitare

Lunghezza: 400-500 parole.""",

        "contenuto": f"""Sei un esperto di E-E-A-T e qualità contenuto per il mercato italiano. Analizza per {url_sito}:

{json.dumps(dati, ensure_ascii=False, indent=2)}

Scrivi un'analisi dettagliata in italiano che include:
1. Valutazione dei 4 pilastri E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness)
2. Analisi della leggibilità per il pubblico italiano
3. Problemi di freshness e aggiornamento contenuti
4. 5 raccomandazioni prioritizzate per migliorare l'E-E-A-T
5. Checklist pratica per l'ottimizzazione dei contenuti

Lunghezza: 450-550 parole.""",

        "piano_azione": f"""Sei un consulente GEO senior italiano. Basandoti su questo audit completo per {url_sito}:

GEO Score: {dati.get('geo_score', 0)}/100
Priorità identificate: {json.dumps(dati.get('priorita', []), ensure_ascii=False)}

Crea un piano d'azione dettagliato in italiano con:
1. INTERVENTI IMMEDIATI (0-7 giorni): azioni quick win ad alto impatto
2. INTERVENTI BREVE TERMINE (7-30 giorni): ottimizzazioni strutturali
3. INTERVENTI MEDIO TERMINE (30-90 giorni): costruzione autorità e brand
4. KPI da monitorare per misurare i progressi
5. Stima realistica del miglioramento del GEO Score per ogni fase

Tono: concreto, con stime di tempo e impatto per ogni azione.
Lunghezza: 500-600 parole.""",

        "benchmark": f"""Sei un esperto di GEO italiano con conoscenza del mercato italiano. Per il sito {url_sito} con GEO Score {dati.get('geo_score', 0)}/100:

Scrivi una sezione di benchmark in italiano che include:
1. Posizionamento del sito rispetto alla media italiana del settore rilevato
2. Cosa fanno i siti italiani più citati dalle AI nel settore
3. Gap principali da colmare rispetto ai competitor
4. Opportunità specifiche per il mercato italiano
5. Trend GEO 2026 rilevanti per questo tipo di sito

Lunghezza: 350-450 parole.""",
    }

    prompt = prompts.get(sezione, "")
    if not prompt:
        return ""

    try:
        loop = asyncio.get_event_loop()
        risposta = await loop.run_in_executor(
            None,
            lambda: client_ai.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
        )
        return risposta.content[0].text
    except Exception as e:
        logger.error(f"❌ Errore Claude API per sezione {sezione}: {e}")
        return f"Analisi non disponibile per questa sezione. Errore: {str(e)}"


# ============================================================
# FUNZIONI UTILITY
# ============================================================

def get_giudizio_score(score: int) -> dict:
    """Restituisce etichetta, colore ed emoji basati sul GEO Score"""
    if score <= 30:
        return {"etichetta": "Invisibile alle AI", "colore": "#EF4444", "emoji": "🔴", "bg": "#FEE2E2"}
    elif score <= 50:
        return {"etichetta": "Visibilità minima", "colore": "#F97316", "emoji": "🟠", "bg": "#FEF3C7"}
    elif score <= 70:
        return {"etichetta": "In sviluppo", "colore": "#F59E0B", "emoji": "🟡", "bg": "#FEF9C3"}
    elif score <= 85:
        return {"etichetta": "Buona visibilità", "colore": "#10B981", "emoji": "🟢", "bg": "#D1FAE5"}
    else:
        return {"etichetta": "Eccellente", "colore": "#3B82F6", "emoji": "💎", "bg": "#DBEAFE"}


def formatta_data(iso_string: str) -> str:
    """Converte ISO datetime in formato italiano"""
    mesi = [
        "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
        "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"
    ]
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return f"{dt.day} {mesi[dt.month-1]} {dt.year} ore {dt.strftime('%H:%M')}"
    except Exception:
        return datetime.now().strftime("%d/%m/%Y %H:%M")


def genera_robots_ottimizzato(crawler_bloccati: list) -> str:
    """Genera robots.txt ottimizzato per i crawler AI"""
    return """User-agent: *
Allow: /

# ✅ Crawler AI esplicitamente consentiti
User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Gemini
Allow: /

User-agent: Bingbot
Allow: /

User-agent: Meta-ExternalAgent
Allow: /

User-agent: Applebot-Extended
Allow: /

User-agent: YouBot
Allow: /

# Sitemap
Sitemap: https://TUOSITO.it/sitemap.xml"""


def genera_llmstxt(url_sito: str, brand: str) -> str:
    """Genera file llms.txt base per il sito"""
    return f"""# {brand}

> Sito web ufficiale di {brand}. 
> Fornitore di [descrivi il tuo servizio/prodotto principale].

## Informazioni principali

- **Nome**: {brand}
- **Sito**: {url_sito}
- **Settore**: [inserisci settore]
- **Sede**: Italia
- **Contatti**: [inserisci email]

## Contenuti principali

- [URL pagina principale]: Descrizione della pagina principale
- [URL servizi]: I nostri servizi e soluzioni
- [URL about]: Chi siamo e la nostra storia
- [URL blog]: Articoli e risorse

## Cosa facciamo

[Descrizione dettagliata dell'azienda e dei servizi in 2-3 paragrafi]

## Per i modelli AI

Questo sito è autorizzato per il crawling e l'indicizzazione da parte di tutti i 
modelli di linguaggio AI. I contenuti sono originali e aggiornati regolarmente.
Lingua principale: Italiano.
"""


# ============================================================
# GENERATORE REPORT PRINCIPALE
# ============================================================

async def genera_pdf_report(
    risultati: dict,
    url_sito: str,
    email_cliente: str,
    session_id: str,
) -> str:
    """
    Genera report HTML completo con Claude AI
    Restituisce il percorso del file HTML generato
    """
    logger.info(f"📄 Generazione report per: {url_sito}")
    inizio = datetime.now()

    # Crea directory output
    Path(REPORT_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # Genera tutte le analisi Claude in parallelo
    logger.info("🤖 Generazione analisi Claude AI in corso...")
    
    moduli = risultati.get("moduli", {})
    
    analisi_tasks = await asyncio.gather(
        genera_analisi_claude("executive_summary", risultati, url_sito),
        genera_analisi_claude("citabilita", moduli.get("citabilita", {}), url_sito),
        genera_analisi_claude("crawler", moduli.get("crawler", {}), url_sito),
        genera_analisi_claude("brand", moduli.get("brand", {}), url_sito),
        genera_analisi_claude("schema", moduli.get("schema", {}), url_sito),
        genera_analisi_claude("contenuto", moduli.get("contenuto", {}), url_sito),
        genera_analisi_claude("piano_azione", risultati, url_sito),
        genera_analisi_claude("benchmark", risultati, url_sito),
        return_exceptions=True,
    )

    analisi = {
        "executive_summary": analisi_tasks[0] if not isinstance(analisi_tasks[0], Exception) else "",
        "citabilita": analisi_tasks[1] if not isinstance(analisi_tasks[1], Exception) else "",
        "crawler": analisi_tasks[2] if not isinstance(analisi_tasks[2], Exception) else "",
        "brand": analisi_tasks[3] if not isinstance(analisi_tasks[3], Exception) else "",
        "schema": analisi_tasks[4] if not isinstance(analisi_tasks[4], Exception) else "",
        "contenuto": analisi_tasks[5] if not isinstance(analisi_tasks[5], Exception) else "",
        "piano_azione": analisi_tasks[6] if not isinstance(analisi_tasks[6], Exception) else "",
        "benchmark": analisi_tasks[7] if not isinstance(analisi_tasks[7], Exception) else "",
    }

    logger.success("✅ Analisi Claude completate")

    # Prepara dati template
    geo_score = risultati.get("geo_score", 0)
    giudizio = get_giudizio_score(geo_score)
    
    # Genera robots.txt ottimizzato
    crawler_bloccati = moduli.get("crawler", {}).get("crawler_bloccati", [])
    robots_ottimizzato = genera_robots_ottimizzato(crawler_bloccati)
    
    # Genera llms.txt
    from backend.engine.brand_mentions import estrai_nome_brand
    brand = estrai_nome_brand(url_sito)
    llmstxt = genera_llmstxt(url_sito, brand)

    # Carica labels
    try:
        with open("data/copy/report_labels.json", "r", encoding="utf-8") as f:
            labels = json.load(f)
    except Exception:
        labels = {}

    # Dati completi per il template
    template_data = {
        "url_sito": url_sito,
        "email_cliente": email_cliente,
        "session_id": session_id,
        "data_analisi": formatta_data(risultati.get("data_analisi", datetime.now().isoformat())),
        "durata_secondi": risultati.get("durata_secondi", 0),
        "geo_score": geo_score,
        "giudizio": giudizio,
        "moduli": moduli,
        "priorita": risultati.get("priorita", []),
        "analisi": analisi,
        "robots_ottimizzato": robots_ottimizzato,
        "llmstxt": llmstxt,
        "brand": brand,
        "labels": labels,
        "anno": datetime.now().year,
    }

    # Renderizza template HTML
    try:
        template = jinja_env.get_template("report_ita.html")
        html_content = template.render(**template_data)
    except Exception as e:
        logger.error(f"❌ Errore rendering template: {e}")
        html_content = f"<html><body><h1>Errore generazione report: {e}</h1></body></html>"

    # Salva file HTML
    dominio = url_sito.replace("https://", "").replace("http://", "").replace("/", "-").replace(".", "-")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_file = f"GEO-Report-{dominio}-{timestamp}"
    
    percorso_html = os.path.join(REPORT_OUTPUT_DIR, f"{nome_file}.html")
    percorso_pdf = os.path.join(REPORT_OUTPUT_DIR, f"{nome_file}.pdf")

    with open(percorso_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.success(f"✅ Report HTML salvato: {percorso_html}")

    # Genera PDF con WeasyPrint
    try:
        from weasyprint import HTML
        HTML(filename=percorso_html).write_pdf(percorso_pdf)
        logger.success(f"✅ PDF generato: {percorso_pdf}")
        percorso_finale = percorso_pdf
    except Exception as e:
        logger.warning(f"⚠️ WeasyPrint non disponibile, uso HTML: {e}")
        percorso_finale = percorso_html

    durata = (datetime.now() - inizio).seconds
    logger.success(f"🎉 Report completo generato in {durata}s")

    return percorso_finale
