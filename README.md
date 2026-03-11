<div align="center">

# 🤖 YTAIMBot

### Автономний YouTube контент-конвеєр на базі ML

[![CI](https://github.com/Dmitze/YTAIMBot/actions/workflows/ci.yml/badge.svg)](https://github.com/Dmitze/YTAIMBot/actions)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Coverage](https://img.shields.io/badge/coverage-80%25-yellowgreen)](https://github.com/Dmitze/YTAIMBot)
[![Tasks](https://img.shields.io/badge/roadmap-640%20tasks-orange)](docs/ROADMAP_AI_AGENT_TASKS.md)
[![Target](https://img.shields.io/badge/target-%245K%2B%2Fmonth-brightgreen)](docs/MONETIZATION_ANALYTICS_GUIDE.md)

**Тренди → Сценарій → Озвучення → Відео → Публікація — повністю автоматично**

[Roadmap (640 задач)](docs/ROADMAP_AI_AGENT_TASKS.md) •
[Архітектура](#-архітектура) •
[Швидкий старт](#-швидкий-старт) •
[Алгоритми](#-алгоритми--структури-даних) •
[Метрики](#-цільові-метрики)

</div>

---

## 🎯 Що це таке

**YTAIMBot** — повністю автономний конвеєр що:

1. 🔍 **Знаходить** трендові теми (Google Trends + YouTube API)
2. ✍️ **Генерує** відеосценарій через локальний LLM (Ollama)
3. 🔊 **Озвучує** текст (Edge-TTS → Coqui TTS fallback, підтримка 🇺🇦 uk-UA)
4. 🎬 **Монтує** відео (MoviePy + FFmpeg, 1080p/30fps)
5. 🖼️ **Генерує** thumbnail (Pillow, 1280×720, CTR-оптимізований)
6. 🛡️ **Перевіряє** якість (Bayesian gate + Cosine Similarity + Compliance)
7. 📤 **Публікує** на YouTube (OAuth2, unlisted-first, AI disclosure)
8. 📈 **Навчається** з метрик (EMA feedback → UCB1 Bandit → краще наступного разу)

**Ціль:** $5 000+/місяць пасивного доходу від AdSense на автопілоті.

---

## 🏗️ Архітектура

### 12-стадійний конвеєр

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        YTAIMBOT PIPELINE v1.0                           │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────────────┤
│ STAGE 1  │ STAGE 2  │ STAGE 3  │ STAGE 4  │ STAGE 5  │    STAGE 6       │
│ INGEST   │FEATURIZE │  REDUCE  │  SCORE   │   PLAN   │      GATE        │
│          │          │  (SVD)   │ (L2 norm)│  top-5   │ Bayes+Cosine     │
│ Google   │ hash →   │Truncated │ sorted   │ Content  │ P(bad|features)  │
│ Trends + │ features │SVD (k=2) │  desc    │  Plans   │ + similarity     │
│ YouTube  │          │          │          │          │ fail-closed ✋    │
├──────────┴──────────┴──────────┴──────────┴──────────┴──────────────────┤
│ STAGE 7  │ STAGE 8  │ STAGE 9  │ STAGE 10 │ STAGE 11 │    STAGE 12      │
│  SCRIPT  │  AUDIO   │SUBTITLES │  VIDEO   │THUMBNAIL │    PUBLISH       │
│          │          │          │          │          │                  │
│ Ollama   │ Edge-TTS │ SRT gen  │ MoviePy  │  Pillow  │ YouTube API v3   │
│ LLM +    │ (uk-UA)  │Sliding   │  FFmpeg  │ 1280×720 │ unlisted-first   │
│ Template │→ Coqui   │ Window   │  1080p   │ CTR opt  │ AI disclosure ✅  │
│ fallback │ fallback │ align    │  30fps   │          │ Token Bucket 🪣   │
└──────────┴──────────┴──────────┴──────────┴──────────┴──────────────────┘
```

### Структура проєкту

```
YTAIMBot/
├── src/ytaimbot_ml/           # 🧠 ML бібліотека (імпортована)
│   ├── schemas.py             #   Dataclasses: TrendSignal → PipelineResult
│   ├── trend_analyzer.py      #   TruncatedSVD + L2 ranking
│   ├── quality/
│   │   ├── bayes_filter.py    #   Gaussian Naive Bayes gate
│   │   ├── similarity_gate.py #   TF-IDF + Edit Distance (Levenshtein)
│   │   ├── blocklist.py       #   Aho-Corasick multi-pattern
│   │   ├── evidence.py        #   Merkle-like artifact chain
│   │   └── compliance.py      #   Pre-publish checklist
│   ├── content/
│   │   ├── generator.py       #   ScriptGenerator (Hook→Body→CTA)
│   │   ├── template_engine.py #   Cosine similarity template select
│   │   └── templates/         #   tutorial / explainer / shorts / review / listicle
│   ├── seo/
│   │   ├── optimizer.py       #   BFS keyword expansion + PageRank
│   │   └── title_generator.py #   CTR-scoring (weighted sum)
│   ├── feedback/
│   │   ├── scorer.py          #   EMA feedback loop
│   │   ├── ab_tester.py       #   Chi-Square A/B testing
│   │   ├── forecaster.py      #   ARIMA trend forecasting
│   │   └── monte_carlo.py     #   Revenue simulation (10K runs)
│   ├── learner/
│   │   ├── bandit.py          #   UCB1 Multi-Armed Bandit
│   │   ├── drift_detector.py  #   KS-test + Reservoir Sampling
│   │   └── optimizer.py       #   Linear PPO (no GPU needed)
│   └── utils/
│       ├── random.py          #   make_rng(seed) — детермінізм
│       ├── kalman.py          #   Scalar Kalman Filter
│       ├── hyperloglog.py     #   Cardinality estimation
│       └── metrics.py         #   Prometheus metrics registry
│
├── modules/                   # ⚙️ Бекенд (оркестрація, адаптери)
│   ├── orchestrator.py        #   Pipeline (12 стадій, fail-closed)
│   ├── scheduler.py           #   Upload Scheduler (Min-Heap)
│   ├── metrics_collector.py   #   YouTube Analytics API
│   ├── adapters/
│   │   ├── base.py            #   ABCs: TrendSource, TTS, LLM, Publisher
│   │   ├── synthetic.py       #   Тестові in-memory реалізації
│   │   ├── google_trends.py   #   trendspyg RSS → TrendSignal
│   │   ├── youtube_search.py  #   YouTube API v3 + QuotaTracker
│   │   ├── composite.py       #   K-way merge (Priority Queue)
│   │   ├── cache.py           #   LRU Cache + TTL
│   │   ├── retry.py           #   Exponential Backoff + Jitter
│   │   ├── tts_edge.py        #   Edge-TTS (uk-UA-OstapNeural)
│   │   ├── tts_local.py       #   Coqui TTS (offline fallback)
│   │   ├── llm_local.py       #   Ollama HTTP adapter
│   │   ├── youtube_publisher.py # YouTube upload + Token Bucket
│   │   ├── youtube_auth.py    #   OAuth2 + auto-refresh
│   │   └── sqlite_storage.py  #   SQLite persistence (B-Tree indexes)
│   ├── video/
│   │   ├── assembler.py       #   MoviePy + FFmpeg DAG
│   │   ├── thumbnail.py       #   Pillow Layer Stack (1280×720)
│   │   ├── subtitles.py       #   SRT generator (Sliding Window)
│   │   └── ai_generator.py    #   Open-Sora (GPU-gated, optional)
│   ├── dashboard/
│   │   ├── manual_review.py   #   CLI review перших 50 відео
│   │   └── audit_log.py       #   Append-Only JSON Lines
│   ├── notifications/
│   │   └── slack.py           #   Slack alerts + Bloom Filter dedup
│   └── reporting/
│       └── weekly_report.py   #   ASCII charts + ARIMA forecast
│
├── tests/                     # 🧪 Pytest (≥90% coverage)
│   ├── conftest.py            #   Fixtures: seeded rng, synthetic trends
│   ├── e2e/                   #   E2E: 8 сценаріїв з матриці
│   ├── load/                  #   Locust: ≤5хв run, ≤3.5GB RAM
│   ├── test_trend_analyzer.py
│   ├── test_bayes_filter.py
│   ├── test_orchestrator.py
│   └── ...                    #   30+ тест-файлів
│
├── scripts/
│   ├── deploy/                #   Blue-Green deploy, systemd, logrotate
│   ├── backup/                #   GFS backup + AES-256 + S3
│   └── monitoring/            #   Prometheus + Grafana configs
│
├── docs/
│   └── ROADMAP_AI_AGENT_TASKS.md  # 📋 640 задач для AI агентів
│
├── Dockerfile                 # Python 3.11-slim + FFmpeg
├── docker-compose.yml         # Bot + Prometheus + Grafana
└── pyproject.toml             # Python 3.11+, numpy, scikit-learn
```

---

## ☁️ Розгортання у хмарі (VPS)

> Бот працює **повністю в хмарі** — локальний сервер не потрібен.
> **Вартість:** ~$4-6/місяць (Hetzner CX22 або DigitalOcean).
> 📋 [**Повна інструкція →** `docs/DEPLOYMENT_CLOUD_VPS.md`](docs/DEPLOYMENT_CLOUD_VPS.md)

### Коротко: 5 кроків

```bash
# ─── 1. На своєму ПК: генеруємо SSH ключ ───────────────────────────────────
ssh-keygen -t ed25519 -C "ytaimbot" -f ~/.ssh/ytaimbot_vps
# Публічний ключ → вставити у Hetzner/DigitalOcean при створенні сервера

# ─── 2. Підключаємось до VPS ────────────────────────────────────────────────
ssh -i ~/.ssh/ytaimbot_vps root@YOUR_SERVER_IP

# ─── 3. На VPS: встановлюємо Docker ────────────────────────────────────────
curl -fsSL https://get.docker.com | sh && apt-get install -y docker-compose-plugin

# ─── 4. Клонуємо та налаштовуємо ───────────────────────────────────────────
cd /opt && git clone https://github.com/Dmitze/YTAIMBot.git && cd YTAIMBot
cp .env.example .env && nano .env   # ← вставляємо YOUTUBE_API_KEY

# ─── 5. Запускаємо ─────────────────────────────────────────────────────────
mkdir -p /opt/ytaimbot-data
docker compose up -d
docker compose logs -f bot           # перевіряємо що все ОК
```

### Вибір VPS

| Хостинг | Тариф | Ціна | RAM | Примітка |
|---------|-------|------|-----|---------|
| **Hetzner** 🇩🇪 | CX22 | €3.79/міс | 4GB | **Рекомендовано** — найдешевше |
| **Hetzner** 🇩🇪 | CX32 | €5.77/міс | 8GB | Якщо потрібен Ollama (offline LLM) |
| **DigitalOcean** 🌊 | Basic | $6/міс | 1GB | $200 безкоштовних кредитів для нових |
| **DigitalOcean** 🌊 | Basic | $12/міс | 2GB | Для Coqui TTS offline |

### Шпаргалка команд

```bash
docker compose ps                         # статус
docker compose logs -f bot                # логи live
docker compose exec bot python -m modules.orchestrator  # ручний запуск
sqlite3 /opt/ytaimbot-data/ytaimbot.db ".tables"       # переглянути БД
cd /opt/YTAIMBot && git pull && docker compose up -d --build  # оновлення
```

### Локально (тільки розробка)

```bash
git clone https://github.com/Dmitze/YTAIMBot.git && cd YTAIMBot
pip install -e ".[dev]"
pytest -q --tb=short
YTAIMBOT_DRY_RUN=true python -m modules.orchestrator
```

---

## 🔧 Конфігурація

Всі налаштування через змінні середовища — жодних hardcoded значень:

```bash
# .env (ніколи не комітити!)

# === Основні ===
YTAIMBOT_DRY_RUN=true          # false → реальна публікація
YTAIMBOT_SEED=42               # ML детермінізм
YTAIMBOT_DATA_DIR=/app/data    # volume для відео, БД, logs

# === YouTube ===
YOUTUBE_API_KEY=AIza...        # Data API v3 (trends)
YOUTUBE_CLIENT_SECRET_PATH=... # OAuth2 для upload
MAX_UPLOADS_PER_DAY=1          # ліміт публікацій

# === LLM ===
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# === TTS ===
TTS_LANGUAGE=uk                # uk / en / ru
TTS_GENDER=male                # male / female

# === Video ===
VIDEO_RESOLUTION=1920x1080
VIDEO_FPS=30

# === Feedback ===
FEEDBACK_ALPHA=0.3             # EMA learning rate
BANDIT_EXPLORATION_C=2.0       # UCB1 exploration constant
DRIFT_THRESHOLD=0.05           # KS-test p-value threshold

# === Monitoring ===
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
S3_BUCKET=ytaimbot-backups
```

---

## 🧮 Алгоритми + Структури даних

Проєкт використовує **35+ алгоритмів** з Computer Science — кожен обраний з обґрунтуванням:

| Категорія | Алгоритм | Big-O | Де використовується |
|-----------|----------|-------|-------------------|
| **ML** | TruncatedSVD | O(n·d·k) | Зниження розмірності трендів |
| **ML** | Gaussian Naive Bayes | O(features) | Quality gate |
| **ML** | UCB1 Bandit | O(k) | Вибір ніші (exploration/exploitation) |
| **ML** | Linear PPO | O(batch·dim) | Оптимізація параметрів контенту |
| **ML** | ARIMA(1,1,1) | O(n·p²) | Прогноз трендів на тиждень вперед |
| **Статистика** | Kalman Filter | O(1) | Згладжування CTR/RPM шуму |
| **Статистика** | Monte Carlo | O(N·V) | P(revenue ≥ $5K) симуляція |
| **Статистика** | KS-test | O(n log n) | Виявлення distribution drift |
| **Статистика** | Chi-Square | O(1) | A/B тест значимість |
| **Пошук** | Aho-Corasick | O(n+m+z) | Multi-pattern blocklist |
| **Пошук** | BFS | O(V+E) | SEO keyword expansion |
| **Пошук** | PageRank | O(k·E) | Keyword importance graph |
| **Структури** | LRU Cache | O(1) | Trend adapter caching |
| **Структури** | Min-Heap | O(log n) | Upload scheduler |
| **Структури** | Bloom Filter | O(k) | Alert deduplication |
| **Структури** | Merkle Chain | O(n) | Evidence artifact integrity |
| **DP** | Edit Distance | O(n·m) | Plagiarism detection |
| **DP** | Token Budget | O(n·W) | Script section allocation |
| **Greedy** | Token Bucket | O(1) | Rate limiting |
| **Greedy** | Activity Selection | O(n log n) | Upload scheduling |

> 📋 Повна таблиця (40+ алгоритмів) → [`docs/ROADMAP_AI_AGENT_TASKS.md`](docs/ROADMAP_AI_AGENT_TASKS.md)

---

## 📊 Цільові метрики

| Метрика | Мінімум | **Ціль** | Інструмент вимірювання |
|---------|---------|----------|----------------------|
| 💰 Дохід | $1K/міс | **$5K+/міс** | Google AdSense |
| 👆 CTR | ≥ 4% | **≥ 6%** | YouTube Studio |
| 👁️ Retention 30s | ≥ 60% | **≥ 70%** | YouTube Analytics |
| 📹 Відео/день | 1 / 3 дні | **1 / день** | Scheduler logs |
| 🔄 Uptime | ≥ 99% | **≥ 99.9%** | Hetzner monitor |
| ⏱️ Час обробки | ≤ 10 хв | **≤ 5 хв** | Prometheus histogram |
| 🧪 Test coverage | ≥ 80% | **≥ 90%** | `pytest --cov` |
| 🎯 Bayes precision | ≥ 80% | **≥ 95%** | `test_bayes_filter.py` |
| 📉 Build time CI | ≤ 3 хв | **≤ 2 хв** | GitHub Actions |

---

## 🗺️ Прогрес розробки

```
Phase 0  ████████████████████  100% ✅  Foundation (15/15 tasks)
Phase 1  ░░░░░░░░░░░░░░░░░░░░    0% 🔲  Real Trend Adapters
Phase 2  ░░░░░░░░░░░░░░░░░░░░    0% 🔲  Content Generation
Phase 3  ░░░░░░░░░░░░░░░░░░░░    0% 🔲  Video Assembly + SEO
Phase 4  ░░░░░░░░░░░░░░░░░░░░    0% 🔲  Publishing Pipeline
Phase 5  ░░░░░░░░░░░░░░░░░░░░    0% 🔲  Metrics Feedback Loop
Phase 6  ░░░░░░░░░░░░░░░░░░░░    0% 🔲  RL Learner + Bandit
Phase 7  ░░░░░░░░░░░░░░░░░░░░    0% 🔲  Infrastructure + DevOps
Phase 8  ░░░░░░░░░░░░░░░░░░░░    0% 🔲  Security + Compliance
Phase 9  ░░░░░░░░░░░░░░░░░░░░    0% 🔲  Testing + Coverage ≥90%
Phase 10 ░░░░░░░░░░░░░░░░░░░░    0% 🔲  Docs + Launch 🚀

Overall  ███░░░░░░░░░░░░░░░░░    2%    15 / 640 tasks done
```

> 📋 **[Повний roadmap (640 задач) →](docs/ROADMAP_AI_AGENT_TASKS.md)**

---

## 🛡️ Fail-Closed Design

**Публікація НІКОЛИ не виконується без проходження всіх gate:**

```
TrendSignal
    │
    ▼
ScriptGenerator ──▶ [AhoCorasick Blocklist check]
    │                       │ FAIL → block
    ▼                    ───┘
SimilarityGate ──▶ [TF-IDF + Edit Distance < 0.85]
    │                       │ FAIL → block (duplicate)
    ▼                    ───┘
BayesQualityFilter ──▶ [P(bad|features) < threshold]
    │                       │ FAIL → block (low quality)
    ▼                    ───┘
ComplianceChecker ──▶ [AI disclosure + no PII]
    │                       │ FAIL → block
    ▼                    ───┘
ManualReview ──▶ [перші 50 відео: ручне підтвердження]
    │                       │ REJECT → archive
    ▼                    ───┘
YouTubePublisher ← тільки якщо ВСІ gates пройдені ✅
                  + YTAIMBOT_DRY_RUN=false
```

---

## 🧪 Тестування

```bash
# Швидкий запуск всіх тестів
pytest -q --tb=short

# З coverage
pytest --cov=src --cov=modules --cov-report=term-missing

# Один модуль
pytest tests/test_trend_analyzer.py -v

# E2E тести (потрібні всі mock)
pytest tests/e2e/ -v

# Property-based тести (Hypothesis)
pytest tests/ -k "property" -v

# Load тест (Locust)
locust -f tests/load/locustfile.py --headless -u 10 -r 2 --run-time 60s
```

---

## 🚀 Deployment Stack

### Infrastructure (Cloud VPS)

| Компонент | Технологія | Де запускається |
|-----------|-----------|-----------------|
| Runtime | Python 3.11+ | Docker container на VPS |
| ML | NumPy + scikit-learn + statsmodels | В контейнері |
| Video | MoviePy + FFmpeg | В контейнері |
| LLM | Groq API (безкоштовно) або Ollama | Groq cloud / локально в VPS |
| TTS | Edge-TTS (Microsoft, безкоштовно) | HTTP виклик з VPS |
| Storage | SQLite (файл на VPS) | `/opt/ytaimbot-data/ytaimbot.db` |
| Backup | SQLite snapshot → gzip → Cloudflare R2 | Cron щодня 03:00 |
| Container | Docker + docker-compose | VPS |
| Server | **Hetzner CX22** (2vCPU, 4GB, 40GB) | Hetzner Cloud EU |
| Monitoring | Prometheus + Grafana | VPS, порт 3000 |
| CI/CD | GitHub Actions | GitHub |

### Вартість у хмарі

```
Hetzner CX22       €3.79/міс   (~$4.10)
Groq API LLM        $0.00/міс  (14K req/день безкоштовно)
Edge-TTS            $0.00/міс  (безкоштовний Microsoft)
YouTube Data API    $0.00/міс  (10K units/день безкоштовно)
Cloudflare R2       $0.00/міс  (до 10GB backup безкоштовно)
─────────────────────────────────────────
TOTAL:             ~$4-6/міс   (≈ 200 грн/міс)
```

---

## 📚 Документація

| Документ | Опис |
|----------|------|
| [**ROADMAP (640 tasks)**](docs/ROADMAP_AI_AGENT_TASKS.md) | Головний roadmap для AI агентів |
| [Architecture Overview](docs/ARCHITECTURE_OVERVIEW.md) | Системна архітектура |
| [Dataflow](docs/ARCHITECTURE_DATAFLOW.md) | Потік даних через 12 стадій |
| [SRS Requirements](docs/SRS_SYSTEM_REQUIREMENTS.md) | Функціональні вимоги |
| [Design: ML Modules](docs/DESIGN_ML_MODULES.md) | TrendAnalyzer, BayesFilter spec |
| [Design: Storage](docs/DESIGN_STORAGE_SCHEMA.md) | SQLite схема (4 таблиці) |
| [Deployment Guide](docs/DEPLOYMENT_GUIDE_HETZNER_LOCAL_FIRST.md) | Hetzner + Docker setup |
| [Security Guide](docs/SECURITY_ERROR_HANDLING_GUIDE.md) | Secrets + error handling |
| [Risk Register](docs/RISK_REGISTER.md) | R-01 через R-08 |
| [Compliance Checklist](docs/COMPLIANCE_CHECKLIST.md) | YouTube ToS + GDPR |
| [Monetization Guide](docs/MONETIZATION_ANALYTICS_GUIDE.md) | YPP + ROI калькулятор |

---

## 🤖 Для AI Агентів

Якщо ти AI агент що починає роботу над цим проєктом:

```
1. Прочитай docs/ROADMAP_AI_AGENT_TASKS.md — там 640 задач
2. Знайди першу задачу зі статусом 🔲 Pending
3. Перевір що всі залежності ✅ Done
4. Постав статус 🔄 In Progress
5. Виконай задачу (файл → тести → acceptance criteria)
6. Постав статус ✅ Done + дата виконання
7. Перейди до наступної задачі
```

**Правила (обов'язкові):**
- Кожна функція: `docstring` + `type hints` + `Big-O` + `example`
- Тести: ніяких реальних HTTP/API викликів — тільки mock
- ML: завжди `np.random.Generator` як параметр (детермінізм!)
- Publishing: fail-closed — тільки після всіх gate ✅

---

## 📄 Ліцензія

MIT © 2026 Dmitze

---

<div align="center">

**Зроблено з ❤️ та 640 задачами**

*Від ідеї до $5K/місяць — крок за кроком, алгоритм за алгоритмом*

</div>