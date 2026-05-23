# Explainable LLM Framework for Tourist-Traffic Forecasting in Phuket

**Master's thesis** - Mathieu Zilli (University of Mons / Prince of Songkla University, 2026)

Supervisors: Prof. Kwankamon Dittakan (PSU Phuket) · Prof. Saïd Mahmoudi (UMons)

---

## What this is

This repo contains the full pipeline for a research project that fine-tunes a large language model on multimodal traffic data to forecast and explain road congestion on four tourist corridors in Phuket, Thailand.

The system takes a structured natural-language prompt describing the current month's context (weather, flights, social trends, calendar events, recent traffic history) and produces two outputs:

- a one-step-ahead numeric forecast of travel-time ratio (TTR)
- a grounded natural-language explanation of that forecast

The model is evaluated on both forecasting accuracy (MAE, RMSE, MAPE) and explanation quality (ablation fidelity, counterfactual consistency, grounding).

---

## Repository structure

```
TFE_Phuket/
├── notebooks/
│   ├── 01_eda_master.ipynb          # Exploratory analysis of the master dataset
│   ├── 02_tomtom_profiles.ipynb     # TomTom traffic profiles per corridor and time set
│   ├── 03_prepare_dataset.ipynb     # Feature engineering → ml_dataset.csv
│   ├── 04_textualize.ipynb          # Tabular rows → natural-language prompts
│   ├── 05_baselines.ipynb           # LV / HA / SN / XGBoost baselines + SHAP
│   ├── 06_llm_finetuning.ipynb      # LoRA fine-tuning + evaluation (LLM-V4 to V10)
│   └── eval/
│       ├── rag_evaluation.ipynb     # RAG chatbot end-to-end evaluation
│       └── rag_ablation.ipynb       # Embedding model and backbone ablation
│
├── scripts/
│   ├── build_master.py              # Merges all sources → phuket_master.csv
│   ├── build_calendar_features.py   # Thai holidays + Phuket events
│   ├── fetch_history_weather.py     # Open-Meteo archive API
│   ├── fetch_poi_data.py            # OpenStreetMap / Overpass API
│   ├── fetch_soc_trends.py          # Google Trends via pytrends
│   ├── generate_pt_data.py          # Phuket Smart Bus schedules
│   ├── generate_sea_data.py         # Rassada Pier ferry schedules
│   └── generate_weekly_events.py    # Night markets + local events
│
├── data/
│   ├── phuket_master.csv            # Master table: 96 rows × 101 cols (24 months × 4 corridors)
│   ├── ml_dataset.csv               # ML-ready: 96 rows × 132 cols (with lags + encoding)
│   ├── ml_train.csv / ml_val.csv / ml_test.csv
│   ├── phuket_flights_monthly.csv   # AOT official - HKT airport, 2022–2024
│   ├── phuket_weather_history_2023_2024.csv  # Open-Meteo hourly, 4 locations
│   ├── phuket_social_trends.csv     # Google Trends weekly, 5 keywords
│   ├── phuket_calendar_features.csv # Thai holidays + Phuket events
│   ├── phuket_poi_data.csv          # OpenStreetMap POIs, 5 categories
│   ├── phuket_ferry_schedule.csv    # Rassada Pier schedules
│   ├── phuket_weekly_events.csv     # Night markets + local events
│   └── phuket_public_transport.csv  # Phuket Smart Bus
│
├── final_data/
│   ├── figures/                     # All thesis figures (EDA, SHAP, predictions, loss curves)
│   └── tables/                      # Canonical result tables (baselines, SHAP, LLM metrics)
│
├── llm/
│   ├── requirements_gpu.txt         # GPU environment (CUDA, transformers, peft, trl)
│   └── VERSION_SUMMARY.md           # Summary of LLM versions V4–V10 with key results
│
├── backend/                         # RAG chatbot backend (FastAPI + ChromaDB)
│   ├── main.py
│   └── rag/
│       ├── ingest.py                # Indexes data into ChromaDB
│       ├── retriever.py             # Retrieval logic + query router
│       └── prompt_builder.py        # Prompt assembly for chatbot queries
│
├── api/                             # Main FastAPI server (serves the frontend)
│   └── main.py                      # All endpoints: /chat, /forecast, /explain, /whatif
│
├── frontend/                        # Next.js chatbot interface
│   ├── package.json
│   └── next.config.js
│
└── tomtom_phuket/                   # TomTom MOVE API pipeline (scripts only, data excluded)
    ├── config.py                    # 4 corridors, time sets, date ranges, job plan
    ├── submit_jobs.py               # Submit → poll → download jobs from TomTom MOVE API
    ├── parse_results.py             # JSON responses → CSV (segments_all, summaries_all)
    └── requirements.txt
```

---

## The four corridors

| ID  | Name         | Route                                  | Key characteristic                                |
| --- | ------------ | -------------------------------------- | ------------------------------------------------- |
| 0   | Airport Road | Route 402 : HKT Airport → Thalang      | Main tourist axis, moderate congestion (PTI 2.04) |
| 1   | Patong Hill  | Route 4029 : Kathu → Patong Beach      | Most congested at PM peak (PTI 2.39)              |
| 2   | Town → Rawai | Route 4022 : Phuket Town → Rawai Beach | Highest PTI (2.81 at AM peak)                     |
| 3   | Bypass Road  | Route 4027 : Kathu → Chalong           | Baseline reference, off-peak (PTI 1.95)           |

---

## Data sources

| Code   | Category                  | Source                       | Period                        |
| ------ | ------------------------- | ---------------------------- | ----------------------------- |
| TT/SPD | Traffic (TTR, speed, PTI) | TomTom MOVE API              | Jan 2023 – Dec 2024           |
| WX     | Weather                   | Open-Meteo archive           | 2023–2024 (2022 extrapolated) |
| FLT    | Flight arrivals           | AOT annual statistics        | 2022–2024                     |
| SOC    | Social signal             | Google Trends (pytrends)     | 2022–2024                     |
| CAL    | Calendar                  | Calendarific + custom events | 2023–2024                     |
| POI    | Points of interest        | OpenStreetMap / Overpass     | Static                        |
| SEA    | Ferry                     | Rassada Pier schedules       | 2022–2024                     |
| PT     | Public transport          | Phuket Smart Bus             | 2022–2024                     |
| EVT    | Local events              | Rule-based script            | 2023–2024                     |

The master table (`phuket_master.csv`) merges all sources at monthly × corridor granularity: 96 rows, 101 columns, zero missing values.

---

## LLM framework

**Base model**: LLaMA 3.1 8B Instruct  
**Fine-tuning**: LoRA (r=16, α=32, dropout=0.1, target modules: q/k/v/o_proj)  
**Hardware**: single RTX 4080 SUPER

Each training sample is serialized into a structured natural-language prompt with a `[CONTEXT]` block (weather, flights, trends, calendar, POIs) and a `[HISTORY]` block (3 months of lagged TTR, PTI, speed). The model handles two question types within a single instruction-tuned framework:

- **Forecast** - returns a JSON object with `next_month_am_tt_ratio`
- **Explanation** - returns a free-text rationale grounded in the prompt context

Three versions reported in the thesis:

| Version | Description                           | MAE   | Ablation fidelity | Grounding |
| ------- | ------------------------------------- | ----- | ----------------- | --------- |
| V4      | Full context, no traffic memory       | 0.120 | 70%               | 45%       |
| V9      | + 3-month lagged traffic features     | 0.131 | 100%              | 95%       |
| V10     | + year-over-year and corridor ranking | 0.146 | 100%              | 90%       |

**V9 is the recommended version**: best explainability across all three protocol tests (100% ablation fidelity, 100% counterfactual consistency, 95% grounding).

Baselines for reference: Last Value MAE 0.145, Historical Average = Seasonal Naive MAE 0.088, XGBoost MAE 0.098.

See [`llm/VERSION_SUMMARY.md`](llm/VERSION_SUMMARY.md) for the full version history (V4–V10).

---

## Explainability evaluation

Three protocol-based tests assess whether explanations are faithful, not just fluent:

1. **Ablation fidelity** - remove a key input (e.g., flight arrivals); check that the explanation stops mentioning it
2. **Counterfactual consistency** - flip a key factor (e.g., high-season → low-season); check that the prediction and direction of reasoning change accordingly
3. **Grounding** - scan the explanation for claims unsupported by the input context

All computed automatically via keyword matching and directional-consistency checks on the test set (n=20).

---

## RAG chatbot

A retrieval-augmented chatbot built on ChromaDB answers natural-language questions from city operators and tourism planners. It covers 100 question types across six intents: nowcast, forecast, explain, what-if, decision, and tourism.

- **Embedding model**: paraphrase-multilingual-MiniLM-L12-v2 (Recall@10 = 0.917)
- **Query router**: keyword-based intent classifier (6 classes)
- **Best backbone**: Qwen2.5 14B + refine agent (Faithfulness = 1.000)
- **Vector DB**: 10 ChromaDB collections, one per data source type

---

## Setup

### Standard environment

```bash
pip install pandas numpy scikit-learn xgboost shap pytrends requests python-dotenv
```

### GPU environment (LLM fine-tuning)

```bash
pip install -r llm/requirements_gpu.txt
```

Requires CUDA 12.x and at least 16 GB VRAM (tested on RTX 4080 SUPER, 16 GB).

### API keys

Create a `.env` file at the project root (never committed):

```
TOMTOM_API_KEY=...
OWM_API_KEY=...
CALENDARIFIC_API_KEY=...
```

---

## Reproducing the results

```bash
# 1. Rebuild master table from raw sources
python scripts/build_master.py

# 2. Feature engineering → ml_dataset.csv
# Run notebook 03_prepare_dataset.ipynb

# 3. Baselines + SHAP
# Run notebook 05_baselines.ipynb

# 4. Textualize → structured prompts
# Run notebook 04_textualize.ipynb

# 5. LoRA fine-tuning (requires GPU)
# Run notebook 06_llm_finetuning.ipynb
# Select version cell: set VERSION = "v9_forecast_traffic_memory_scratch"

# 6. RAG chatbot evaluation
# Run notebooks/eval/rag_evaluation.ipynb
```

Pre-computed results and all thesis figures are in `final_data/`.

---

## Notes on data quality

- **Weather 2022**: extrapolated from 2023 seasonal profile (same month, -1 year). Documented in thesis Chapter 3.
- **Ferry/transport passenger volumes**: real schedules, synthetic demand figures. Documented in thesis Chapter 3.
- **TomTom coverage**: full 24-month dataset (Jan 2023 – Dec 2024) used for training. Extended access obtained via institutional contact.

---

## Citation

If you use this code or dataset in your work:

```
Zilli, M. (2026). Explainable LLM Framework for Tourist-Traffic Forecasting in Phuket, Thailand.
Master's thesis, University of Mons / Prince of Songkla University.
```
