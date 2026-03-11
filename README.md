<div align="center">

# 🤖 YTAIMBot

### Автономний YouTube контент-конвеєр — $0 на AI сервіси

[![CI](https://github.com/Dmitze/YTAIMBot/actions/workflows/ci.yml/badge.svg)](https://github.com/Dmitze/YTAIMBot/actions)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Coverage](https://img.shields.io/badge/coverage-80%25-yellowgreen)](https://github.com/Dmitze/YTAIMBot)
[![Tasks](https://img.shields.io/badge/roadmap-640%20tasks-orange)](docs/ROADMAP_AI_AGENT_TASKS.md)
[![Target](https://img.shields.io/badge/target-%245K%2B%2Fmonth-brightgreen)](docs/MONETIZATION_ANALYTICS_GUIDE.md)
[![Cost](https://img.shields.io/badge/AI%20cost-%240%2Fmonth-blue)](docs/ROADMAP_AI_AGENT_TASKS.md)

**Тренди → Сценарій → Озвучення → Відео → Публікація — повністю автоматично і безкоштовно**

[Roadmap (640 задач)](docs/ROADMAP_AI_AGENT_TASKS.md) •
[Архітектура](#-архітектура) •
[Безкоштовний старт](#-швидкий-старт-0) •
[Алгоритми](#-алгоритми--структури-даних) •
[Метрики](#-цільові-метрики)

</div>

---

## 💡 Концепція: $0 на AI

> **Головне правило:** Всі AI-сервіси — тільки безкоштовні тарифи. Платимо тільки за хостинг — і тільки тоді, коли канал вже заробляє.

```
Ваш гаманець:  $0 на AI   →  Groq (free) + edge-tts (безлімітно) + Pexels (free)
Хостинг:       $0 старт   →  GitHub Actions (free 2000 хв/місяць)
               $4/міс     →  тільки коли канал вже монетизований
```

---

## 🎯 Що робить бот

**YTAIMBot** — повністю автономний конвеєр що:

1. 🔍 **Знаходить** трендові теми (Google Trends + YouTube API — обидва **безкоштовні**)
2. ✍️ **Генерує** відеосценарій (Groq llama-3.1 **безкоштовно** → Gemini Flash **безкоштовно**)
3. 🔊 **Озвучує** текст (edge-tts **∞ безлімітно** → ElevenLabs → TTSMaker — всі **безкоштовні**)
4. 🎬 **Монтує** відео (MoviePy + Pexels стокові кадри — **безкоштовно**)
5. 🖼️ **Генерує** thumbnail (Pillow, 1280×720, CTR-оптимізований — **безкоштовно**)
6. 🛡️ **Перевіряє** якість (Bayesian gate + Cosine Similarity + Compliance)
7. 📤 **Публікує** на YouTube (OAuth2, unlisted-first, AI disclosure)
8. 📈 **Навчається** з метрик (EMA feedback → UCB1 Bandit → краще наступного разу)

**Ціль:** $5 000+/місяць пасивного доходу від AdSense на автопілоті.

---

## 💰 Стек безкоштовних сервісів

### LLM (мозок — генерація тексту)

| Сервіс | Безкоштовний ліміт | Реєстрація | Рекомендація |
|--------|-------------------|-----------|-------------|
| **Groq Cloud** | 14 400 запитів/день | [console.groq.com](https://console.groq.com) ✅ без картки | ⭐ Головний |
| **Google Gemini 1.5 Flash** | 1 500 запитів/день | [aistudio.google.com](https://aistudio.google.com/app/apikey) ✅ | ⭐ Резерв |
| Ollama (self-hosted) | ♾ unlimited | Oracle Free Tier ARM VM | Опціонально |

### TTS (озвучення — авто-перемикання при вичерпанні)

| Сервіс | Безкоштовний ліміт | Ключ потрібен? | Якість |
|--------|-------------------|--------------|--------|
| **edge-tts** | ♾ **БЕЗЛІМІТНО** | ❌ Ні | ⭐⭐⭐⭐ |
| **ElevenLabs** | 10 000 символів/місяць | ✅ [elevenlabs.io](https://elevenlabs.io) | ⭐⭐⭐⭐⭐ |
| **Gemini TTS** | ~1 000 000 символів/день | ✅ той самий GEMINI_API_KEY | ⭐⭐⭐⭐ |
| **TTSMaker** | 20 000 символів/тиждень | ✅ [ttsmaker.com](https://ttsmaker.com) | ⭐⭐⭐ |

> 💡 **Логіка**: бот автоматично перевіряє залишок квоти і перемикається на наступний сервіс. edge-tts завжди останній в ланцюгу як необмежений fallback.

### Відео (стокові кадри — без AI відео-генерації)

| Сервіс | Безкоштовний ліміт | Ліцензія |
|--------|-------------------|---------|
| **Pexels API** | 200 запитів/год, 20 000/міс | Комерційне ✅, без атрибуції |
| **Pixabay API** | 5 000 запитів/день | Комерційне ✅, без атрибуції |
| **YouTube Audio Library** | ♾ unlimited | Для YouTube відео ✅ |

> 🎥 **Чому не CapCut/Kling/Veo?** Їх безкоштовні tier не мають публічного API — тільки веб-інтерфейс. Наш бот використовує Pexels stock footage + MoviePy для автоматичного монтажу, що набагато надійніше для автоматизації.

---

## 🏗️ Архітектура

### 12-стадійний конвеєр

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     YTAIMBOT PIPELINE v2.0 — $0 AI                      │
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
│ Groq     │ edge-tts │ SRT gen  │ MoviePy  │  Pillow  │ YouTube API v3   │
│ (free)→  │(unlimited│Sliding   │  +Pexels │ 1280×720 │ unlisted-first   │
│ Gemini   │ fallback)│ Window   │  stock   │ CTR opt  │ AI disclosure ✅  │
│ (free)   │→ElevenLab│ align    │  1080p   │          │ Token Bucket 🪣   │
│          │→TTSMaker │          │  30fps   │          │                  │
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
│   │   └── similarity_gate.py #   TF-IDF + Edit Distance
│   ├── content/
│   │   ├── script_generator.py #  ScriptGenerator (Hook→Body→CTA)
│   │   └── token_budget.py    #   Proportional token allocation
│   ├── seo/
│   │   ├── title_optimizer.py #   CTR-scoring (12 шаблонів)
│   │   └── thumbnail_scorer.py #  Pillow Weber contrast + Sobel
│   ├── quota/
│   │   └── service_tracker.py #   SQLite квота-трекер (всі free-tier сервіси)
│   └── utils/
│       └── random.py          #   make_rng(seed) — детермінізм
│
├── modules/                   # ⚙️ Бекенд (оркестрація, адаптери)
│   ├── orchestrator.py        #   Pipeline (12 стадій, fail-closed)
│   └── adapters/
│       ├── base.py            #   ABCs: TrendSource, TTS, LLM, Publisher
│       ├── llm/
│       │   ├── groq.py        #   ✅ Groq Cloud (14 400 req/day FREE)
│       │   ├── gemini.py      #   ✅ Google Gemini (1 500 req/day FREE)
│       │   └── ollama.py      #   Optional: self-hosted Ollama
│       ├── tts/
│       │   ├── edge_tts.py    #   ✅ edge-tts (UNLIMITED, no key)
│       │   ├── elevenlabs.py  #   ✅ ElevenLabs (10k chars/month FREE)
│       │   ├── gemini_tts.py  #   ✅ Gemini TTS (1M chars/day FREE)
│       │   ├── ttsmaker.py    #   ✅ TTSMaker (20k chars/week FREE)
│       │   └── free_tier_chain.py # ✅ Auto-switch chain
│       ├── video/
│       │   ├── assembler.py   #   MoviePy + FFmpeg assembly
│       │   ├── pexels.py      #   ✅ Pexels + Pixabay stock footage
│       │   ├── thumbnail.py   #   Pillow thumbnail generator
│       │   └── subtitle.py    #   SRT subtitle generator
│       └── publisher/
│           ├── youtube_upload.py  # YouTube Data API v3 (OAuth2)
│           └── quota_guard.py     # Token Bucket (6 uploads/day max)
│
└── tests/                     # 🧪 Pytest (190+ passing)
```

---

## 🚀 Швидкий старт ($0)

### Крок 1 — Отримай безкоштовні ключі (5 хвилин)

```bash
# 1. Groq API (головний LLM) — 14 400 запитів/день FREE
#    → Зайди на console.groq.com → "Create API Key"
#    → Без кредитної картки!

# 2. Google AI Studio (резервний LLM + TTS) — FREE
#    → aistudio.google.com/app/apikey → "Create API key"
#    → Той самий ключ для LLM і TTS!

# 3. Pexels API (стокові відео) — FREE
#    → pexels.com/api → "Your API Key"
#    → Без кредитної картки!

# 4. YouTube API (тренди + публікація) — FREE
#    → console.cloud.google.com → APIs & Services → YouTube Data API v3
```

### Крок 2 — Запуск локально

```bash
git clone https://github.com/Dmitze/YTAIMBot.git && cd YTAIMBot
pip install -e ".[dev]"
cp .env.example .env

# Заповни ключі в .env:
# GROQ_API_KEY=gsk_...
# GEMINI_API_KEY=AIza...
# PEXELS_API_KEY=...

# Тест (без реальних API викликів)
pytest -q --tb=short

# Запуск pipeline (dry-run)
YTAIMBOT_DRY_RUN=true python -m modules.orchestrator
```

### Крок 3 — Деплой (GitHub Actions — теж безкоштовно!)

```bash
# GitHub Actions FREE: 2 000 хвилин/місяць
# Достатньо для 1-2 відео/день з 5-хвилинним pipeline!

# Додай секрети в GitHub: Settings → Secrets → Actions
# GROQ_API_KEY, GEMINI_API_KEY, PEXELS_API_KEY,
# YOUTUBE_API_KEY, YOUTUBE_OAUTH_TOKEN_JSON

# Pipeline запускається автоматично щодня в 09:00 UTC
# .github/workflows/daily_pipeline.yml
```

---

## ☁️ Варіанти хостингу

| Платформа | Вартість | RAM | Підходить для |
|-----------|----------|-----|-------------|
| **GitHub Actions** ⭐ | **$0/міс** (2000 хв/міс) | 7GB | Старт — 1-2 відео/день |
| **Oracle Cloud Free** 🆓 | **$0 назавжди** | 24GB ARM | Ollama + повний pipeline |
| **Render.com Free** | $0 (750 год/міс) | 512MB | Тільки API сервер |
| **Railway.app** | ~$0-5/міс | 512MB | Dev/test |
| **Hetzner CX22** | €3.79/міс | 4GB | Production (після монетизації) |

> 💡 **Рекомендована стратегія:** Починай з GitHub Actions ($0). Коли канал заробляє $20+/міс — переходь на Oracle Free Tier або Hetzner CX22.

---

## 🔧 Конфігурація

Всі налаштування через змінні середовища — жодних hardcoded значень:

```bash
# .env (ніколи не комітити!)

# === LLM — мозок (обидва безкоштовні) ===
GROQ_API_KEY=gsk_...           # console.groq.com (рекомендовано)
GEMINI_API_KEY=AIza...         # aistudio.google.com (резерв)

# === TTS — озвучення ===
TTS_VOICE=uk-UA-OstapNeural   # edge-tts — безлімітно і безкоштовно
ELEVENLABS_API_KEY=...         # +якість (10k симв/міс free)
TTSMAKER_API_TOKEN=...         # +резерв (20k симв/тиждень free)

# === Відео ===
PEXELS_API_KEY=...             # стокові кадри (free)
PIXABAY_API_KEY=...            # стокові кадри backup (free)

# === YouTube ===
YOUTUBE_API_KEY=AIza...        # тренди (free)
YOUTUBE_CLIENT_SECRET_PATH=data/client_secret.json  # публікація

# === Pipeline ===
YTAIMBOT_DRY_RUN=true         # false = реальна публікація
YTAIMBOT_SEED=42               # ML детермінізм
MAX_UPLOADS_PER_DAY=1          # ліміт публікацій
SCRIPT_LANGUAGE=uk             # мова відео
```

---

## 🧮 Алгоритми + Структури даних

Проєкт використовує **35+ алгоритмів** з Computer Science:

| Категорія | Алгоритм | Big-O | Де використовується |
|-----------|----------|-------|-------------------|
| **ML** | TruncatedSVD | O(n·d·k) | Зниження розмірності трендів |
| **ML** | Gaussian Naive Bayes | O(features) | Quality gate |
| **ML** | UCB1 Bandit | O(k) | Вибір ніші (exploration/exploitation) |
| **ML** | ARIMA(1,1,1) | O(n·p²) | Прогноз трендів на тиждень вперед |
| **Статистика** | Kalman Filter | O(1) | Згладжування CTR/RPM шуму |
| **Статистика** | EMA | O(1) | Smooth analytics, TTS quota |
| **Статистика** | Monte Carlo | O(N·V) | P(revenue ≥ $5K) симуляція |
| **Пошук** | Aho-Corasick | O(n+m+z) | Multi-pattern blocklist |
| **Пошук** | BFS | O(V+E) | SEO keyword expansion |
| **Структури** | LRU Cache | O(1) | Trend adapter caching |
| **Структури** | Token Bucket | O(1) | Upload rate limiting |
| **Структури** | Sliding Window | O(1) | Free-tier quota tracking |
| **Ланцюг** | Chain of Responsibility | O(n) | TTS fallback chain |
| **DP** | Edit Distance | O(n·m) | Plagiarism detection |

---

## 📊 Цільові метрики

| Метрика | Мінімум | **Ціль** | Інструмент вимірювання |
|---------|---------|----------|----------------------|
| 💰 Дохід | $1K/міс | **$5K+/міс** | Google AdSense |
| 👆 CTR | ≥ 4% | **≥ 6%** | YouTube Studio |
| 👁️ Retention 30s | ≥ 60% | **≥ 70%** | YouTube Analytics |
| 📹 Відео/день | 1 / 3 дні | **1 / день** | Scheduler logs |
| 🔄 Uptime | ≥ 99% | **≥ 99.9%** | GitHub Actions |
| 💲 AI cost | — | **$0/міс** | Free-tier only |
| 🧪 Test coverage | ≥ 80% | **≥ 90%** | `pytest --cov` |

---

## 🗺️ Прогрес розробки

```
Phase 0  ████████████████████  100% ✅  Foundation (15/15 tasks)
Phase 1  ████████████████████  100% ✅  Real Trend Adapters
Phase 2  ████████████████████  100% ✅  Content Generation (LLM + TTS)
Phase 3  ████████████████████  100% ✅  SEO (TitleOptimizer + ThumbnailScorer)
Phase 4  ████████████████████  100% ✅  Video Assembly + Publishing
Phase 5  ████░░░░░░░░░░░░░░░░   20% 🔄  Free-Tier Stack (QuotaGuard + YouTube Upload)
Phase 6  ░░░░░░░░░░░░░░░░░░░░    0% 🔲  Metrics Feedback Loop + EMA
Phase 7  ░░░░░░░░░░░░░░░░░░░░    0% 🔲  RL Learner + UCB1 Bandit
Phase 8  ░░░░░░░░░░░░░░░░░░░░    0% 🔲  Infrastructure + DevOps
Phase 9  ░░░░░░░░░░░░░░░░░░░░    0% 🔲  Security + Compliance
Phase 10 ░░░░░░░░░░░░░░░░░░░░    0% 🔲  Testing + Coverage ≥90%

Tests    ████████████████░░░░   83%    190 passed, 17 skipped
```

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
```

---

## 📚 Документація

| Документ | Опис |
|----------|------|
| [**ROADMAP (640 tasks)**](docs/ROADMAP_AI_AGENT_TASKS.md) | Головний roadmap для AI агентів |
| [Architecture Overview](docs/ARCHITECTURE_OVERVIEW.md) | Системна архітектура |
| [Deployment Guide](docs/DEPLOYMENT_CLOUD_VPS.md) | GitHub Actions + Oracle Free + Hetzner |
| [Monetization Guide](docs/MONETIZATION_ANALYTICS_GUIDE.md) | YPP + ROI калькулятор |
| [Security Guide](docs/SECURITY_ERROR_HANDLING_GUIDE.md) | Secrets + error handling |
| [Compliance Checklist](docs/COMPLIANCE_CHECKLIST.md) | YouTube ToS + GDPR |

---

## 🤖 Для AI Агентів

Якщо ти AI агент що починає роботу над цим проєктом:

```
1. Прочитай docs/ROADMAP_AI_AGENT_TASKS.md — там 640 задач
2. ВАЖЛИВО: Всі AI-сервіси — ТІЛЬКИ безкоштовні тарифи!
3. Знайди першу задачу зі статусом 🔲 Pending
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
- **AI services: ONLY free tiers — ніяких платних API!**

---

## 📄 Ліцензія

MIT © 2026 Dmitze

---

<div align="center">

**Зроблено з ❤️ та $0 бюджетом на AI**

*Від ідеї до $5K/місяць — крок за кроком, алгоритм за алгоритмом*

</div>