<div align="center">

# 🤖 YTAIMBot

### Автономний YouTube контент-конвеєр — $0 на AI сервіси

[![CI](https://github.com/Dmitze/YTAIMBot/actions/workflows/ci.yml/badge.svg)](https://github.com/Dmitze/YTAIMBot/actions)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-224%20passed-brightgreen)](https://github.com/Dmitze/YTAIMBot)
[![Roadmap](https://img.shields.io/badge/roadmap-640%20tasks-orange)](docs/ROADMAP_AI_AGENT_TASKS.md)
[![AI Cost](https://img.shields.io/badge/AI%20cost-%240%2Fmonth-blue)](docs/ROADMAP_AI_AGENT_TASKS.md)

**Тренди → Сценарій → Озвучення → Відео → Публікація — повністю автоматично і безкоштовно**

[Стратегія та ніші](#-стратегія-ніші--реалістичний-заробіток) •
[Архітектура](#-архітектура) •
[Швидкий старт](#-швидкий-старт-0) •
[Roadmap](docs/ROADMAP_AI_AGENT_TASKS.md)

</div>

---

## 💡 Головна ідея: автоматизація виграє у масштабі

> Ручне створення AI-відео займає **5–6 годин/день** і приносить $0 за тиждень.
> YTAIMBot робить те саме за **10 хвилин** — і так **кожен день, місяцями**.
> Саме стабільність і масштаб дають гроші — не магія AI.

```
Реальний експеримент (людина вручну):
  7 днів × 5-6 год = 9 відео → 32K переглядів → $0 заробітку

YTAIMBot (автомат):
  Місяць 1–3:   30–90 відео  →  $0–$50    (бот навчається, алгоритм збирає дані)
  Місяць 4–6:   90–180 відео →  $50–$300  (канал зростає, YPP монетизація)
  Місяць 7–9:   180–250 відео → $300–$1K  (UCB1 bandit знайшов найкращу нішу)
  Місяць 10–12: 300–365 відео → $1K–$5K+  (масштаб: 2-3 канали)
```

**Чому автоматизація перемагає конкурентів:**
- Конкуренти роблять 1 відео/день вручну — ти робиш 2 без зусиль
- ML scoring вибирає **топ-5% трендів** замість випадкових тем
- UCB1 Bandit навчається що "заходить" — кожен місяць краще за попередній
- Бот не втомлюється, не хворіє, не пропускає дні

---

## ⚠️ Чесні очікування (без рожевих окулярів)

| Місяць | Відео | Заробіток | Що відбувається |
|--------|-------|-----------|----------------|
| 1–2 | 30–60 | **$0** | Збір даних, бот навчається, нульовий дохід — це нормально |
| 3–4 | 90–120 | **$0–$50** | Перші підписники, алгоритм YouTube помічає канал |
| 5–6 | 150–180 | **$50–$300** | YPP монетизація (1K підп + 4K год перегляду) |
| 7–9 | 200–250 | **$300–$1K** | UCB1 оптимізував нішу, CTR зростає |
| 10–12 | 300–365 | **$1K–$5K+** | Масштаб на 2–3 канали в різних нішах |

> 🚨 **Хто каже "$100/день за тиждень" — продає курси.** Реальний шлях — 6–12 місяців.

---

## 🎯 Стратегія: ніші + реалістичний заробіток

### Формула вибору прибуткової ніші

```
Нішевий score = RPM × (1 / конкуренція) × автоматизованість

RPM (дохід з 1000 переглядів, EN мова):
  Фінанси / інвестиції:   $10–$20  ⬅ найкращий RPM
  Бізнес / підприємництво: $8–$15
  Технології / AI:        $5–$12
  Освіта / наука:         $4–$9
  Психологія / поведінка: $3–$7
  Розваги / horror:       $1–$3   ⬅ найнижчий, але 90% конкурентів тут
```

### 🏆 Топ-10 ніш для YTAIMBot

| # | Ніша | RPM | Конк. AI | Приклади відео | Чому підходить |
|---|------|-----|----------|----------------|----------------|
| 1 | **Фінанси для початківців** | $10–$20 | 🟡 Середня | "5 помилок з кредитами", "Що таке ETF" | Pexels footage є, Groq генерує факти, вічнозелена |
| 2 | **AI та бізнес-автоматизація** | $8–$15 | 🟢 Низька | "Топ AI інструменти 2026", "Як автоматизувати X" | Щодня нові тренди, платоспроможна аудиторія |
| 3 | **Психологія та поведінка** | $5–$10 | 🟡 Середня | "Чому ми відкладаємо", "Dark triad пояснення" | Narration без обличчя, ElevenLabs ідеально |
| 4 | **Космос та наука** | $4–$9 | 🟢 Низька | "Що буде якщо упасти в ЧД", "Факти про Марс" | NASA Public Domain відео/фото, вічнозелена |
| 5 | **Продуктивність та тайм-менеджмент** | $5–$8 | 🟡 Середня | "Pomodoro для програмістів", "Deep Work метод" | Pexels footage, легко скриптувати |
| 6 | **Маловідомі факти про технології** | $5–$12 | 🟢 Низька | "Як Google Пошук насправді працює" | Vічнозелений + технічна аудиторія |
| 7 | **Географія та маловідомі країни** | $3–$6 | 🟢 Дуже низька | "Країни що зникнуть до 2050", "Найменші держави" | Pixabay footage, низька конкуренція |
| 8 | **Мовні факти + лінгвістика** | $4–$7 | 🟢 Низька | "Слова без перекладу", "Неможливі мови" | Унікальна ніша, мало AI конкурентів |
| 9 | **Здоров'я: сон, харчування** | $4–$8 | 🔴 Висока | "Чому 8 год сну не норма", "Coldwater facts" | Велика аудиторія, але ризик YMYL |
| 10 | **Кримінальні розслідування (факти)** | $3–$5 | 🔴 Висока | "Топ нерозкриті злочини" | Конкурентно, але стабільні перегляди |

> ❌ **НЕ рекомендую на старті:** Horror stories, мотивація — перенасичено AI-контентом

### 🚀 Рекомендована стратегія старту

```
КРОК 1 (Місяць 1): Запусти 2 тестові канали паралельно
  Канал A: "Finance Facts" (EN)     — RPM $10–$20, вічнозелений
  Канал B: "AI & Automation" (EN)   — RPM $8–$15, завжди актуальний

  UCB1 Bandit аналізує CTR та retention кожного відео →
  через 60 днів залиш той канал що показує кращі метрики

КРОК 2 (Місяць 2–3): Подвоїти частоту на кращому каналі
  1 відео/день → 2 відео/день
  GitHub Actions: 09:00 UTC + 17:00 UTC cron

КРОК 3 (Місяць 5–6): YPP монетизація
  Ціль: 1 000 підписників + 4 000 год перегляду (або 10M Shorts)
  Shorts стратегія: легше набрати 10M переглядів ніж 4K год

КРОК 4 (Місяць 7+): Масштаб
  Відкрий 3-й канал у найкращій ніші що знайшов UCB1
  Reinvest: перші $50 AdSense → ElevenLabs paid ($5/міс) = краща якість TTS
```

### 💰 Розрахунок потенційного доходу

```
Консервативний (RPM = $5, UA аудиторія):
  6 міс: 180 відео × 1 000 переглядів = 180K/міс → $900/міс
  12 міс: 365 відео × 3 000 переглядів = 1.1M/міс → $5 500/міс

Реалістичний (RPM = $8, EN аудиторія — фінанси):
  6 міс: 180 відео × 2 000 переглядів = 360K/міс → $2 880/міс
  12 міс: 365 відео × 5 000 переглядів = 1.8M/міс → $14 400/міс (оптимістично)

Базовий (якщо все йде погано, RPM = $3):
  12 міс: 365 відео × 1 000 переглядів = 365K/міс → $1 095/міс
```

---

## 💰 Стек безкоштовних сервісів

### LLM — мозок (генерація сценаріїв)

| Сервіс | Безкоштовний ліміт | Пріоритет | Реєстрація |
|--------|-------------------|-----------|-----------|
| **Groq Cloud** | 14 400 req/день, llama-3.1-8b | ⭐ 1-й | [console.groq.com](https://console.groq.com) — без картки |
| **Google Gemini 1.5 Flash** | 1 500 req/день, 1M токенів | ⭐ 2-й | [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| Ollama (self-hosted) | ♾ unlimited | Опційно | Oracle Free Tier ARM VM |

### TTS — озвучення (Chain of Responsibility, авто-перемикання)

| Сервіс | Безкоштовний ліміт | Якість | Пріоритет |
|--------|-------------------|--------|-----------|
| **ElevenLabs** | 10 000 символів/місяць | ⭐⭐⭐⭐⭐ найкраща | 1-й |
| **Gemini TTS** | ~1 000 000 символів/день | ⭐⭐⭐⭐ | 2-й |
| **TTSMaker** | 20 000 символів/тиждень | ⭐⭐⭐ | 3-й |
| **edge-tts** (Microsoft) | ♾ **БЕЗЛІМІТНО** — без ключа | ⭐⭐ (гарантований fallback) | 4-й |

> `FreeTierTTSChain` перевіряє квоту **перед** кожним запитом і
> автоматично переходить на наступний сервіс. Гроші ніколи не списуються.

### Відео — стокові кадри

| Сервіс | Безкоштовний ліміт | Ліцензія |
|--------|-------------------|---------|
| **Pexels API** | 200 req/год, 20 000/міс | Комерційне ✅ |
| **Pixabay API** | 5 000 req/день | Комерційне ✅ |
| **NASA Image Library** | ♾ unlimited | Public Domain ✅ |
| **YouTube Audio Library** | ♾ unlimited | YouTube відео ✅ |

---

## 🏗️ Архітектура

### 12-стадійний конвеєр

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    YTAIMBOT PIPELINE v2.0 — $0 AI                        │
├─────────┬─────────┬──────────┬─────────┬─────────┬───────────────────────┤
│STAGE 1  │STAGE 2  │ STAGE 3  │ STAGE 4 │ STAGE 5 │       STAGE 6         │
│INGEST   │FEATURIZE│  REDUCE  │  SCORE  │  PLAN   │        GATE           │
│Google   │hash  →  │Truncated │L2 norm  │ top-5   │  Bayes + Cosine       │
│Trends + │features │SVD (k=2) │ sorted  │Content  │  P(bad|features)<0.5  │
│YouTube  │         │          │  desc   │  Plans  │  fail-closed ✋        │
├─────────┴─────────┴──────────┴─────────┴─────────┴───────────────────────┤
│STAGE 7  │STAGE 8  │ STAGE 9  │STAGE 10 │STAGE 11 │       STAGE 12        │
│ SCRIPT  │  AUDIO  │SUBTITLES │  VIDEO  │THUMBNAIL│       PUBLISH         │
│Groq(1)  │ElevenLab│ SRT gen  │ MoviePy │ Pillow  │  YouTube API v3       │
│Gemini(2)│GeminiTTS│Sliding   │  +Pexels│ 1280×720│  unlisted → public    │
│Ollama(3)│TTSMaker │ Window   │ 1080p   │ CTR opt │  AI disclosure ✅      │
│         │edge-tts │ align    │  30fps  │         │  Token Bucket 🪣       │
│         │  (∞!)   │          │         │         │                       │
└─────────┴─────────┴──────────┴─────────┴─────────┴───────────────────────┘
  ⚡ ServiceQuotaTracker (data/quota.db) захищає стадії 7, 8, 12 від перевитрати
  🧠 UCB1 Bandit (Stage 4) постійно навчається яка ніша дає кращий CTR
```

### Структура проєкту

```
YTAIMBot/
├── src/ytaimbot_ml/               # 🧠 ML бібліотека (чиста логіка, без I/O)
│   ├── schemas.py                 #   Dataclasses: TrendSignal → PipelineResult
│   ├── trend_analyzer.py          #   TruncatedSVD(k=2) + L2 ranking
│   ├── quality/bayes_filter.py    #   Gaussian NB gate: P(bad|x) < 0.5
│   ├── quota/service_tracker.py   #   SQLite квота-трекер (7 free-tier сервісів)
│   └── utils/random.py            #   make_rng(seed) — детермінізм
│
├── modules/                       # ⚙️ Pipeline + адаптери (I/O шар)
│   ├── orchestrator.py            #   12-стадійний Pipeline (fail-closed)
│   └── adapters/
│       ├── llm/                   #   ✅ Groq → Gemini → Ollama (optional)
│       ├── tts/                   #   ✅ ElevenLabs → GeminiTTS → TTSMaker → edge-tts
│       ├── video/                 #   ✅ Pexels + Pixabay + MoviePy
│       ├── publisher/             #   ✅ YouTube OAuth2 + QuotaGuard Token Bucket
│       └── analytics/             #   ✅ YouTubeAnalytics + EMA smoothing
│
└── tests/                         # 🧪 224 passed, 17 skipped
```

---

## 🚀 Швидкий старт ($0)

### Крок 1 — Отримай безкоштовні ключі (10 хвилин)

```bash
# 1. Groq API (14 400 req/день, llama-3.1-8b)
#    → console.groq.com → "Create API Key" (без картки!)

# 2. Google AI Studio (1 500 req/день LLM + 1M chars/день TTS)
#    → aistudio.google.com/app/apikey (один ключ для LLM і TTS!)

# 3. Pexels API (стокові відео)
#    → pexels.com/api → "Your API Key" (без картки!)

# 4. ElevenLabs (кращий TTS голос, 10 000 символів/місяць)
#    → elevenlabs.io → Free account (без картки!)

# 5. YouTube API (тренди + публікація)
#    → console.cloud.google.com → YouTube Data API v3
```

### Крок 2 — Запуск

```bash
git clone https://github.com/Dmitze/YTAIMBot.git && cd YTAIMBot
pip install -e ".[dev]"
cp .env.example .env   # заповни ключі

# Перевірка (224 тести, без реальних API викликів)
pytest -q --tb=short

# Dry-run (тренди + скрипт + аудіо, БЕЗ публікації на YouTube)
YTAIMBOT_DRY_RUN=true python -m modules.orchestrator
```

### Крок 3 — Деплой на GitHub Actions ($0/міс)

```bash
# GitHub Actions FREE: 2 000 хвилин/місяць
# Pipeline ~5 хвилин → достатньо для 2 відео/день!

# 1. Додай секрети: GitHub → Settings → Secrets → Actions
#    GROQ_API_KEY, GEMINI_API_KEY, ELEVENLABS_API_KEY,
#    PEXELS_API_KEY, YOUTUBE_API_KEY, YOUTUBE_OAUTH_TOKEN_JSON

# 2. Встанови YTAIMBOT_DRY_RUN=false в secrets

# Pipeline запускається автоматично щодня о 09:00 та 17:00 UTC
```

---

## ☁️ Варіанти хостингу

| Платформа | Вартість | RAM | Для чого |
|-----------|----------|-----|----------|
| **GitHub Actions** ⭐ | **$0/міс** | 7GB | Старт — 2 відео/день cron |
| **Oracle Cloud Free** 🆓 | **$0 назавжди** | 24GB ARM | Ollama self-hosted LLM |
| **Railway.app** | $0–5/міс | 512MB | Dev/test |
| **Hetzner CX22** | €3.79/міс | 4GB | Production (після MonetizatION) |

> 💡 **Стратегія:** GitHub Actions до перших $50 AdSense → потім Hetzner.

---

## 🔧 Конфігурація

```bash
# .env — НІКОЛИ не комітити!

# LLM (обидва безкоштовні — авто-перемикання)
GROQ_API_KEY=gsk_...             # console.groq.com (primary, 14 400/day)
GEMINI_API_KEY=AIza...           # aistudio.google.com (backup, 1 500/day)

# TTS Chain (авто-перемикання при вичерпанні квоти)
ELEVENLABS_API_KEY=...           # 10k символів/місяць (найкращий голос)
TTSMAKER_API_TOKEN=...           # 20k символів/тиждень
# edge-tts: ключ не потрібен! (∞ безлімітно)

# Відео (стоки)
PEXELS_API_KEY=...               # 200 req/год (primary)
PIXABAY_API_KEY=...              # 5 000 req/день (backup)

# YouTube
YOUTUBE_API_KEY=AIza...          # тренди (безкоштовно)
YOUTUBE_CLIENT_SECRET_PATH=data/client_secret.json

# Pipeline
YTAIMBOT_DRY_RUN=true           # false = реальна публікація
YTAIMBOT_SEED=42                 # ML детермінізм
MAX_UPLOADS_PER_DAY=2            # 2 відео/день (GitHub Actions)
SCRIPT_LANGUAGE=en               # EN для вищого RPM!
NICHE=finance                    # finance | tech | science | psychology
```

---

## 🧮 Алгоритми + Структури даних

| Категорія | Алгоритм | Big-O | Де використовується |
|-----------|----------|-------|-------------------|
| **ML** | TruncatedSVD | O(n·d·k) | Зниження розмірності трендів |
| **ML** | Gaussian Naive Bayes | O(features) | Quality gate |
| **ML** | UCB1 Bandit | O(k) | Вибір ніші — exploration vs exploitation |
| **ML** | EMA | O(1) | Згладжування CTR/RPM між відео |
| **Статистика** | Monte Carlo | O(N·V) | Симуляція P(revenue ≥ $5K) |
| **Пошук** | Aho-Corasick | O(n+m+z) | Multi-pattern blocklist перевірка |
| **Структури** | LRU Cache | O(1) | Trend adapter caching |
| **Структури** | Token Bucket | O(1) | Upload rate limiting |
| **Структури** | Sliding Window | O(1) | Free-tier quota tracking |
| **Ланцюг** | Chain of Responsibility | O(k) | TTS / LLM fallback chain |
| **DP** | Proportional Knapsack | O(n) | Token budget між секціями скрипту |

---

## 📊 Цільові метрики

| Метрика | Міс 1–3 | Міс 4–6 | Ціль (міс 12) |
|---------|---------|---------|--------------|
| 💰 Дохід | $0 | $50–$300 | **$1K–$5K+/міс** |
| 👆 CTR | ≥ 3% | ≥ 4% | **≥ 6%** |
| 👁️ Retention 30s | ≥ 50% | ≥ 60% | **≥ 70%** |
| 📹 Відео/день | 1/3 дні | 1/день | **2/день** |
| 💲 AI cost | $0 | $0 | **$0** (free-tier) |
| 🧪 Tests | 224 | ≥250 | **≥90% coverage** |

---

## 🛡️ Fail-Closed Design

```
TrendSignal
    │
    ▼
ScriptGenerator ──▶ [AhoCorasick Blocklist]        FAIL → block
    │
    ▼
SimilarityGate ──▶ [TF-IDF + Edit Distance < 0.85] FAIL → block (duplicate)
    │
    ▼
BayesQualityFilter ──▶ [P(bad|features) < 0.5]    FAIL → block (low quality)
    │
    ▼
ComplianceChecker ──▶ [AI disclosure + YouTube ToS] FAIL → block
    │
    ▼
YouTubePublisher ← ТІЛЬКИ якщо ВСІ gates ✅ + YTAIMBOT_DRY_RUN=false
```

---

## 🗺️ Прогрес розробки

```
Phase 0  ████████████████████  100% ✅  Foundation (15 tasks)
Phase 1  ████████████████████  100% ✅  Real Trend Adapters (Google + YouTube)
Phase 2  ████████████████████  100% ✅  Content Generation (Groq LLM + FreeTierTTS)
Phase 3  ████████████████████  100% ✅  SEO Optimizer + Thumbnail Generator
Phase 4  ████████████████████  100% ✅  Video Assembly (MoviePy + SRT + Pillow)
Phase 5  ████████████░░░░░░░░   60% 🔄  Free-Tier Cloud Stack (YouTube Upload)
Phase 6  ░░░░░░░░░░░░░░░░░░░░    0% 🔲  Metrics Feedback + EMA Tracker
Phase 7  ░░░░░░░░░░░░░░░░░░░░    0% 🔲  UCB1 Bandit + Niche Optimizer
Phase 8  ░░░░░░░░░░░░░░░░░░░░    0% 🔲  Infrastructure + GitHub Actions cron
Phase 9  ░░░░░░░░░░░░░░░░░░░░    0% 🔲  Security + YouTube ToS Compliance
Phase 10 ░░░░░░░░░░░░░░░░░░░░    0% 🔲  Testing + Coverage ≥90%

Tests    ████████████████░░░░   83%    224 passed, 17 skipped ✅
```

---

## 🧪 Тестування

```bash
pytest -q --tb=short                               # 224 passed
pytest --cov=src --cov=modules --cov-report=term-missing  # coverage
pytest tests/unit/test_free_tier_stack.py -v       # free-tier stack tests
```

---

## 📚 Документація

| Документ | Опис |
|----------|------|
| [**ROADMAP (640 tasks)**](docs/ROADMAP_AI_AGENT_TASKS.md) | Roadmap + стратегія ніш + бізнес-плани |
| [Architecture Overview](docs/ARCHITECTURE_OVERVIEW.md) | Системна архітектура |
| [Deployment Guide](docs/DEPLOYMENT_CLOUD_VPS.md) | GitHub Actions + Oracle Free + Hetzner |
| [AI Agent Start](docs/AI_AGENT_START_PROMPT_2026.md) | Онбординг для AI агентів |

---

## 🤖 Для AI Агентів

```
1. Прочитай docs/ROADMAP_AI_AGENT_TASKS.md — там всі правила і задачі
2. RULE-11: сервіси з free-tier дозволені, ServiceQuotaTracker ОБОВ'ЯЗКОВИЙ
3. RULE-12: LLM primary = Groq API (не Ollama, не локально!)
4. RULE-13: check_available() перед КОЖНИМ зовнішнім API викликом
5. Знайди 🔲 Pending → постав 🔄 In Progress → виконай → ✅ Done
```

---

<div align="center">

**Зроблено з ❤️, $0 бюджетом на AI та 224 тестами**

*Перші 3 місяці — $0. Місяць 6 — перші гроші. Місяць 12 — $1K–$5K+*

*Не магія. Просто: правильна ніша + автоматизація + час.*

</div>
