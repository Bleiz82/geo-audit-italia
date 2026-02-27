# 🇮🇹 GEO Audit Italia — by DigIdentity Agency

**GEO-first, SEO-supportato.** Il primo motore di audit GEO completamente in italiano.
Ottimizza la presenza dei tuoi clienti sui motori di ricerca AI (ChatGPT, Perplexity,
Claude, Gemini, Google AI Overviews) mantenendo solide fondamenta SEO tradizionali.

> **La ricerca AI sta divorando quella tradizionale.**
> Questo tool ottimizza per dove sta andando il traffico, non per dove era.

---

## 🇮🇹 Perché il GEO è la prossima frontiera per le agenzie italiane

| Metrica | Valore |
|--------|--------|
| Mercato GEO globale | $886M (proiettato $7.3B entro il 2031) |
| Crescita traffico referral da AI | +527% anno su anno |
| Conversione traffico AI vs organico | 4.4x superiore |
| Calo traffico search previsto da Gartner entro 2028 | -50% |
| Brand mention vs backlink per visibilità AI | 3x più forte correlazione |
| Marketer italiani che investono in GEO | Solo ~23% |

---

## 🚀 Quick Start

### Installazione (macOS/Linux)

```bash
git clone https://github.com/TUO-USERNAME/geo-audit-italia.git
cd geo-audit-italia
cp .env.example .env
pip install -r requirements.txt
uvicorn backend.main:app --reload
```


Requisiti
Python 3.8+
Account Stripe (test o live)
Account Resend.com (invio email)
Redis (per la coda asincrona)

⚙️ Comandi Engine (uso interno agenzia)
Comando
Funzione
python engine/geo_audit.py <url>
Audit GEO + SEO completo con agenti paralleli
python engine/citability.py <url>
Score di citabilità AI del contenuto
python engine/crawlers.py <url>
Verifica accesso AI crawler (robots.txt)
python engine/llmstxt.py <url>
Analisi o generazione llms.txt
python engine/brand_mentions.py <url>
Scansione brand mention su piattaforme AI-cited
python engine/schema_analyzer.py <url>
Analisi dati strutturati JSON-LD
python engine/content_quality.py <url>
Qualità contenuto & E-E-A-T
python engine/report_generator.py
Genera report PDF professionale in italiano


🏗️ Architettura
geo-audit-italia/
│
├── frontend/
│   ├── index.html               # Landing page IT (conversione)
│   ├── checkout.html            # Pagina checkout Stripe
│   ├── success.html             # Pagina post-pagamento
│   └── assets/
│       ├── css/style.css
│       ├── js/main.js
│       └── images/
│
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── api/
│   │   ├── stripe_webhook.py    # Gestione webhook Stripe
│   │   ├── audit_trigger.py     # Trigger audit dopo pagamento
│   │   └── email_sender.py      # Invio report via Resend
│   ├── engine/
│   │   ├── geo_audit.py         # Orchestratore principale (5 agenti paralleli)
│   │   ├── citability.py        # Analisi citabilità AI
│   │   ├── crawlers.py          # Analisi AI crawler
│   │   ├── brand_mentions.py    # Scanner brand mention IT
│   │   ├── schema_analyzer.py   # Analisi struttura dati
│   │   ├── content_quality.py   # E-E-A-T e qualità contenuto
│   │   └── report_generator.py  # Generatore PDF report IT
│   └── templates/
│       └── report_ita.html      # Template HTML report in italiano
│
├── data/
│   ├── schema/
│   │   ├── local-business-it.json
│   │   ├── organization-it.json
│   │   ├── article-author-it.json
│   │   └── ecommerce-it.json
│   └── copy/
│       ├── landing_copy.md      # Copy landing page IT
│       └── report_labels.json   # Label report in italiano
│
├── .env.example
├── requirements.txt
├── docker-compose.yml
└── README.md


🔄 Come Funziona il Flusso Completo
Flusso Automatico (SaaS)
Quando un cliente completa il pagamento su geo-audit.it:
Lead Capture — Inserisce URL del sito + email su landing page
Stripe Checkout — Pagamento sicuro €97 (singolo) o €297/mese (agency)
Webhook Trigger — Stripe notifica il backend con i dati dell'ordine
Avvio Engine — 5 moduli paralleli analizzano il sito in ~3 minuti
Generazione PDF — Report professionale branded in italiano
Email Delivery — PDF inviato automaticamente via Resend.com
Metodologia di Scoring
Categoria
Peso
Citabilità AI & Visibilità
25%
Autorità del Brand (menzioni)
20%
Qualità Contenuto & E-E-A-T
20%
Fondamenta Tecniche
15%
Dati Strutturati (Schema)
10%
Ottimizzazione Piattaforme
10%


🎯 Target di Mercato Italiano
Web Agency & SEO Agency — Audit automatizzati per i propri clienti
Consulenti di Marketing Digitale — Nuovo servizio ad alto valore aggiunto
PMI Italiane — Scoprire la propria invisibilità AI prima dei competitor
E-commerce — Ottimizzare schede prodotto per AI shopping
Attività Locali — Essere trovati dagli assistenti AI locali

💶 Pricing (mercato italiano)
Piano
Prezzo
Contenuto
Audit Singolo
€97
1 audit completo + PDF report
Agency Monthly
€297/mese
10 audit/mese + white label PDF
Agency Annual
€197/mese
10 audit/mese + white label + priority support


📜 Licenza
MIT License — Fork libero, attribuzione apprezzata.

🤝 Contributi
Contributi benvenuti! Leggi docs/CONTRIBUTING.md prima di aprire una PR.

Costruito per l'era della ricerca AI. Made in Sardinia 🇮🇹 Powered by DigIdentity Agency

---
