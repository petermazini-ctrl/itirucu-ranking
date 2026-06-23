# Ranking de Empresas — Itiruçu & Entroncamento de Jaguaquara

Geração automatizada de relatórios SEO com IA para empresas sem presença digital, ranqueadas por nicho e nota.

## Funcionalidades

- **Scraper Google Maps**: busca empresas por nicho em 3 regiões (Itiruçu, Entroncamento de Jaguaquara, Jaguaquara)
- **Geração de relatórios LLM**: usa Mistral (primário) ou Groq (fallback) para criar relatórios de marketing SEO
- **Ranking interativo**: página HTML com busca, 105 nichos, 789 empresas, 795 PDFs
- **PDFs otimizados**: fpdf2 com Helvetica, Latin-1, fontes 16-20pt
- **Detecção de oportunidades**: empresas com rating ≥ 4.0 sem site ou redes sociais
- **GitHub Pages**: site 100% estático — todos os relatórios pré-gerados

## Estrutura

```
google_maps_tracker/
├── google_maps_tracker.py    # Scraper principal (130+ termos)
├── generate_report.py        # Geração de relatório LLM + PDF
├── ranking_report.py         # Gera ranking_empresas.html
├── serve_ranking.py          # Servidor local para gerar relatórios sob demanda
├── batch_generate.py         # Geração em lote de relatórios
├── search_missing_niches.py  # Busca focada em nichos sub-representados
├── tracked_companies.json    # 789 empresas rastreadas
├── reports_generated.json    # Controle de 795 relatórios gerados
├── ranking_empresas.html     # Ranking interativo (GitHub Pages)
├── relatorios/               # 795 PDFs de relatórios
└── .env                      # Chaves de API (não versionado)
```

## Como usar

### 1. Configurar ambiente

```bash
python -m venv venv
venv\Scripts\activate
pip install playwright fpdf2 requests python-dotenv
playwright install chromium
```

### 2. .env

```env
MISTRAL_API_KEY=sua_chave
GROQ_API_KEY=sua_chave
TELEGRAM_TOKEN=seu_token
TELEGRAM_CHAT_ID=seu_chat_id
```

### 3. Scraping

```bash
python google_maps_tracker.py
```

### 4. Gerar relatórios

```bash
python batch_generate.py
```

### 5. Servidor local (para gerar relatórios novos)

```bash
python serve_ranking.py
# Abrir http://localhost:8000
```

### 6. Regenerar ranking

```bash
python ranking_report.py
```

## GitHub Pages

O site está em: https://petermazini-ctrl.github.io/itirucu-ranking/

O botão "Gerar" no ranking mostra um aviso para usar o servidor local — todos os 795 PDFs já estão pré-gerados e funcionam offline.

## Nichos principais

| Nicho | Empresas |
|---|---|
| Advocacia | 115 |
| Mercados / Supermercados | 77 |
| Móveis / Decoração | 40 |
| Oficina Mecânica / Auto Peças | 33 |
| Restaurantes | 28 |
| Posto de Combustível | 25 |
| Clínicas / Dentistas | 23 |
| +98 nichos | 528 |

## Contato

**Piter Mazini Mota** — 73 98814-0990 — Pitemazini@gmail.com
SEO, Gestão de Tráfego, Sites, Automação, Suporte TI, Redes
