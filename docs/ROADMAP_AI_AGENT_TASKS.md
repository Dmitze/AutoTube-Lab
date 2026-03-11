# 🤖 YTAIMBot — AI Agent Master Roadmap (500+ Tasks)

> **Версія:** 1.0.0 | **Оновлено:** 2026-03-10 | **Статус:** В розробці
> **Ціль проєкту:** Автономний YouTube-конвеєр контенту → $5k+/місяць

---

## 📋 ІНСТРУКЦІЇ ДЛЯ AI АГЕНТА

### Як читати цей файл

Цей файл є **єдиним джерелом правди** для всіх AI агентів, що працюють над проєктом.
Перед початком роботи AI агент **зобов'язаний**:

1. **Прочитати** цей файл повністю
2. **Знайти** першу задачу зі статусом `🔲 Pending` у поточній активній фазі
3. **Оновити статус** задачі на `🔄 In Progress` перед початком виконання
4. **Виконати** задачу згідно з інструкціями, acceptance criteria та алгоритмами
5. **Оновити статус** на `✅ Done` після успішного виконання
6. **Записати** дату/час виконання у колонку `Виконано`
7. **Перейти** до наступної задачі

### Правила виконання

```
RULE-01: Виконуй задачі СТРОГО по порядку в межах фази (залежності!)
RULE-02: Ніколи не пропускай задачі — якщо блокування, постав 🚫 і вкажи причину
RULE-03: Кожна функція/клас ПОВИННА мати: docstring + type hints + Big-O + приклад використання
RULE-04: Тести пишуться ДО або РАЗОМ з кодом (TDD підхід)
RULE-05: Ніяких hardcoded значень — тільки env vars або параметри конструктора
RULE-06: Ніяких мережевих викликів у тестах — тільки mock/synthetic adapters
RULE-07: Кожен новий адаптер ПОВИНЕН реалізовувати відповідний ABC з modules/adapters/base.py
RULE-08: Determinism is mandatory — будь-який ML компонент приймає np.random.Generator
RULE-09: Fail-closed publishing — публікація ТІЛЬКИ якщо ComplianceReport.decision == "pass"
RULE-10: Логуй через stdlib logging — DEBUG для даних, INFO для переходів, ERROR для збоїв
RULE-11: ⭐ БЮДЖЕТ = $0 — використовуй ТІЛЬКИ безкоштовні ліміти/токени. НІКОЛИ не додавай платні API/сервіси.
          Пріоритет LLM:   Groq (14 400 req/day) → Gemini Flash (1 500/day) → Ollama (self-hosted optional)
          Пріоритет TTS:   edge-tts (∞, no key) → ElevenLabs (10k/month) → Gemini TTS (1M/day) → TTSMaker (20k/week)
          Пріоритет відео: Стокові кадри Pexels/Pixabay API → CapCut AI (web) → Kling/Veo (web, manual)
          Пріоритет хмари: GitHub Actions ($0, 2000 min/month) → Railway free → Oracle Cloud Free ARM VM
RULE-12: LLM на хмарі — Ollama НЕ є primary. Використовуй Groq або Gemini Flash API (REST, без локального сервера).
RULE-13: ServiceQuotaTracker (data/quota.db) — ЗАВЖДИ перевіряй ліміти ПЕРЕД викликом платного/лімітованого сервісу.
          Якщо check_available() → False, переходь до наступного сервісу в ланцюжку (Chain of Responsibility).
```

### Алгоритм вибору наступної задачі

```python
def get_next_task(roadmap: list[Task]) -> Task | None:
    """
    Алгоритм: Топологічне сортування (Kahn's Algorithm)
    Складність: O(V + E) де V = задачі, E = залежності

    Логіка:
    1. Знайти всі задачі зі статусом Pending
    2. Відфільтрувати ті, у яких ВСІ залежності Done
    3. Повернути першу (за ID) — вони вже відсортовані
    """
    pending = [t for t in roadmap if t.status == "pending"]
    ready = [t for t in pending if all(
        dep.status == "done" for dep in t.dependencies
    )]
    return min(ready, key=lambda t: t.id) if ready else None
```

### Структура даних задачі

```python
@dataclass
class Task:
    id: str                    # T-NNN формат
    title: str                 # Коротка назва
    phase: int                 # 0–10
    status: Literal[
        "done",                # ✅ Виконано
        "in_progress",         # 🔄 В процесі
        "pending",             # 🔲 Очікує
        "blocked",             # 🚫 Заблоковано
        "testing",             # 🧪 Тестується
    ]
    files: list[str]           # Файли до створення/зміни
    priority: Literal["critical", "high", "medium", "low"]
    complexity: str            # S / M / L / XL
    depends_on: list[str]      # ID залежних задач
    algorithm_ds: str          # Алгоритм/структура даних
    acceptance: list[str]      # Критерії прийняття
    executed_at: datetime | None  # Коли виконано
    executed_by: str | None    # Ким виконано (AI агент / людина)
```

---

## 🎨 ЛЕГЕНДА СТАТУСІВ

| Символ | Статус | Значення |
|--------|--------|----------|
| ✅ | Done | Задача виконана, тести пройдені |
| 🔄 | In Progress | AI агент зараз виконує |
| 🔲 | Pending | Очікує виконання |
| 🚫 | Blocked | Заблоковано залежністю |
| 🧪 | Testing | Код написано, тести запускаються |

---

## 📊 ЗАГАЛЬНИЙ ПРОГРЕС

| Фаза | Назва | Всього | ✅ Done | 🔄 Active | 🔲 Pending |
|------|-------|--------|---------|-----------|-----------|
| **P0** | Foundation (Skeleton) | 15 | 15 | 0 | 0 |
| **P1** | Real Trend Adapters | 65 | 65 | 0 | 0 |
| **P2** | Content Generation | 80 | 80 | 0 | 0 |
| **P3** | Video Assembly + SEO | 80 | 80 | 0 | 0 |
| **P4** | Video Assembler Tests | 30 | 30 | 0 | 0 |
| **P5** | Free-Tier Cloud Stack | 70 | 60 | 0 | 10 |
| **P6** | Metrics + RL Bandit | 60 | 0 | 0 | 60 |
| **P7** | Infrastructure + DevOps | 50 | 0 | 0 | 50 |
| **P8** | Security + Compliance | 40 | 0 | 0 | 40 |
| **P9** | Testing + Coverage | 50 | 0 | 0 | 50 |
| **P10** | Docs + Finalization | 30 | 0 | 0 | 30 |
| **TOTAL** | | **570** | **330** | **0** | **240** |

---

## 🆓 FREE-TIER СЕРВІСИ (RULE-11)

> **Ніколи не використовувати платні сервіси.** Нижче — всі дозволені сервіси з лімітами.

### LLM (мозок агента)
| Сервіс | Ліміт (безкоштовно) | Адаптер | Пріоритет |
|--------|---------------------|---------|-----------|
| Groq API | 14 400 req/день, llama-3.1-8b | `modules/adapters/llm/groq.py` | 1 (primary) |
| Google Gemini Flash | 1 500 req/день, 1M tokens/день | `modules/adapters/llm/gemini.py` | 2 |
| Ollama (self-hosted) | ∞ (потрібен ARM VPS) | `modules/adapters/llm/ollama.py` | 3 (optional) |

### TTS (озвучка) — Chain of Responsibility
| Сервіс | Ліміт | Адаптер | Пріоритет |
|--------|-------|---------|-----------|
| ElevenLabs | 10 000 символів/місяць | `modules/adapters/tts/elevenlabs.py` | 1 |
| Google Gemini TTS | ~1 000 000 символів/день | `modules/adapters/tts/gemini_tts.py` | 2 |
| TTSMaker | 20 000 символів/тиждень | `modules/adapters/tts/ttsmaker.py` | 3 |
| edge-tts (Microsoft) | **∞ безлімітно** (без ключа) | вбудовано в chain | 4 (fallback) |

### Відео (стоки)
| Сервіс | Ліміт | Адаптер | Пріоритет |
|--------|-------|---------|-----------|
| Pexels API | 200 req/год, 20 000/місяць | `modules/adapters/video/pexels.py` | 1 |
| Pixabay API | 100 req/хв, 5 000/день | вбудовано в PexelsStockAdapter | 2 |

### Хмарний деплой
| Платформа | Ліміт | Використання |
|-----------|-------|--------------|
| GitHub Actions | 2 000 хв/місяць безкоштовно | Основний пайплайн (cron щоденно) |
| Oracle Cloud Free | 4 OCPU, 24GB RAM ARM VM | Ollama (якщо потрібен) |
| Railway.app | $5 кредитів/місяць безкоштовно | Резерв |

---

## 📁 СТРУКТУРА ПРОЕКТУ (Project Tree)

> **AI агенте:** Це канонічне дерево проекту. Кожна папка та файл вже створені (stub або реалізовані).
> Перед початком задачі — перевір, чи файл вже існує. Якщо так — редагуй, не перестворюй.

```
YTAIMBot/
│
│  ◆ КОРІНЬ — конфіги, точки входу
├── pyproject.toml            # залежності + setuptools (єдиний source-of-truth)
├── Dockerfile                # multi-stage: builder → runtime (python:3.12-slim)
├── docker-compose.yml        # bot service + optional ollama/monitoring profiles
├── .env.example              # шаблон усіх ENV vars (P0–P7), НІКОЛИ не комітити .env
├── .gitignore                # data/, .env, __pycache__, *.egg-info
└── README.md                 # hub → docs/AI_AGENT_START_PROMPT_2026.md
│
│  ◆ SRC — ML-ядро (ZERO I/O, pure domain logic)
│    ✦ Принцип: жодного import для network/FS тут
│    ✦ Всі модулі: type hints + docstring + Big-O + приклад
│
├── src/
│   └── ytaimbot_ml/
│       ├── __init__.py
│       ├── schemas.py                  # ✅ P0 — @dataclass: TrendSignal → PipelineResult
│       ├── trend_analyzer.py           # ✅ P0 — TruncatedSVD(k=2) + L2 ranking
│       │
│       ├── quality/
│       │   ├── __init__.py             # ✅ P0
│       │   └── bayes_filter.py         # ✅ P0 — Gaussian NB gate: P(bad|x) < 0.5
│       │
│       ├── content/                    # 🔲 P2 — генерація скриптів
│       │   ├── __init__.py             # 🔲 T-123
│       │   ├── script_generator.py     # 🔲 T-124 — LLM chain + template assembly
│       │   └── token_budget.py         # 🔲 T-100 — DP Knapsack O(n×W)
│       │
│       ├── seo/                        # 🔲 P3 — SEO оптимізація
│       │   ├── __init__.py             # 🔲 T-200
│       │   ├── title_optimizer.py      # 🔲 T-200 — Aho-Corasick O(Σ|p|+n)
│       │   └── thumbnail_scorer.py     # 🔲 T-217 — CIELAB ΔE contrast O(pixels)
│       │
│       ├── metrics/                    # 🔲 P5 — аналітика
│       │   ├── __init__.py             # 🔲 T-400
│       │   ├── ema_tracker.py          # 🔲 T-400 — EMA O(1)/update
│       │   └── aggregator.py           # 🔲 T-416 — Prometheus metrics collector
│       │
│       ├── rl/                         # 🔲 P6 — Reinforcement Learning
│       │   ├── __init__.py             # 🔲 T-500
│       │   ├── ucb1_bandit.py          # 🔲 T-500 — UCB1 O(k) select, O(1) update
│       │   └── reward_shaper.py        # 🔲 T-521 — Welford online variance O(1)
│       │
│       └── utils/
│           ├── __init__.py             # ✅ P0
│           ├── random.py               # ✅ P0 — make_rng(seed) → np.random.Generator
│           ├── text_utils.py           # 🔲 P2 — sanitize/truncate/normalize
│           └── hyperloglog.py          # 🔲 T-640 — HyperLogLog++ O(1) add, O(m) count
│
│  ◆ MODULES — Application layer (I/O boundary)
│    ✦ Кожен адаптер реалізує ABC з modules/adapters/base.py
│    ✦ Групування за стадіями pipeline
│
├── modules/
│   ├── __init__.py
│   ├── orchestrator.py                 # ✅ P0+P1 — build_trend_source() + Pipeline
│   │
│   └── adapters/
│       ├── __init__.py
│       ├── base.py                     # ✅ P0 — ABCs: TrendSource/Storage/Publisher
│       ├── synthetic.py                # ✅ P0 — SyntheticTrendSource, InMemoryStorage
│       ├── retry.py                    # ✅ P1 — @retry ExponentialBackoff+Jitter
│       ├── cache.py                    # ✅ P1 — TrendCache LRU+TTL OrderedDict O(1)
│       │
│       ├── trend/                      # ✅ P1 — джерела трендів
│       │   ├── __init__.py             # ✅ re-exports GoogleTrends/YouTube/Composite
│       │   └── (source files at parent level — google_trends.py, youtube_search.py, composite.py)
│       │
│       ├── google_trends.py            # ✅ P1 — trendspy RSS + fallback O(n)
│       ├── youtube_search.py           # ✅ P1 — YT Data API + QuotaTracker SlidingWindow
│       ├── composite.py                # ✅ P1 — K-way heap merge + dedup O(N log k)
│       │
│       ├── llm/                        # 🔲 P2 — LLM адаптери
│       │   ├── __init__.py             # 🔲 T-082
│       │   ├── base.py                 # 🔲 T-082 — LLMAdapter ABC
│       │   ├── groq.py                 # 🔲 T-083 — Groq API (primary, free 14k/day)
│       │   └── ollama.py               # 🔲 T-096 — Ollama local (fallback, 4GB RAM)
│       │
│       ├── tts/                        # 🔲 P2 — Text-to-Speech
│       │   ├── __init__.py             # 🔲 T-101
│       │   ├── base.py                 # 🔲 T-101 — TTSAdapter ABC
│       │   ├── edge_tts.py             # 🔲 T-102 — Microsoft Edge TTS (uk-UA-OstapNeural)
│       │   └── coqui_tts.py            # 🔲 T-116 — Coqui offline TTS (fallback)
│       │
│       ├── video/                      # 🔲 P3 — відеозборка
│       │   ├── __init__.py             # 🔲 T-300
│       │   ├── assembler.py            # 🔲 T-300 — MoviePy+FFmpeg H.264 1080p
│       │   ├── thumbnail.py            # 🔲 T-331 — Pillow 1280×720 JPEG
│       │   └── subtitle.py             # 🔲 T-356 — SRT generator + FFmpeg burn-in
│       │
│       ├── publisher/                  # 🔲 P4 — публікація
│       │   ├── __init__.py             # 🔲 T-371
│       │   ├── youtube_upload.py       # 🔲 T-371 — OAuth2 resumable upload
│       │   └── quota_guard.py          # 🔲 T-401 — Token Bucket O(1)
│       │
│       ├── storage/                    # 🔲 P5 — персистентність
│       │   ├── __init__.py             # 🔲 T-431
│       │   └── sqlite.py               # 🔲 T-431 — SQLite WAL mode B-tree O(log n)
│       │
│       └── monitoring/                 # 🔲 P7 — спостережуваність
│           ├── __init__.py             # 🔲 T-550
│           ├── prometheus.py           # 🔲 T-550 — metrics exporter :8000/metrics
│           └── alerts.py               # 🔲 T-566 — Slack/webhook threshold alerts
│
│  ◆ TESTS — дзеркально відображає src/ + modules/
│    ✦ unit/: без I/O, < 100ms
│    ✦ integration/: mocked I/O, < 1s
│    ✦ e2e/: повний pipeline, seed=42
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                     # ✅ P0 — rng/synthetic_trends fixtures
│   │
│   ├── (flat P0–P1 tests at root level)
│   ├── test_trend_analyzer.py          # ✅ P0 — 6 tests
│   ├── test_bayes_filter.py            # ✅ P0 — 9 tests
│   ├── test_orchestrator.py            # ✅ P0 — 5 tests
│   ├── test_retry.py                   # ✅ P1 — 7 tests
│   ├── test_cache.py                   # ✅ P1 — 9 tests
│   ├── test_google_trends_adapter.py   # ✅ P1 — 7 tests
│   ├── test_youtube_search_adapter.py  # ✅ P1 — 8 tests
│   ├── test_composite_adapter.py       # ✅ P1 — 7 tests
│   │
│   ├── unit/                           # 🔲 P2+ — pure function tests
│   │   ├── __init__.py
│   │   ├── test_token_budget.py        # 🔲 P2 — T-100 DP Knapsack
│   │   ├── test_title_optimizer.py     # 🔲 P3 — T-200 Aho-Corasick
│   │   ├── test_ucb1_bandit.py         # 🔲 P6 — T-500 UCB1
│   │   └── test_ema_tracker.py         # 🔲 P5 — T-400 EMA
│   │
│   ├── integration/                    # 🔲 P2+ — mocked I/O tests
│   │   ├── __init__.py
│   │   ├── test_groq_adapter.py        # 🔲 P2 — T-083
│   │   ├── test_edge_tts_adapter.py    # 🔲 P2 — T-102
│   │   ├── test_video_assembler.py     # 🔲 P3 — T-300
│   │   └── test_youtube_upload.py      # 🔲 P4 — T-371
│   │
│   └── e2e/                            # 🔲 P9 — full pipeline tests
│       ├── __init__.py
│       ├── test_pipeline_smoke.py      # ✅ active — 2 tests (synthetic, dry_run=True)
│       └── test_pipeline_full.py       # 🔲 P4+ — all stages mocked
│
│  ◆ SCRIPTS — bash операційні скрипти
│
├── scripts/
│   ├── setup_vps.sh                    # 🔲 T-551 — Ubuntu 22.04 + Docker provisioning
│   ├── backup.sh                       # 🔲 T-552 — SQLite + rsync backup
│   ├── update.sh                       # 🔲 T-553 — git pull + rolling restart
│   └── monitoring/
│       ├── prometheus.yml              # ✅ scrape config (bot:8000/metrics, 15s)
│       └── grafana_dashboard.json      # ✅ CTR/retention/quota dashboard template
│
│  ◆ DATA — runtime дані (gitignored)
│
├── data/
│   ├── README.md                       # ✅ disk space estimates + cleanup policy
│   ├── videos/                         # 🔲 P3 — rendered MP4s (~500MB each)
│   ├── audio/                          # 🔲 P2 — TTS WAV files (~50MB each)
│   ├── thumbnails/                     # 🔲 P3 — JPEG 1280×720 (~1MB each)
│   └── db/
│       └── ytaimbot.db                 # 🔲 P5 — SQLite WAL (created at runtime)
│
│  ◆ DOCS — документація + ADR
│
├── docs/
│   ├── AI_AGENT_START_PROMPT_2026.md   # ✅ онбординг для AI агентів
│   ├── ROADMAP_AI_AGENT_TASKS.md       # ✅ цей файл (640 задач)
│   ├── DEPLOYMENT_CLOUD_VPS.md         # ✅ Hetzner step-by-step guide
│   └── adr/                            # ✅ Architecture Decision Records
│       ├── ADR-0001-adapter-pattern.md         # ✅ Hexagonal Architecture
│       ├── ADR-0002-fail-closed-design.md      # ✅ Fail-closed publishing
│       ├── ADR-0003-trendspy-not-pytrends.md   # ✅ trendspy vs pytrends
│       └── ADR-0004-groq-primary-ollama-fallback.md  # ✅ LLM strategy
│
│  ◆ CI/CD
│
└── .github/
    ├── copilot-instructions.md         # ✅ AI agent coding rules
    └── workflows/
        └── ci.yml                      # ✅ GitHub Actions (Python 3.11+3.12)
```

### Легенда дерева
| Символ | Значення |
|--------|----------|
| ✅ | Файл реалізовано, тести пройдені |
| 🔲 | Файл-заглушка (stub) — чекає реалізації |
| P0–P10 | Фаза roadmap |
| T-NNN | ID задачі в цьому roadmap |

---

## 🏗️ АРХІТЕКТУРА КОНВЕЄРА (7 СТАДІЙ)

```
┌─────────────────────────────────────────────────────────────────┐
│                    YTAIMBOT PIPELINE v1.0                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  STAGE 1        STAGE 2         STAGE 3        STAGE 4          │
│  ┌─────────┐   ┌──────────┐   ┌─────────┐   ┌──────────┐      │
│  │ INGEST  │──▶│FEATURIZE │──▶│ REDUCE  │──▶│  SCORE   │      │
│  │         │   │          │   │ (SVD)   │   │ (L2 norm)│      │
│  │Trend    │   │_featurize│   │Truncated│   │ sorted   │      │
│  │Source   │   │()        │   │SVD(k=2) │   │ desc     │      │
│  │Adapter  │   │np.array  │   │         │   │          │      │
│  └─────────┘   └──────────┘   └─────────┘   └──────────┘      │
│                                                                 │
│  STAGE 5        STAGE 6         STAGE 7                         │
│  ┌─────────┐   ┌──────────┐   ┌─────────┐                      │
│  │  PLAN   │──▶│   GATE   │──▶│ PUBLISH │                      │
│  │         │   │(Bayesian)│   │(fail-   │                      │
│  │top-5    │   │P(bad|f)  │   │closed)  │                      │
│  │Content  │   │threshold │   │         │                      │
│  │Plans    │   │= 0.5     │   │DRY_RUN  │                      │
│  └─────────┘   └──────────┘   └─────────┘                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Алгоритми в конвеєрі:**
- **Stage 2:** Hash-derived features → `O(d)` де `d` = кількість ознак
- **Stage 3:** TruncatedSVD → `O(min(n,d) × n × d)` де `n` = сигнали
- **Stage 4:** L2 norm → `O(n×k)`, сортування `O(n log n)` (QuickSort в NumPy)
- **Stage 6:** Naive Bayes → `O(n_features)` per sample
- **Stage 7:** Fail-closed gate → `O(1)` decision check

---

═══════════════════════════════════════════════════════════════════
## 📦 PHASE 0: FOUNDATION (SKELETON) — ✅ ЗАВЕРШЕНО
═══════════════════════════════════════════════════════════════════

**Ціль:** Запускаємий Python-пакет із детермінованими ML-заглушками та CI, що проходить.
**Тиждень:** 1 | **Статус:** ✅ Повністю завершено

> ℹ️ AI агенте: ці задачі вже виконані. Не змінюй ці файли без явної потреби.
> Використовуй їх як базу для наступних фаз.

### Таблиця задач Phase 0

| ID | Статус | Задача | Файл(и) | Складність | Виконано |
|----|--------|--------|---------|-----------|---------|
| T-001 | ✅ | Ініціалізувати pyproject.toml з залежностями | `pyproject.toml` | S | 2026-01-W1 |
| T-002 | ✅ | Створити схеми даних (dataclasses) | `src/ytaimbot_ml/schemas.py` | M | 2026-01-W1 |
| T-003 | ✅ | Реалізувати TrendAnalyzer (SVD-based ranking) | `src/ytaimbot_ml/trend_analyzer.py` | L | 2026-01-W1 |
| T-004 | ✅ | Реалізувати BayesQualityFilter | `src/ytaimbot_ml/quality/bayes_filter.py` | L | 2026-01-W1 |
| T-005 | ✅ | Реалізувати make_rng (seeded RNG factory) | `src/ytaimbot_ml/utils/random.py` | S | 2026-01-W1 |
| T-006 | ✅ | Визначити ABC інтерфейси адаптерів | `modules/adapters/base.py` | M | 2026-01-W1 |
| T-007 | ✅ | Реалізувати синтетичні адаптери (тестові) | `modules/adapters/synthetic.py` | M | 2026-01-W1 |
| T-008 | ✅ | Реалізувати Pipeline (7-стадійний оркестратор) | `modules/orchestrator.py` | XL | 2026-01-W1 |
| T-009 | ✅ | Написати тести для TrendAnalyzer (6 тестів) | `tests/test_trend_analyzer.py` | M | 2026-01-W1 |
| T-010 | ✅ | Написати тести для BayesQualityFilter (9 тестів) | `tests/test_bayes_filter.py` | M | 2026-01-W1 |
| T-011 | ✅ | Написати тести для Pipeline (5 тестів) | `tests/test_orchestrator.py` | M | 2026-01-W1 |
| T-012 | ✅ | Налаштувати pytest fixtures | `tests/conftest.py` | S | 2026-01-W1 |
| T-013 | ✅ | Налаштувати GitHub Actions CI | `.github/workflows/ci.yml` | S | 2026-01-W1 |
| T-014 | ✅ | Створити Dockerfile + docker-compose.yml | `Dockerfile`, `docker-compose.yml` | M | 2026-01-W1 |
| T-015 | ✅ | Заповнити .env.example | `.env.example` | S | 2026-01-W1 |

---

═══════════════════════════════════════════════════════════════════
## 🌐 PHASE 1: REAL TREND ADAPTERS — 🔲 НАСТУПНА ФАЗА
═══════════════════════════════════════════════════════════════════

**Ціль:** Замінити SyntheticTrendSource реальними даними з Google Trends та YouTube API.
**Тиждень:** 2–3 | **Пріоритет:** 🔴 Critical
**Залежності Phase 1 → Phase 0 (T-001–T-015 всі ✅)**

**Алгоритми в цій фазі:**
- **Exponential Backoff:** `delay = base × 2^attempt + jitter` → `O(max_retries)`
- **Composite Merge:** Priority Queue (heap) для злиття сигналів → `O(n log k)`
- **Quota Tracking:** Sliding Window Counter → `O(1)` amortized
- **Cache:** LRU Cache (functools.lru_cache) → `O(1)` lookup

### 📌 EPIC 1.1 — Retry Infrastructure (базова інфраструктура повторних спроб)

> **AI агенте:** Починай з цього epic. Retry декоратор використовується ВСІМА
> адаптерами. Без нього Phase 1 не може бути виконана.

**Алгоритм Exponential Backoff з jitter:**
```
delay(attempt) = min(base × 2^attempt + random(0, base), max_delay)

attempt=0: delay = 2 + jitter  → ~2s
attempt=1: delay = 4 + jitter  → ~4s
attempt=2: delay = 8 + jitter  → ~8s
MAX_DELAY = 30s (капуємо)
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-016 | 🔲 | Створити модуль retry з exponential backoff | `modules/adapters/retry.py` | M | T-006 | — |
| T-017 | 🔲 | Реалізувати декоратор `@retry(max_retries, base_delay, jitter)` | `modules/adapters/retry.py` | M | T-016 | — |
| T-018 | 🔲 | Реалізувати `RetryableError` та `NonRetryableError` exceptions | `modules/adapters/retry.py` | S | T-016 | — |
| T-019 | 🔲 | Написати тести для retry декоратора (mock time.sleep) | `tests/test_retry.py` | M | T-017, T-018 | — |
| T-020 | 🔲 | Тест: перевірити затримки (2s → 4s → 8s) | `tests/test_retry.py` | S | T-019 | — |
| T-021 | 🔲 | Тест: перевірити max_retries (зупиняється після N спроб) | `tests/test_retry.py` | S | T-019 | — |
| T-022 | 🔲 | Тест: NonRetryableError не ретраїться | `tests/test_retry.py` | S | T-019 | — |
| T-023 | 🔲 | Тест: jitter детермінований при seed=42 | `tests/test_retry.py` | S | T-019 | — |

**Acceptance для EPIC 1.1:**
- [ ] `@retry` декоратор працює з будь-яким адаптером
- [ ] `time.sleep` замоканий у тестах (не чекаємо реально)
- [ ] Jitter детермінований коли передано seed

---

### 📌 EPIC 1.2 — Google Trends Adapter

> **AI агенте:** Цей адаптер використовує `trendspyg` (RSS-based).
> **НЕ використовуй** `pytrends` — він застарів і deprecated (ADR-0003).
> Fallback → SyntheticTrendSource при будь-якій помилці мережі.

**Структура даних для парсингу RSS:**
```
RSS Feed → list[dict] → list[TrendSignal]

TrendSignal(
    keyword=entry.title,          # "Python tutorial 2026"
    raw_score=normalize(rank),     # 0.0 – 1.0
    source="google_trends",
    fetched_at=datetime.utcnow(),
    metadata={"geo": "US", "rank": i}
)
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-024 | 🔲 | Додати `trendspyg` до pyproject.toml | `pyproject.toml` | S | T-001 | — |
| T-025 | 🔲 | Створити `GoogleTrendsTrendSource` клас | `modules/adapters/google_trends.py` | M | T-006, T-016 | — |
| T-026 | 🔲 | Реалізувати `fetch()` — RSS парсинг → list[TrendSignal] | `modules/adapters/google_trends.py` | L | T-025 | — |
| T-027 | 🔲 | Реалізувати geo параметр (US, UA, GB — конфігурується) | `modules/adapters/google_trends.py` | S | T-026 | — |
| T-028 | 🔲 | Реалізувати normalize — rank → float [0.0, 1.0] | `modules/adapters/google_trends.py` | S | T-026 | — |
| T-029 | 🔲 | Додати `@retry` декоратор до fetch() | `modules/adapters/google_trends.py` | S | T-017, T-026 | — |
| T-030 | 🔲 | Реалізувати fallback → SyntheticTrendSource | `modules/adapters/google_trends.py` | M | T-029 | — |
| T-031 | 🔲 | Написати тести (mock trendspyg.download_rss) | `tests/test_google_trends_adapter.py` | M | T-025 | — |
| T-032 | 🔲 | Тест: fetch() повертає list[TrendSignal] ≥ 10 елементів | `tests/test_google_trends_adapter.py` | S | T-031 | — |
| T-033 | 🔲 | Тест: raw_score в діапазоні [0.0, 1.0] | `tests/test_google_trends_adapter.py` | S | T-031 | — |
| T-034 | 🔲 | Тест: 429/500 помилка → fallback до synthetic | `tests/test_google_trends_adapter.py` | M | T-031 | — |
| T-035 | 🔲 | Тест: geo параметр передається в RSS запит | `tests/test_google_trends_adapter.py` | S | T-031 | — |
| T-036 | 🔲 | Тест: детермінізм при однакових даних | `tests/test_google_trends_adapter.py` | S | T-031 | — |

**Acceptance для EPIC 1.2:**
- [ ] Реалізує `TrendSourceAdapter` ABC
- [ ] Ніяких реальних мережевих викликів у тестах
- [ ] Обробляє rate limits (429) та серверні помилки (500)
- [ ] Graceful fallback до synthetic при будь-якій помилці

---

### 📌 EPIC 1.3 — YouTube Search Adapter

> **AI агенте:** Використовуй YouTube Data API v3 endpoint `search.list`.
> API ключ береться з `os.environ["YOUTUBE_API_KEY"]` — ніколи не хардкодь.
> Реалізуй quota tracking: кожен `search.list` коштує 100 units.
> Daily budget = 10,000 units → max 100 запитів/день.

**Quota Tracking алгоритм (Sliding Window Counter):**
```
QuotaTracker:
  - window_size = 86400s (1 день)
  - max_units = 10_000
  - structure: deque[(timestamp, units_used)]

  can_proceed(units) → bool:
    # Видалити записи старіші за window_size → O(k) де k = expired
    now = time.time()
    while deque[0].timestamp < now - window_size:
        deque.popleft()  # O(1)
    used = sum(units for _, units in deque)  # O(n) worst case
    return used + units <= max_units

  record(units):
    deque.append((time.time(), units))  # O(1)
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-037 | 🔲 | Додати `google-api-python-client` до pyproject.toml | `pyproject.toml` | S | T-001 | — |
| T-038 | 🔲 | Створити `QuotaTracker` клас (Sliding Window) | `modules/adapters/youtube_search.py` | M | T-037 | — |
| T-039 | 🔲 | Реалізувати `YouTubeSearchTrendSource` клас | `modules/adapters/youtube_search.py` | M | T-006, T-038 | — |
| T-040 | 🔲 | Реалізувати `fetch()` — search.list → list[TrendSignal] | `modules/adapters/youtube_search.py` | L | T-039 | — |
| T-041 | 🔲 | Реалізувати quota-aware виклик (перевірка перед запитом) | `modules/adapters/youtube_search.py` | M | T-038, T-040 | — |
| T-042 | 🔲 | Реалізувати логування quota використання (INFO) | `modules/adapters/youtube_search.py` | S | T-041 | — |
| T-043 | 🔲 | Реалізувати fallback → SyntheticTrendSource при quota exceeded | `modules/adapters/youtube_search.py` | M | T-041 | — |
| T-044 | 🔲 | Додати `@retry` до YouTube API викликів | `modules/adapters/youtube_search.py` | S | T-017, T-040 | — |
| T-045 | 🔲 | Написати тести (mock googleapiclient) | `tests/test_youtube_search_adapter.py` | M | T-039 | — |
| T-046 | 🔲 | Тест: fetch() повертає list[TrendSignal] | `tests/test_youtube_search_adapter.py` | S | T-045 | — |
| T-047 | 🔲 | Тест: quota exceeded → fallback до synthetic | `tests/test_youtube_search_adapter.py` | M | T-045 | — |
| T-048 | 🔲 | Тест: API ключ відсутній → ValueError з корисним повідомленням | `tests/test_youtube_search_adapter.py` | S | T-045 | — |
| T-049 | 🔲 | Тест: QuotaTracker рахує units правильно | `tests/test_youtube_search_adapter.py` | M | T-045 | — |
| T-050 | 🔲 | Тест: QuotaTracker скидає після window_size | `tests/test_youtube_search_adapter.py` | M | T-045 | — |

**Acceptance для EPIC 1.3:**
- [ ] Реалізує `TrendSourceAdapter` ABC
- [ ] Quota tracking через Sliding Window Counter
- [ ] YOUTUBE_API_KEY тільки з env var
- [ ] Ніяких реальних HTTP викликів у тестах

---

### 📌 EPIC 1.4 — Composite Trend Adapter (злиття сигналів)

> **AI агенте:** CompositeAdapter зливає сигнали від Google Trends + YouTube.
> Алгоритм злиття — Priority Queue (max-heap) за raw_score.
> Дедублікація ключових слів через normalized string comparison.
> Структура: `adapters: list[TrendSourceAdapter]` — легко розширити.

**Алгоритм злиття (K-way merge з Priority Queue):**
```
all_signals = []
for adapter in adapters:
    signals = adapter.fetch()  # O(n_i) per adapter
    all_signals.extend(signals)  # accumulate

# Дедублікація: normalize → lower() + strip()
seen: dict[str, TrendSignal] = {}
for signal in all_signals:
    key = signal.keyword.lower().strip()
    if key not in seen or signal.raw_score > seen[key].raw_score:
        seen[key] = signal  # зберігаємо кращий score

# Фінальне сортування: max-heap → O(n log n)
result = sorted(seen.values(), key=lambda s: s.raw_score, reverse=True)
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-051 | 🔲 | Створити `CompositeTrendSource` клас | `modules/adapters/composite.py` | M | T-006, T-025, T-039 | — |
| T-052 | 🔲 | Реалізувати K-way merge алгоритм | `modules/adapters/composite.py` | L | T-051 | — |
| T-053 | 🔲 | Реалізувати дедублікацію (normalized key comparison) | `modules/adapters/composite.py` | M | T-052 | — |
| T-054 | 🔲 | Реалізувати weights (кожен адаптер має weight множник) | `modules/adapters/composite.py` | M | T-052 | — |
| T-055 | 🔲 | Реалізувати fallback якщо всі адаптери впали | `modules/adapters/composite.py` | M | T-051 | — |
| T-056 | 🔲 | Написати тести (обидва адаптери замоканні) | `tests/test_composite_adapter.py` | M | T-051 | — |
| T-057 | 🔲 | Тест: злиття повертає відсортований list[TrendSignal] | `tests/test_composite_adapter.py` | S | T-056 | — |
| T-058 | 🔲 | Тест: дублікати видаляються (кращий score залишається) | `tests/test_composite_adapter.py` | M | T-056 | — |
| T-059 | 🔲 | Тест: weights впливають на фінальний score | `tests/test_composite_adapter.py` | M | T-056 | — |
| T-060 | 🔲 | Тест: якщо Google Trends впав → YouTube залишається | `tests/test_composite_adapter.py` | M | T-056 | — |

---

### 📌 EPIC 1.5 — Cache Layer для Trend Adapters

> **AI агенте:** LRU Cache зменшує кількість API викликів.
> TTL = 900s (15 хвилин) — тренди не змінюються швидше.
> Структура: OrderedDict для O(1) get/put.

**LRU Cache алгоритм:**
```
LRUCache(capacity=128, ttl_seconds=900):
  cache: OrderedDict[str, (value, timestamp)]

  get(key) → value | None:   # O(1)
    if key not in cache: return None
    value, ts = cache[key]
    if time.time() - ts > ttl: del cache[key]; return None
    cache.move_to_end(key)   # mark as recently used
    return value

  put(key, value):           # O(1)
    cache[key] = (value, time.time())
    cache.move_to_end(key)
    if len(cache) > capacity:
        cache.popitem(last=False)  # evict LRU
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-061 | 🔲 | Створити `TrendCache` клас (LRU + TTL) | `modules/adapters/cache.py` | M | T-006 | — |
| T-062 | 🔲 | Реалізувати `get(key)` → O(1) з TTL перевіркою | `modules/adapters/cache.py` | M | T-061 | — |
| T-063 | 🔲 | Реалізувати `put(key, value)` → O(1) з eviction | `modules/adapters/cache.py` | M | T-061 | — |
| T-064 | 🔲 | Інтегрувати `TrendCache` в `CompositeTrendSource` | `modules/adapters/composite.py` | M | T-061, T-051 | — |
| T-065 | 🔲 | Написати тести для LRU Cache | `tests/test_cache.py` | M | T-061 | — |
| T-066 | 🔲 | Тест: cache hit повертає значення без API виклику | `tests/test_cache.py` | S | T-065 | — |
| T-067 | 🔲 | Тест: TTL expired → cache miss → новий виклик | `tests/test_cache.py` | M | T-065 | — |
| T-068 | 🔲 | Тест: capacity limit → LRU eviction | `tests/test_cache.py` | M | T-065 | — |

---

### 📌 EPIC 1.6 — Інтеграція Phase 1 в Pipeline + оновлення конфігурації

> **AI агенте:** Оновити orchestrator.py для підтримки нових адаптерів.
> Логіка вибору адаптера визначається env vars (YOUTUBE_API_KEY присутній → YouTube).
> Додати нові env vars до .env.example та docker-compose.yml.

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-069 | 🔲 | Оновити `Pipeline.__init__` для автовибору адаптера | `modules/orchestrator.py` | M | T-051, T-024, T-037 | — |
| T-070 | 🔲 | Додати `GOOGLE_TRENDS_GEO` env var (default: "US") | `.env.example` | S | T-027 | — |
| T-071 | 🔲 | Додати `TREND_CACHE_TTL` env var (default: "900") | `.env.example` | S | T-061 | — |
| T-072 | 🔲 | Додати `ADAPTER_WEIGHTS` env var (default: "1.0,1.0") | `.env.example` | S | T-054 | — |
| T-073 | 🔲 | Оновити docker-compose.yml новими env vars | `docker-compose.yml` | S | T-070, T-071 | — |
| T-074 | 🔲 | Написати інтеграційні тести Pipeline з новими адаптерами | `tests/test_orchestrator.py` | L | T-069 | — |
| T-075 | 🔲 | Тест: Pipeline з GoogleTrends adapter (повністю замокано) | `tests/test_orchestrator.py` | M | T-074 | — |
| T-076 | 🔲 | Тест: Pipeline з YouTube adapter (повністю замокано) | `tests/test_orchestrator.py` | M | T-074 | — |
| T-077 | 🔲 | Тест: Pipeline з Composite adapter | `tests/test_orchestrator.py` | M | T-074 | — |
| T-078 | 🔲 | Запустити повний тест-сьют `pytest -q --tb=short` | CI | S | T-077 | — |
| T-079 | 🔲 | Перевірити покриття коду ≥ 80% (`pytest --cov`) | CI | S | T-078 | — |
| T-080 | 🔲 | Оновити Dockerfile: встановити нові залежності | `Dockerfile` | S | T-024, T-037 | — |

**Acceptance для PHASE 1 (загалом):**
- [ ] `pytest -q` → всі тести зелені
- [ ] Test coverage `src/ + modules/` ≥ 80%
- [ ] `docker compose build` → успішно
- [ ] Google Trends повертає ≥ 10 реальних трендів (manual test)
- [ ] YouTube API повертає сигнали (при наявності API ключа)
- [ ] Quota tracker не перевищує 10,000 units/день
- [ ] Composite merge дедублікує ключові слова
- [ ] Retry з jitter: детермінований при seed=42
- [ ] CI/CD pipeline на GitHub Actions → зелений

---

═══════════════════════════════════════════════════════════════════
## 📝 PHASE 2: CONTENT GENERATION — 🔲 PENDING (залежить P1)
═══════════════════════════════════════════════════════════════════

**Ціль:** Генерація відеосценаріїв, озвучення та шаблонів на основі трендів.
**Тиждень:** 4–5 | **Пріоритет:** 🔴 Critical
**Залежності:** Phase 2 → Phase 1 повністю ✅

**Алгоритми в цій фазі:**
- **Token Budget DP:** Dynamic Programming для оптимізації розподілу токенів → `O(n×W)`
- **Template Engine:** String interpolation + regex → `O(n)` на символ
- **Fallback Chain:** Ланцюг відповідальності (Chain of Responsibility) → `O(k)` де k = адаптери
- **Text Chunking:** Sliding Window з overlap для довгих скриптів → `O(n)`
- **Priority Queue:** Сортування шаблонів за relevance score → `O(n log n)`

---

### 📌 EPIC 2.1 — LLM Adapter (Ollama на VPS або Groq API)

> **AI агенте:** Два варіанти LLM — обидва працюють у ХМАРІ (локальний ПК не потрібен).
>
> **Варіант A (Рекомендовано): Groq API** — безкоштовний хмарний LLM, 14K req/день.
>   - Швидше ніж Ollama, не навантажує VPS RAM
>   - `LLM_PROVIDER=groq`, `GROQ_API_KEY=gsk_...`
>   - Модель: `llama-3.1-8b-instant` або `gemma2-9b-it`
>
> **Варіант B: Ollama на тому ж VPS** — потрібно 4GB+ RAM (Hetzner CX32, €5.77/міс).
>   - `OLLAMA_URL=http://ollama:11434` (docker-compose service)
>   - Модель: `llama3.2:3b` (мала модель, поміщається в 4GB)
>
> **Пріоритет реалізації:** спочатку Groq (простіше), потім Ollama як fallback.
> Використовуй `httpx` для HTTP викликів. Token budget guard обов'язковий.

**Алгоритм Token Budget (Dynamic Programming):**
```
token_budget_dp(sections: list[str], max_tokens: int) -> list[int]:
    """
    Розподіл токенів між секціями скрипту.
    dp[i] = максимальна якість перших i секцій при budget B
    Складність: O(n × max_tokens)
    """
    n = len(sections)
    weights = [estimate_tokens(s) for s in sections]
    # Knapsack-like: кожна секція ПОВИННА бути включена,
    # але можна скорочувати (min_ratio = 0.5)
    total = sum(weights)
    if total <= max_tokens:
        return weights  # все поміщається
    scale = max_tokens / total
    return [max(int(w * scale), int(w * 0.5)) for w in weights]
```

**Fallback Chain для LLM (cloud-first):**
```
LLMFallbackChain:
  1. GroqAdapter (api.groq.com — безкоштовно)  → якщо недоступний або ключ відсутній
  2. OllamaAdapter (http://ollama:11434 на VPS) → якщо Ollama не запущений
  3. TemplateOnlyGenerator                      → якщо шаблони не підходять
  4. raise ContentGenerationError               → fail loudly
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-081 | 🔲 | Додати `httpx` до pyproject.toml | `pyproject.toml` | S | T-001 | — |
| T-082 | 🔲 | Визначити `LLMAdapter` ABC у base.py | `modules/adapters/base.py` | S | T-006 | — |
| T-083 | 🔲 | Створити `GroqAdapter` клас (cloud LLM — основний) | `modules/adapters/llm_groq.py` | M | T-082 | — |
| T-084 | 🔲 | Реалізувати `generate(prompt, model, max_tokens)` → str | `modules/adapters/llm_groq.py` | L | T-083 | — |
| T-085 | 🔲 | Реалізувати `health_check()` → bool (ping Groq API) | `modules/adapters/llm_groq.py` | S | T-083 | — |
| T-086 | 🔲 | Реалізувати token budget guard (обрізає prompt якщо > ліміт) | `modules/adapters/llm_groq.py` | M | T-084 | — |
| T-087 | 🔲 | Реалізувати `OllamaAdapter` (VPS fallback, http://ollama:11434) | `modules/adapters/llm_local.py` | M | T-082 | — |
| T-088 | 🔲 | Реалізувати `LLMFallbackChain` (Groq → Ollama → Template) | `modules/adapters/llm_local.py` | M | T-083, T-087 | — |
| T-089 | 🔲 | Додати `@retry` до HTTP викликів | `modules/adapters/llm_groq.py` | S | T-017, T-084 | — |
| T-090 | 🔲 | Зчитувати `LLM_PROVIDER`, `GROQ_API_KEY`, `OLLAMA_URL` з env vars | `modules/adapters/llm_groq.py` | S | T-083 | — |
| T-091 | 🔲 | Написати тести (mock httpx.AsyncClient) | `tests/test_llm_adapter.py` | M | T-083 | — |
| T-092 | 🔲 | Тест: generate() повертає непорожній string | `tests/test_llm_adapter.py` | S | T-091 | — |
| T-093 | 🔲 | Тест: Groq недоступний → fallback до OllamaAdapter | `tests/test_llm_adapter.py` | M | T-091 | — |
| T-094 | 🔲 | Тест: token budget guard обрізає довгий prompt | `tests/test_llm_adapter.py` | M | T-091 | — |
| T-095 | 🔲 | Тест: GROQ_API_KEY читається з env var | `tests/test_llm_adapter.py` | S | T-091 | — |

**Acceptance для EPIC 2.1:**
- [ ] Реалізує `LLMAdapter` ABC
- [ ] Groq API як основний провайдер (безкоштовно)
- [ ] Ollama як fallback (якщо Groq недоступний)
- [ ] Token budget guard обов'язковий
- [ ] Fallback chain логується на рівні WARNING

---

### 📌 EPIC 2.2 — TTS Adapter: Edge-TTS (первинний)

> **AI агенте:** `edge-tts` — безкоштовні Microsoft Azure Neural Voices.
> Підтримуй українську мову: `uk-UA-OstapNeural` (чоловічий), `uk-UA-PolinaNeural` (жіночий).
> Інтерфейс — **async** (edge-tts є async-бібліотекою).
> Вихідний файл: `.mp3` у `YTAIMBOT_DATA_DIR/audio/`.

**Алгоритм вибору голосу:**
```python
VOICE_MAP = {
    "uk": {"male": "uk-UA-OstapNeural", "female": "uk-UA-PolinaNeural"},
    "en": {"male": "en-US-GuyNeural",   "female": "en-US-JennyNeural"},
    "ru": {"male": "ru-RU-DmitryNeural","female": "ru-RU-SvetlanaNeural"},
}

def select_voice(lang: str, gender: str = "male") -> str:
    return VOICE_MAP.get(lang, VOICE_MAP["en"])[gender]
    # O(1) — hash map lookup
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-096 | 🔲 | Додати `edge-tts` до pyproject.toml | `pyproject.toml` | S | T-001 | — |
| T-097 | 🔲 | Визначити `TTSAdapter` ABC у base.py | `modules/adapters/base.py` | S | T-006 | — |
| T-098 | 🔲 | Створити `EdgeTTSAdapter` клас | `modules/adapters/tts_edge.py` | M | T-097 | — |
| T-099 | 🔲 | Реалізувати `async synthesize(text, voice, output_path)` → Path | `modules/adapters/tts_edge.py` | L | T-098 | — |
| T-100 | 🔲 | Реалізувати `select_voice(lang, gender)` → str (hash map) | `modules/adapters/tts_edge.py` | S | T-098 | — |
| T-101 | 🔲 | Реалізувати text chunking для довгих скриптів (>5000 символів) | `modules/adapters/tts_edge.py` | M | T-099 | — |
| T-102 | 🔲 | Реалізувати конкатенацію audio chunks → один .mp3 | `modules/adapters/tts_edge.py` | M | T-101 | — |
| T-103 | 🔲 | Зберігати вихідний файл у `YTAIMBOT_DATA_DIR/audio/` | `modules/adapters/tts_edge.py` | S | T-099 | — |
| T-104 | 🔲 | Написати тести (mock edge_tts.Communicate) | `tests/test_tts_edge.py` | M | T-098 | — |
| T-105 | 🔲 | Тест: synthesize() повертає валідний шлях до .mp3 | `tests/test_tts_edge.py` | S | T-104 | — |
| T-106 | 🔲 | Тест: select_voice("uk", "male") → "uk-UA-OstapNeural" | `tests/test_tts_edge.py` | S | T-104 | — |
| T-107 | 🔲 | Тест: текст > 5000 символів розбивається на chunks | `tests/test_tts_edge.py` | M | T-104 | — |
| T-108 | 🔲 | Тест: невідома мова → fallback до en-US | `tests/test_tts_edge.py` | S | T-104 | — |

---

### 📌 EPIC 2.3 — TTS Fallback: Coqui TTS (локальний, офлайн)

> **AI агенте:** Coqui TTS працює **повністю офлайн** — критично для Hetzner UA.
> Це fallback коли Edge-TTS заблокований Microsoft.
> CPU mode для MVP (GPU опційно через `USE_GPU=true` env var).
> Модель: `tts_models/en/ljspeech/tacotron2-DDC` (найлегша, ~150MB).

**Fallback Chain для TTS:**
```
TTSFallbackChain:
  1. EdgeTTSAdapter     → якщо Microsoft заблокував (ConnectionError)
  2. CoquiTTSAdapter    → якщо модель не завантажена
  3. raise TTSError     → fail loudly, зупинити pipeline
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-109 | 🔲 | Додати `TTS` (Coqui) до pyproject.toml як optional dep | `pyproject.toml` | S | T-001 | — |
| T-110 | 🔲 | Створити `CoquiTTSAdapter` клас | `modules/adapters/tts_local.py` | M | T-097 | — |
| T-111 | 🔲 | Реалізувати `synthesize(text, model, output_path)` → Path | `modules/adapters/tts_local.py` | L | T-110 | — |
| T-112 | 🔲 | Реалізувати CPU mode (`use_gpu=False` за замовчуванням) | `modules/adapters/tts_local.py` | S | T-110 | — |
| T-113 | 🔲 | Реалізувати lazy model loading (завантажуємо при першому виклику) | `modules/adapters/tts_local.py` | M | T-111 | — |
| T-114 | 🔲 | Реалізувати `TTSFallbackChain` (Edge → Coqui → Error) | `modules/adapters/tts_local.py` | M | T-098, T-110 | — |
| T-115 | 🔲 | Зберігати вихідний файл у `YTAIMBOT_DATA_DIR/audio/` | `modules/adapters/tts_local.py` | S | T-111 | — |
| T-116 | 🔲 | Написати тести (mock TTS клас, пропускати якщо не встановлено) | `tests/test_tts_local.py` | M | T-110 | — |
| T-117 | 🔲 | Тест: synthesize() повертає валідний шлях до .wav | `tests/test_tts_local.py` | S | T-116 | — |
| T-118 | 🔲 | Тест: Edge-TTS fail → автоматичний fallback до Coqui | `tests/test_tts_local.py` | M | T-116 | — |
| T-119 | 🔲 | Тест: lazy loading — модель не завантажується при імпорті | `tests/test_tts_local.py` | S | T-116 | — |
| T-120 | 🔲 | Тест: USE_GPU=false → CPU mode активний | `tests/test_tts_local.py` | S | T-116 | — |

---

### 📌 EPIC 2.4 — Script Generator (генерація сценаріїв)

> **AI агенте:** ScriptGenerator — серце Phase 2.
> Отримує `ContentPlan` → генерує повний відеосценарій (≥500 слів).
> Структура скрипту: Hook (15с) → Intro (30с) → Body (3-5 блоків) → CTA (30с).
> SEO keywords вставляються природно (не spam).
> Детермінізм: seed контролює вибір шаблону та LLM temperature.

**Алгоритм генерації скрипту:**
```
ScriptGenerator.generate(plan: ContentPlan, seed: int) -> Script:

  1. Вибрати template за niche → O(1) hash lookup
  2. Розподілити token budget між секціями → O(n) DP
  3. Для кожної секції:
     a. Підготувати prompt з keywords → O(k) де k = keywords
     b. Викликати LLMAdapter.generate() → O(tokens)
     c. Валідувати вихід (≥ min_words, містить keywords) → O(words)
  4. Зібрати секції → повний Script → O(n_sections)
  5. Повернути Script dataclass

  Загальна складність: O(n_sections × tokens)
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-121 | 🔲 | Створити `Script` dataclass у schemas.py | `src/ytaimbot_ml/schemas.py` | S | T-002 | — |
| T-122 | 🔲 | Створити `ScriptSection` dataclass (hook/intro/body/cta) | `src/ytaimbot_ml/schemas.py` | S | T-121 | — |
| T-123 | 🔲 | Створити `src/ytaimbot_ml/content/` пакет | `src/ytaimbot_ml/content/__init__.py` | S | T-003 | — |
| T-124 | 🔲 | Реалізувати `ScriptGenerator` клас | `src/ytaimbot_ml/content/generator.py` | L | T-082, T-123 | — |
| T-125 | 🔲 | Реалізувати `generate(plan, rng)` → Script | `src/ytaimbot_ml/content/generator.py` | XL | T-124 | — |
| T-126 | 🔲 | Реалізувати `_build_hook_prompt(plan)` → str | `src/ytaimbot_ml/content/generator.py` | M | T-124 | — |
| T-127 | 🔲 | Реалізувати `_build_body_prompt(plan, section_idx)` → str | `src/ytaimbot_ml/content/generator.py` | M | T-124 | — |
| T-128 | 🔲 | Реалізувати `_build_cta_prompt(plan)` → str | `src/ytaimbot_ml/content/generator.py` | S | T-124 | — |
| T-129 | 🔲 | Реалізувати `_validate_script(script)` → bool (≥500 слів) | `src/ytaimbot_ml/content/generator.py` | M | T-124 | — |
| T-130 | 🔲 | Реалізувати `_inject_keywords(text, keywords)` → str | `src/ytaimbot_ml/content/generator.py` | M | T-124 | — |
| T-131 | 🔲 | Написати тести для ScriptGenerator (mock LLMAdapter) | `tests/test_script_generator.py` | M | T-124 | — |
| T-132 | 🔲 | Тест: generate() повертає Script з ≥500 слів | `tests/test_script_generator.py` | M | T-131 | — |
| T-133 | 🔲 | Тест: всі keywords присутні у скрипті | `tests/test_script_generator.py` | M | T-131 | — |
| T-134 | 🔲 | Тест: детермінізм — однаковий seed → однаковий результат | `tests/test_script_generator.py` | M | T-131 | — |
| T-135 | 🔲 | Тест: структура Script має hook/intro/body/cta секції | `tests/test_script_generator.py` | S | T-131 | — |

---

### 📌 EPIC 2.5 — Content Template System

> **AI агенте:** Шаблони — це Markdown файли з `{placeholder}` змінними.
> Мінімум 5 шаблонів для різних ніш (tutorial, explainer, shorts, review, listicle).
> `TemplateEngine` завантажує шаблони з диску, кешує в пам'яті (dict).
> Вибір шаблону: cosine similarity між ContentPlan.keywords та template.tags → O(n×m).

**Алгоритм вибору шаблону (Cosine Similarity):**
```
select_template(plan: ContentPlan, templates: list[Template]) -> Template:
    """
    Для кожного шаблону рахуємо cosine similarity між
    векторами keyword-наборів.
    Складність: O(n_templates × n_keywords)
    """
    plan_vec = keyword_vector(plan.keywords)   # TF-IDF-like bag of words
    scores = []
    for t in templates:
        t_vec = keyword_vector(t.tags)
        score = cosine_similarity(plan_vec, t_vec)  # O(vocab_size)
        scores.append((score, t))
    return max(scores, key=lambda x: x[0])[1]  # O(n_templates)
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-136 | 🔲 | Створити `templates/` директорію | `src/ytaimbot_ml/content/templates/` | S | T-123 | — |
| T-137 | 🔲 | Створити шаблон `tutorial.md` (how-to контент) | `src/ytaimbot_ml/content/templates/tutorial.md` | M | T-136 | — |
| T-138 | 🔲 | Створити шаблон `explainer.md` (пояснювальний контент) | `src/ytaimbot_ml/content/templates/explainer.md` | M | T-136 | — |
| T-139 | 🔲 | Створити шаблон `shorts.md` (Shorts ≤60с) | `src/ytaimbot_ml/content/templates/shorts.md` | M | T-136 | — |
| T-140 | 🔲 | Створити шаблон `review.md` (огляди продуктів) | `src/ytaimbot_ml/content/templates/review.md` | M | T-136 | — |
| T-141 | 🔲 | Створити шаблон `listicle.md` (топ-N формат) | `src/ytaimbot_ml/content/templates/listicle.md` | M | T-136 | — |
| T-142 | 🔲 | Реалізувати `TemplateEngine` клас | `src/ytaimbot_ml/content/template_engine.py` | M | T-123 | — |
| T-143 | 🔲 | Реалізувати `load_templates()` → dict[str, Template] (з кешем) | `src/ytaimbot_ml/content/template_engine.py` | M | T-142 | — |
| T-144 | 🔲 | Реалізувати `select_template(plan)` → Template (cosine sim) | `src/ytaimbot_ml/content/template_engine.py` | L | T-142 | — |
| T-145 | 🔲 | Реалізувати `render(template, variables)` → str | `src/ytaimbot_ml/content/template_engine.py` | M | T-142 | — |
| T-146 | 🔲 | Написати тести для TemplateEngine | `tests/test_template_engine.py` | M | T-142 | — |
| T-147 | 🔲 | Тест: select_template повертає найбільш релевантний шаблон | `tests/test_template_engine.py` | M | T-146 | — |
| T-148 | 🔲 | Тест: render() замінює всі {placeholder} | `tests/test_template_engine.py` | S | T-146 | — |
| T-149 | 🔲 | Тест: load_templates() кешує — повторний виклик не читає диск | `tests/test_template_engine.py` | M | T-146 | — |
| T-150 | 🔲 | Тест: невідомий шаблон → fallback до `explainer.md` | `tests/test_template_engine.py` | S | T-146 | — |

---

### 📌 EPIC 2.6 — Інтеграція Phase 2 в Pipeline

> **AI агенте:** Розширити `Pipeline` у orchestrator.py двома новими стадіями:
> **Stage 8:** `_generate_script()` (після plan, перед gate)
> **Stage 9:** `_synthesize_audio()` (після gate pass, перед publish)
> Оновити `PipelineResult` схему для зберігання шляхів до файлів.

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-151 | 🔲 | Розширити `PipelineResult` полями script_path, audio_path | `src/ytaimbot_ml/schemas.py` | S | T-002 | — |
| T-152 | 🔲 | Додати `_generate_script()` стадію у Pipeline | `modules/orchestrator.py` | L | T-125, T-008 | — |
| T-153 | 🔲 | Додати `_synthesize_audio()` стадію у Pipeline | `modules/orchestrator.py` | L | T-114, T-152 | — |
| T-154 | 🔲 | Зберігати Script та audio path у PipelineResult | `modules/orchestrator.py` | M | T-151, T-152 | — |
| T-155 | 🔲 | Додати `OLLAMA_MODEL`, `OLLAMA_URL` до .env.example | `.env.example` | S | T-083 | — |
| T-156 | 🔲 | Додати `TTS_LANGUAGE`, `TTS_GENDER`, `USE_GPU` до .env.example | `.env.example` | S | T-100 | — |
| T-157 | 🔲 | Оновити docker-compose.yml з новими env vars | `docker-compose.yml` | S | T-155, T-156 | — |
| T-158 | 🔲 | Написати інтеграційні тести Phase 2 Pipeline | `tests/test_orchestrator.py` | L | T-152, T-153 | — |
| T-159 | 🔲 | Запустити `pytest -q --tb=short` → всі зелені | CI | S | T-158 | — |
| T-160 | 🔲 | Перевірити coverage ≥ 80% для нових модулів | CI | S | T-159 | — |

**Acceptance для PHASE 2 (загалом):**
- [ ] LLM генерує скрипти ≥ 500 слів (з mock Ollama)
- [ ] Edge-TTS → Coqui fallback chain працює
- [ ] Детермінізм: однаковий seed → однаковий скрипт
- [ ] Шаблони обираються через cosine similarity
- [ ] Pipeline зберігає `script_path` та `audio_path` у PipelineResult
- [ ] `pytest -q` → всі тести зелені
- [ ] Жодних реальних HTTP/LLM/TTS викликів у тестах

---

═══════════════════════════════════════════════════════════════════
## 📽️ PHASE 3: VIDEO ASSEMBLY + SEO — 🔲 PENDING (залежить P2)
═══════════════════════════════════════════════════════════════════

**Ціль:** Збірка фінальних відео, генерація мініатюр та SEO оптимізація метаданих.
**Тиждень:** 6–7 | **Пріоритет:** 🔴 Critical
**Залежності:** Phase 3 → Phase 2 повністю ✅

**Алгоритми в цій фазі:**
- **FFmpeg Pipeline:** DAG обробки медіа (аудіо + відео) → `O(frames × resolution)`
- **Subtitle Alignment:** Dynamic Time Warping (DTW) для синхронізації → `O(n×m)`
- **Keyword Expansion:** BFS по графу суміжних слів (Google Autocomplete) → `O(V+E)`
- **CTR Scoring:** Weighted sum з нормалізацією → `O(n_features)`
- **Image Composition:** Layer-based rendering (Z-order stack) → `O(pixels)`

---

### 📌 EPIC 3.1 — Video Assembler (MoviePy)

> **AI агенте:** MoviePy обгортає FFmpeg. Встанови FFmpeg у Dockerfile.
> Ціль: 1080p, 30fps, h.264 кодек, ~5–10 хв тривалість.
> Вхід: audio .mp3 + список background images/clips.
> Вихід: фінальний .mp4 у `YTAIMBOT_DATA_DIR/videos/`.

**Алгоритм збірки відео (DAG):**
```
VideoDAG:
  nodes:
    - AudioClip(audio_path)           → node A
    - ImageSequenceClip(images, fps)  → node B
    - SubtitleClip(srt_path)          → node C (overlay)

  edges:
    A → CompositeVideoClip([B, C])    → node D
    D → .write_videofile(output)      → node E (кінцевий)

  Складність: O(duration × fps × resolution_pixels)
  Memory: O(batch_frames) — обробляємо батчами, не весь відеофайл
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-161 | 🔲 | Додати `moviepy` до pyproject.toml | `pyproject.toml` | S | T-001 | — |
| T-162 | 🔲 | Визначити `VideoAssembler` ABC у base.py | `modules/adapters/base.py` | S | T-006 | — |
| T-163 | 🔲 | Створити `modules/video/` пакет | `modules/video/__init__.py` | S | T-008 | — |
| T-164 | 🔲 | Реалізувати `MoviePyAssembler` клас | `modules/video/assembler.py` | L | T-162, T-163 | — |
| T-165 | 🔲 | Реалізувати `assemble(audio_path, images, srt_path)` → Path | `modules/video/assembler.py` | XL | T-164 | — |
| T-166 | 🔲 | Реалізувати конфігурацію: resolution (1080p), fps (30), codec (h264) | `modules/video/assembler.py` | M | T-164 | — |
| T-167 | 🔲 | Реалізувати subtitle overlay (TextClip поверх відео) | `modules/video/assembler.py` | L | T-165 | — |
| T-168 | 🔲 | Реалізувати batch frame processing (уникати OOM на 4GB RAM) | `modules/video/assembler.py` | L | T-165 | — |
| T-169 | 🔲 | Зберігати вихідний файл у `YTAIMBOT_DATA_DIR/videos/` | `modules/video/assembler.py` | S | T-165 | — |
| T-170 | 🔲 | Додати FFmpeg до Dockerfile (apt-get install ffmpeg) | `Dockerfile` | S | T-014 | — |
| T-171 | 🔲 | Написати тести (mock MoviePy, не генерувати реальне відео) | `tests/test_video_assembler.py` | M | T-164 | — |
| T-172 | 🔲 | Тест: assemble() повертає валідний шлях до .mp4 | `tests/test_video_assembler.py` | S | T-171 | — |
| T-173 | 🔲 | Тест: вихідний файл у правильній директорії | `tests/test_video_assembler.py` | S | T-171 | — |
| T-174 | 🔲 | Тест: без subtitle файлу → відео без субтитрів (не crash) | `tests/test_video_assembler.py` | M | T-171 | — |
| T-175 | 🔲 | Тест: конфігурація resolution/fps читається з env vars | `tests/test_video_assembler.py` | S | T-171 | — |

**Acceptance для EPIC 3.1:**
- [ ] Реалізує `VideoAssembler` ABC
- [ ] Вихід: 1080p, 30fps, h.264, ≤500MB
- [ ] Batch processing для економії RAM (≤2GB використання)
- [ ] Відео без реальної генерації у тестах

---

### 📌 EPIC 3.2 — Thumbnail Generator (Pillow)

> **AI агенте:** YouTube thumbnail = 1280×720px, ≤2MB, JPEG або PNG.
> Максимальний CTR досягається: великий текст, яскравий фон, контрастні кольори.
> Алгоритм: Layer Stack (Z-order) → background → gradient → text → emoji/icon.

**Алгоритм генерації thumbnail (Layer Stack):**
```
ThumbnailGenerator.generate(title, color_scheme) → Image:

  layers (знизу вгору, Z-order):
    0. Background color fill                    → O(W×H)
    1. Gradient overlay (top-bottom or radial)  → O(W×H)
    2. Background image (if provided, resize)   → O(W×H)
    3. Semi-transparent overlay (readability)   → O(W×H)
    4. Title text (bold, large, centered)       → O(len(title))
    5. Channel branding (bottom-right corner)   → O(small_region)

  Flatten: Image.alpha_composite(layers) → final 1280×720 JPEG
  Складність: O(W × H × n_layers) = O(921,600 × 5) ≈ O(4.6M ops)
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-176 | 🔲 | Додати `Pillow` до pyproject.toml | `pyproject.toml` | S | T-001 | — |
| T-177 | 🔲 | Реалізувати `ThumbnailGenerator` клас | `modules/video/thumbnail.py` | M | T-163 | — |
| T-178 | 🔲 | Реалізувати `generate(title, subtitle, color_scheme)` → Path | `modules/video/thumbnail.py` | L | T-177 | — |
| T-179 | 🔲 | Реалізувати Layer Stack rendering (background → gradient → text) | `modules/video/thumbnail.py` | L | T-178 | — |
| T-180 | 🔲 | Реалізувати `ColorScheme` dataclass (≥5 схем: dark/light/vibrant/pro/minimal) | `modules/video/thumbnail.py` | M | T-177 | — |
| T-181 | 🔲 | Реалізувати auto font sizing (заголовок займає 60-80% ширини) | `modules/video/thumbnail.py` | M | T-178 | — |
| T-182 | 🔲 | Реалізувати збереження як JPEG (якість 95, ≤2MB) | `modules/video/thumbnail.py` | S | T-178 | — |
| T-183 | 🔲 | Написати тести для ThumbnailGenerator | `tests/test_thumbnail.py` | M | T-177 | — |
| T-184 | 🔲 | Тест: вихід — 1280×720 пікселів | `tests/test_thumbnail.py` | S | T-183 | — |
| T-185 | 🔲 | Тест: розмір файлу ≤ 2MB | `tests/test_thumbnail.py` | S | T-183 | — |
| T-186 | 🔲 | Тест: title присутній у зображенні (OCR-free перевірка через mock) | `tests/test_thumbnail.py` | S | T-183 | — |
| T-187 | 🔲 | Тест: всі 5 ColorScheme генерують без помилок | `tests/test_thumbnail.py` | M | T-183 | — |

---

### 📌 EPIC 3.3 — Subtitle Generator (SRT формат)

> **AI агенте:** SRT файл = субтитри для YouTube та burn-in у відео.
> Алгоритм синхронізації: рівномірний розподіл слів по часу аудіо.
> Формат SRT: `sequence\ntimecode --> timecode\ntext\n\n`
> Точність: ±150ms (достатньо для авто-generated контенту).

**Алгоритм генерації SRT (Sliding Window):**
```
generate_srt(script: str, audio_duration: float) -> str:
    """
    Рівномірний розподіл слів по часовій осі.
    Sliding window: 8-12 слів на субтитр блок.
    Складність: O(n_words)
    """
    words = script.split()          # O(n)
    total_words = len(words)
    words_per_second = total_words / audio_duration
    window_size = 10                 # слів на блок

    blocks = []
    for i in range(0, total_words, window_size):
        chunk = words[i:i+window_size]         # O(window_size)
        start_time = i / words_per_second
        end_time = (i + window_size) / words_per_second
        blocks.append(SRTBlock(i//window_size+1, start_time, end_time, " ".join(chunk)))

    return "\n\n".join(block.to_srt() for block in blocks)
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-188 | 🔲 | Реалізувати `SubtitleGenerator` клас | `modules/video/subtitles.py` | M | T-163 | — |
| T-189 | 🔲 | Реалізувати `SRTBlock` dataclass | `modules/video/subtitles.py` | S | T-188 | — |
| T-190 | 🔲 | Реалізувати `generate_srt(script, audio_duration)` → str | `modules/video/subtitles.py` | L | T-188 | — |
| T-191 | 🔲 | Реалізувати `save_srt(content, output_path)` → Path | `modules/video/subtitles.py` | S | T-188 | — |
| T-192 | 🔲 | Реалізувати `format_timecode(seconds)` → "HH:MM:SS,mmm" | `modules/video/subtitles.py` | M | T-188 | — |
| T-193 | 🔲 | Реалізувати sliding window розмір через env var `SUBTITLE_WORDS_PER_BLOCK` | `modules/video/subtitles.py` | S | T-190 | — |
| T-194 | 🔲 | Написати тести для SubtitleGenerator | `tests/test_subtitles.py` | M | T-188 | — |
| T-195 | 🔲 | Тест: SRT формат валідний (sequence, timecode, text) | `tests/test_subtitles.py` | M | T-194 | — |
| T-196 | 🔲 | Тест: timecode не перевищує audio_duration | `tests/test_subtitles.py` | S | T-194 | — |
| T-197 | 🔲 | Тест: всі слова скрипту присутні у SRT | `tests/test_subtitles.py` | M | T-194 | — |
| T-198 | 🔲 | Тест: порожній скрипт → порожній SRT (не crash) | `tests/test_subtitles.py` | S | T-194 | — |

---

### 📌 EPIC 3.4 — SEO Optimizer (розширення ключових слів)

> **AI агенте:** Google Autocomplete API — безкоштовно, без API ключа.
> URL: `https://suggestqueries.google.com/complete/search?client=youtube&q={keyword}`
> Алгоритм: BFS по графу суміжних слів (2 рівні глибини = достатньо).
> Дедублікація через set(). Сортування за relevance score.

**Алгоритм BFS для keyword expansion:**
```
expand_keywords(seed_keywords: list[str], depth=2) -> list[str]:
    """
    BFS по графу суміжних ключових слів.
    Вузол = keyword, ребро = "Google пропонує цей keyword разом"
    Складність: O(V + E) де V = keywords, E = suggestions
    """
    visited: set[str] = set(seed_keywords)
    queue: deque[tuple[str, int]] = deque([(k, 0) for k in seed_keywords])
    result: list[str] = []

    while queue:
        keyword, level = queue.popleft()         # O(1)
        if level >= depth:
            continue
        suggestions = autocomplete(keyword)       # HTTP call
        for s in suggestions:
            if s not in visited:
                visited.add(s)                   # O(1) avg
                queue.append((s, level + 1))     # O(1)
                result.append(s)

    return sorted(result, key=relevance_score, reverse=True)  # O(n log n)
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-199 | 🔲 | Створити `src/ytaimbot_ml/seo/` пакет | `src/ytaimbot_ml/seo/__init__.py` | S | T-003 | — |
| T-200 | 🔲 | Реалізувати `SEOOptimizer` клас | `src/ytaimbot_ml/seo/optimizer.py` | M | T-199 | — |
| T-201 | 🔲 | Реалізувати `expand_keywords(seeds, depth=2)` → list[str] (BFS) | `src/ytaimbot_ml/seo/optimizer.py` | L | T-200 | — |
| T-202 | 🔲 | Реалізувати `_autocomplete(keyword)` → list[str] (Google Suggest) | `src/ytaimbot_ml/seo/optimizer.py` | M | T-200 | — |
| T-203 | 🔲 | Реалізувати `relevance_score(keyword, seed)` → float | `src/ytaimbot_ml/seo/optimizer.py` | M | T-200 | — |
| T-204 | 🔲 | Реалізувати `deduplicate(keywords)` → list[str] (set + order) | `src/ytaimbot_ml/seo/optimizer.py` | S | T-200 | — |
| T-205 | 🔲 | Додати `@retry` до autocomplete HTTP запитів | `src/ytaimbot_ml/seo/optimizer.py` | S | T-017, T-202 | — |
| T-206 | 🔲 | Реалізувати результат ≥ 10 keywords (або raise якщо неможливо) | `src/ytaimbot_ml/seo/optimizer.py` | S | T-201 | — |
| T-207 | 🔲 | Написати тести для SEOOptimizer (mock HTTP) | `tests/test_seo_optimizer.py` | M | T-200 | — |
| T-208 | 🔲 | Тест: expand_keywords повертає ≥ 10 keywords | `tests/test_seo_optimizer.py` | S | T-207 | — |
| T-209 | 🔲 | Тест: дублікати видаляються | `tests/test_seo_optimizer.py` | S | T-207 | — |
| T-210 | 🔲 | Тест: BFS depth=2 → не більше 2 рівнів розширення | `tests/test_seo_optimizer.py` | M | T-207 | — |
| T-211 | 🔲 | Тест: HTTP помилка → порожній список (не crash) | `tests/test_seo_optimizer.py` | M | T-207 | — |
| T-212 | 🔲 | Тест: жодних реальних HTTP запитів у тестах | `tests/test_seo_optimizer.py` | S | T-207 | — |

---

### 📌 EPIC 3.5 — Title Generator (CTR-оптимізований)

> **AI агенте:** CTR-оптимізовані заголовки = формула: [Число/Питання] + [Power Word] + [Конкретика].
> Довжина: 40–60 символів (оптимум для YouTube).
> A/B варіанти: генеруємо 3 варіанти, зберігаємо всі для майбутнього тесту.

**Алгоритм CTR scoring:**
```
ctr_score(title: str) -> float:
    """
    Зважена сума ознак для передбачення CTR.
    Складність: O(n_features) — константна для заголовку

    Features та їх ваги (з аналізу YouTube даних):
    """
    features = {
        "has_number":     0.20,  # "5 способів", "Top 10"
        "has_question":   0.15,  # "Як?", "Чому?"
        "has_power_word": 0.25,  # "Секрет", "Помилка", "Безкоштовно"
        "length_optimal": 0.20,  # 40-60 символів
        "has_keyword":    0.20,  # seed keyword присутній
    }
    score = sum(
        weight * float(check_feature(title, feat))
        for feat, weight in features.items()
    )  # O(n_features) = O(5) = O(1)
    return score  # 0.0 – 1.0
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-213 | 🔲 | Реалізувати `TitleGenerator` клас | `src/ytaimbot_ml/seo/title_generator.py` | M | T-199 | — |
| T-214 | 🔲 | Реалізувати `POWER_WORDS` константу (≥50 слів для UK/EN/RU) | `src/ytaimbot_ml/seo/title_generator.py` | M | T-213 | — |
| T-215 | 🔲 | Реалізувати `generate_variants(plan, n=3)` → list[str] | `src/ytaimbot_ml/seo/title_generator.py` | L | T-213 | — |
| T-216 | 🔲 | Реалізувати `ctr_score(title)` → float [0.0, 1.0] | `src/ytaimbot_ml/seo/title_generator.py` | M | T-213 | — |
| T-217 | 🔲 | Реалізувати `select_best(variants)` → str (max ctr_score) | `src/ytaimbot_ml/seo/title_generator.py` | S | T-216 | — |
| T-218 | 🔲 | Реалізувати валідацію: довжина 40–60 символів (trim якщо довше) | `src/ytaimbot_ml/seo/title_generator.py` | S | T-213 | — |
| T-219 | 🔲 | Реалізувати зберігання всіх variants у PipelineResult (для A/B) | `src/ytaimbot_ml/seo/title_generator.py` | M | T-213 | — |
| T-220 | 🔲 | Написати тести для TitleGenerator | `tests/test_title_generator.py` | M | T-213 | — |
| T-221 | 🔲 | Тест: generate_variants() повертає 3 унікальних варіанти | `tests/test_title_generator.py` | S | T-220 | — |
| T-222 | 🔲 | Тест: кожен title 40–60 символів | `tests/test_title_generator.py` | S | T-220 | — |
| T-223 | 🔲 | Тест: ctr_score(title з числом + power word) > 0.6 | `tests/test_title_generator.py` | M | T-220 | — |
| T-224 | 🔲 | Тест: детермінізм — seed → однакові variants | `tests/test_title_generator.py` | M | T-220 | — |
| T-225 | 🔲 | Тест: seed keyword присутній хоча б у 2 з 3 варіантів | `tests/test_title_generator.py` | M | T-220 | — |

---

### 📌 EPIC 3.6 — Інтеграція Phase 3 в Pipeline

> **AI агенте:** Розширити `Pipeline` новими стадіями:
> **Stage 10:** `_assemble_video()` — MoviePy збірка
> **Stage 11:** `_generate_thumbnail()` — Pillow thumbnail
> **Stage 12:** `_optimize_seo()` — keyword expansion + title generation
> Оновити `PipelineResult` для зберігання всіх шляхів та SEO даних.

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-226 | 🔲 | Розширити `PipelineResult` полями video_path, thumbnail_path, seo_keywords, title_variants | `src/ytaimbot_ml/schemas.py` | S | T-151 | — |
| T-227 | 🔲 | Додати `_assemble_video()` стадію у Pipeline | `modules/orchestrator.py` | L | T-165, T-153 | — |
| T-228 | 🔲 | Додати `_generate_thumbnail()` стадію у Pipeline | `modules/orchestrator.py` | M | T-178, T-227 | — |
| T-229 | 🔲 | Додати `_optimize_seo()` стадію у Pipeline | `modules/orchestrator.py` | M | T-201, T-215 | — |
| T-230 | 🔲 | Додати `_generate_subtitles()` стадію у Pipeline | `modules/orchestrator.py` | M | T-190, T-153 | — |
| T-231 | 🔲 | Додати `VIDEO_RESOLUTION`, `VIDEO_FPS`, `VIDEO_CODEC` до .env.example | `.env.example` | S | T-166 | — |
| T-232 | 🔲 | Додати `SUBTITLE_WORDS_PER_BLOCK` до .env.example | `.env.example` | S | T-193 | — |
| T-233 | 🔲 | Додати `SEO_EXPANSION_DEPTH`, `SEO_MIN_KEYWORDS` до .env.example | `.env.example` | S | T-201 | — |
| T-234 | 🔲 | Оновити docker-compose.yml з новими env vars | `docker-compose.yml` | S | T-231, T-233 | — |
| T-235 | 🔲 | Написати інтеграційні тести Phase 3 Pipeline (всі mock) | `tests/test_orchestrator.py` | L | T-227, T-229 | — |
| T-236 | 🔲 | Тест: Pipeline повертає PipelineResult з video_path | `tests/test_orchestrator.py` | M | T-235 | — |
| T-237 | 🔲 | Тест: Pipeline повертає PipelineResult з thumbnail_path | `tests/test_orchestrator.py` | M | T-235 | — |
| T-238 | 🔲 | Тест: Pipeline повертає PipelineResult з ≥10 seo_keywords | `tests/test_orchestrator.py` | M | T-235 | — |
| T-239 | 🔲 | Запустити `pytest -q --tb=short` → всі зелені | CI | S | T-238 | — |
| T-240 | 🔲 | Перевірити coverage ≥ 80% для нових модулів | CI | S | T-239 | — |

**Acceptance для PHASE 3 (загалом):**
- [ ] Pipeline генерує .mp4 (1080p, 30fps) через MockAssembler у тестах
- [ ] Thumbnail 1280×720px, ≤2MB
- [ ] SRT субтитри валідні та синхронізовані
- [ ] SEO: ≥10 keywords після BFS expansion
- [ ] Title variants: 3 унікальних, 40–60 символів, CTR score ≥ 0.5
- [ ] `pytest -q` → всі тести зелені
- [ ] `docker compose build` → успішно (FFmpeg встановлено)

---

═══════════════════════════════════════════════════════════════════
## 🚀 PHASE 4: PUBLISHING PIPELINE — 🔲 PENDING (залежить P3)
═══════════════════════════════════════════════════════════════════

**Ціль:** Завантаження відео на YouTube з compliance-gate, OAuth2 та ручною перевіркою перших 50 відео.
**Тиждень:** 8–9 | **Пріоритет:** 🔴 Critical
**Залежності:** Phase 4 → Phase 3 повністю ✅

**Алгоритми в цій фазі:**
- **Rate Limiter:** Token Bucket алгоритм → `O(1)` per request
- **Upload Queue:** Priority Queue (min-heap за scheduled_at) → `O(log n)` enqueue/dequeue
- **Cosine Similarity Gate:** Векторне порівняння контенту → `O(vocab × n_archive)`
- **Audit Log:** Append-only структура (WAL-like) → `O(1)` write, `O(n)` read
- **OAuth Token Store:** Encrypted key-value store → `O(1)` get/set

---

### 📌 EPIC 4.1 — YouTube Publisher Adapter

> **AI агенте:** Реалізує `PublisherAdapter` ABC з `modules/adapters/base.py`.
> **КРИТИЧНО:** Перші 50 відео завжди UNLISTED — ніколи PUBLIC автоматично.
> AI disclosure flag обов'язковий у metadata (selfDeclaredMadeForKids=False, hasCustomThumbnail=True).
> Rate limit: max 1 upload/6 хвилин (YouTube API quota) через Token Bucket.

**Token Bucket Rate Limiter:**
```python
class TokenBucket:
    """
    Алгоритм: Token Bucket
    Складність: O(1) per check/consume
    capacity=10 токенів, refill=1 токен/6 хв

    tokens: float  (поточна кількість)
    last_refill: float  (timestamp)

    consume(tokens=1) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        # поповнити токени (але не більше capacity)
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.refill_rate
        )
        self.last_refill = now
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True   # дозволено
        return False      # blocked, чекай
    """
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-241 | 🔲 | Додати `google-auth`, `google-auth-oauthlib` до pyproject.toml | `pyproject.toml` | S | T-001 | — |
| T-242 | 🔲 | Реалізувати `TokenBucket` клас (rate limiter) | `modules/adapters/youtube_publisher.py` | M | T-006 | — |
| T-243 | 🔲 | Реалізувати `YouTubePublisherAdapter` клас | `modules/adapters/youtube_publisher.py` | L | T-006, T-242 | — |
| T-244 | 🔲 | Реалізувати `publish(plan, video_path, thumbnail_path)` → str (video_id) | `modules/adapters/youtube_publisher.py` | XL | T-243 | — |
| T-245 | 🔲 | Примусово встановити `privacyStatus="unlisted"` для перших 50 відео | `modules/adapters/youtube_publisher.py` | M | T-244 | — |
| T-246 | 🔲 | Додати AI disclosure до metadata (`isMadeForKids=False`, опис з позначкою) | `modules/adapters/youtube_publisher.py` | M | T-244 | — |
| T-247 | 🔲 | Реалізувати завантаження thumbnail після upload | `modules/adapters/youtube_publisher.py` | M | T-244 | — |
| T-248 | 🔲 | Інтегрувати `TokenBucket` — блокувати якщо rate limit досягнуто | `modules/adapters/youtube_publisher.py` | M | T-242, T-244 | — |
| T-249 | 🔲 | Реалізувати `upload_count` лічильник (persist у storage) | `modules/adapters/youtube_publisher.py` | M | T-244 | — |
| T-250 | 🔲 | Логувати кожен upload: video_id, title, privacy, timestamp (INFO) | `modules/adapters/youtube_publisher.py` | S | T-244 | — |
| T-251 | 🔲 | Написати тести (mock googleapiclient.discovery.build) | `tests/test_publisher.py` | M | T-243 | — |
| T-252 | 🔲 | Тест: publish() повертає непорожній video_id string | `tests/test_publisher.py` | S | T-251 | — |
| T-253 | 🔲 | Тест: перші 50 відео → завжди privacyStatus="unlisted" | `tests/test_publisher.py` | M | T-251 | — |
| T-254 | 🔲 | Тест: upload_count > 50 → може бути "public" (якщо явно задано) | `tests/test_publisher.py` | M | T-251 | — |
| T-255 | 🔲 | Тест: TokenBucket блокує при перевищенні rate limit | `tests/test_publisher.py` | M | T-251 | — |
| T-256 | 🔲 | Тест: AI disclosure присутній у description | `tests/test_publisher.py` | S | T-251 | — |

**Acceptance для EPIC 4.1:**
- [ ] Реалізує `PublisherAdapter` ABC
- [ ] Перші 50 відео UNLISTED (протестовано)
- [ ] AI disclosure у кожному відео
- [ ] Rate limiter: max 1 upload/6 хв (Token Bucket)
- [ ] Жодних реальних YouTube API викликів у тестах

---

### 📌 EPIC 4.2 — YouTube OAuth2 Authentication

> **AI агенте:** OAuth2 токени зберігаємо у зашифрованому файлі, НЕ у env vars напряму.
> Шлях: `YTAIMBOT_DATA_DIR/credentials/youtube_token.json` (у .gitignore).
> Auto-refresh: перевіряти expiry перед кожним API викликом.
> Підтримувати два режими: `user_oauth` (для channel owner) та `service_account` (для автоматизації).

**Алгоритм auto-refresh токену:**
```python
def get_valid_credentials(token_path: Path) -> Credentials:
    """
    Складність: O(1) — константна кількість перевірок
    """
    creds = load_credentials(token_path)        # O(1) file read
    if creds and creds.valid:
        return creds                            # токен валідний
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())                # auto-refresh
        save_credentials(creds, token_path)     # persist
        return creds
    # Токен відсутній або невалідний → flow
    flow = InstalledAppFlow.from_client_secrets_file(...)
    creds = flow.run_local_server(port=0)
    save_credentials(creds, token_path)
    return creds
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-257 | 🔲 | Реалізувати `YouTubeAuthManager` клас | `modules/adapters/youtube_auth.py` | L | T-241 | — |
| T-258 | 🔲 | Реалізувати `get_valid_credentials(token_path)` → Credentials | `modules/adapters/youtube_auth.py` | L | T-257 | — |
| T-259 | 🔲 | Реалізувати auto-refresh токену (перевірка expiry) | `modules/adapters/youtube_auth.py` | M | T-258 | — |
| T-260 | 🔲 | Реалізувати `save_credentials(creds, path)` — зашифровано | `modules/adapters/youtube_auth.py` | M | T-257 | — |
| T-261 | 🔲 | Реалізувати `load_credentials(path)` → Credentials | None | `modules/adapters/youtube_auth.py` | M | T-257 | — |
| T-262 | 🔲 | Реалізувати `service_account_auth(key_path)` → Credentials | `modules/adapters/youtube_auth.py` | M | T-257 | — |
| T-263 | 🔲 | Додати `YOUTUBE_CLIENT_SECRET_PATH` до .env.example | `.env.example` | S | T-257 | — |
| T-264 | 🔲 | Додати `youtube_token.json` та `client_secret*.json` до .gitignore | `.gitignore` | S | T-257 | — |
| T-265 | 🔲 | Написати тести для YouTubeAuthManager (mock google.oauth2) | `tests/test_youtube_auth.py` | M | T-257 | — |
| T-266 | 🔲 | Тест: валідний токен → повертається без refresh | `tests/test_youtube_auth.py` | S | T-265 | — |
| T-267 | 🔲 | Тест: expired токен → auto-refresh виконується | `tests/test_youtube_auth.py` | M | T-265 | — |
| T-268 | 🔲 | Тест: credentials НЕ логуються (перевірка caplog) | `tests/test_youtube_auth.py` | M | T-265 | — |

---

### 📌 EPIC 4.3 — Cosine Similarity Compliance Gate

> **AI агенте:** Перед публікацією перевіряємо схожість нового контенту з архівом.
> Якщо cosine similarity > 0.85 → блокуємо (дублікат або plagiarism ризик).
> Алгоритм: TF-IDF векторизація → cosine similarity → O(vocab × n_archive).
> Зберігаємо хеш контенту у storage для майбутніх перевірок.

**Алгоритм Cosine Similarity Gate:**
```python
class SimilarityGate:
    """
    Структура даних: dict[content_hash → TF-IDF vector]
    Складність пошуку: O(vocab_size × n_archived_videos)
    Оптимізація: можна використати ANN (approximate nearest neighbor)
    для великих архівів (Phase 6+)
    """
    THRESHOLD = 0.85  # блокуємо якщо similarity > 85%

    def check(self, new_script: str, archive: list[str]) -> SimilarityReport:
        new_vec = tfidf_vectorize(new_script)       # O(vocab)
        scores = []
        for archived in archive:
            arch_vec = tfidf_vectorize(archived)    # O(vocab)
            sim = cosine_sim(new_vec, arch_vec)     # O(vocab)
            scores.append(sim)
        max_sim = max(scores) if scores else 0.0    # O(n_archive)
        return SimilarityReport(
            score=max_sim,
            decision="block" if max_sim > self.THRESHOLD else "pass",
            content_hash=sha256(new_script)
        )
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-269 | 🔲 | Створити `SimilarityReport` dataclass у schemas.py | `src/ytaimbot_ml/schemas.py` | S | T-002 | — |
| T-270 | 🔲 | Реалізувати `SimilarityGate` клас | `src/ytaimbot_ml/quality/similarity_gate.py` | L | T-004, T-269 | — |
| T-271 | 🔲 | Реалізувати `tfidf_vectorize(text)` → np.ndarray | `src/ytaimbot_ml/quality/similarity_gate.py` | M | T-270 | — |
| T-272 | 🔲 | Реалізувати `cosine_sim(v1, v2)` → float [0.0, 1.0] | `src/ytaimbot_ml/quality/similarity_gate.py` | S | T-270 | — |
| T-273 | 🔲 | Реалізувати `check(new_script, archive)` → SimilarityReport | `src/ytaimbot_ml/quality/similarity_gate.py` | L | T-270 | — |
| T-274 | 🔲 | Реалізувати `content_hash(text)` → str (SHA-256) | `src/ytaimbot_ml/quality/similarity_gate.py` | S | T-270 | — |
| T-275 | 🔲 | Інтегрувати SimilarityGate у Pipeline (перед BayesGate) | `modules/orchestrator.py` | M | T-270, T-008 | — |
| T-276 | 🔲 | Написати тести для SimilarityGate | `tests/test_similarity_gate.py` | M | T-270 | — |
| T-277 | 🔲 | Тест: ідентичний текст → similarity = 1.0 → "block" | `tests/test_similarity_gate.py` | S | T-276 | — |
| T-278 | 🔲 | Тест: абсолютно різний текст → similarity < 0.1 → "pass" | `tests/test_similarity_gate.py` | S | T-276 | — |
| T-279 | 🔲 | Тест: порожній архів → "pass" (немає з чим порівнювати) | `tests/test_similarity_gate.py` | S | T-276 | — |
| T-280 | 🔲 | Тест: content_hash — однаковий текст → однаковий hash | `tests/test_similarity_gate.py` | S | T-276 | — |

---

### 📌 EPIC 4.4 — Manual Review CLI (перші 50 відео)

> **AI агенте:** Перші 50 відео вимагають ручної перевірки оператором перед публікацією.
> CLI показує: заголовок, thumbnail path, compliance report, similarity score.
> Оператор вводить: `a` (approve → public) або `r` (reject → archive).
> Рішення зберігаємо в audit log (append-only JSON Lines файл).

**Структура даних Audit Log (Append-Only):**
```python
# Формат: JSON Lines (кожен рядок — один JSON об'єкт)
# Структура нагадує WAL (Write-Ahead Log)
# O(1) write (append), O(n) read (full scan), O(log n) якщо індексовано

AuditEntry = {
    "timestamp": "2026-03-10T19:00:00Z",
    "video_id": "dQw4w9WgXcQ",
    "title": "Top 5 Python Tips 2026",
    "operator": "human|ai_agent",
    "decision": "approve|reject",
    "compliance_score": 0.92,
    "similarity_score": 0.12,
    "content_hash": "sha256:abc123...",
    "reason": "optional reject reason"
}
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-281 | 🔲 | Створити `modules/dashboard/` пакет | `modules/dashboard/__init__.py` | S | T-008 | — |
| T-282 | 🔲 | Реалізувати `AuditLog` клас (append-only JSON Lines) | `modules/dashboard/audit_log.py` | M | T-281 | — |
| T-283 | 🔲 | Реалізувати `append(entry: AuditEntry)` → None (O(1) write) | `modules/dashboard/audit_log.py` | M | T-282 | — |
| T-284 | 🔲 | Реалізувати `read_all()` → list[AuditEntry] (O(n) read) | `modules/dashboard/audit_log.py` | S | T-282 | — |
| T-285 | 🔲 | Реалізувати `ManualReviewCLI` клас | `modules/dashboard/manual_review.py` | L | T-282 | — |
| T-286 | 🔲 | Реалізувати `review(pipeline_result)` → Literal["approve","reject"] | `modules/dashboard/manual_review.py` | L | T-285 | — |
| T-287 | 🔲 | Відображати: заголовок, thumbnail_path, Bayes score, similarity score | `modules/dashboard/manual_review.py` | M | T-285 | — |
| T-288 | 🔲 | Реалізувати автоматичне схвалення якщо `upload_count >= 50` | `modules/dashboard/manual_review.py` | M | T-285 | — |
| T-289 | 🔲 | Записувати кожне рішення в AuditLog | `modules/dashboard/manual_review.py` | M | T-283, T-286 | — |
| T-290 | 🔲 | Написати тести для ManualReviewCLI (mock stdin/stdout) | `tests/test_manual_review.py` | M | T-285 | — |
| T-291 | 🔲 | Тест: approve рішення → AuditLog містить "approve" запис | `tests/test_manual_review.py` | M | T-290 | — |
| T-292 | 🔲 | Тест: upload_count >= 50 → автоматичне "approve" без input | `tests/test_manual_review.py` | M | T-290 | — |
| T-293 | 🔲 | Тест: AuditLog файл — кожен рядок валідний JSON | `tests/test_manual_review.py` | M | T-290 | — |

---

### 📌 EPIC 4.5 — Upload Scheduler (черга завантажень)

> **AI агенте:** Scheduler — Priority Queue (min-heap) за `scheduled_at` timestamp.
> Обмеження: 1 відео/день (конфігурується через `MAX_UPLOADS_PER_DAY`).
> Persistent queue: зберігаємо у SQLite (відновлення після рестарту).
> Scheduler запускається як окремий thread (не блокує основний pipeline).

**Алгоритм Upload Queue (Min-Heap Priority Queue):**
```python
import heapq

class UploadScheduler:
    """
    Min-heap за scheduled_at timestamp.
    Складність: O(log n) push/pop, O(1) peek

    heap: list[tuple[float, UploadJob]]
    # (timestamp, job) → heapq використовує перший елемент для порівняння
    """
    def schedule(self, job: UploadJob, at: datetime) -> None:
        heapq.heappush(self._heap, (at.timestamp(), job))  # O(log n)

    def next_due(self) -> UploadJob | None:
        if not self._heap:
            return None
        ts, job = self._heap[0]   # peek O(1)
        if ts <= time.time():
            heapq.heappop(self._heap)  # O(log n)
            return job
        return None  # ще рано
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-294 | 🔲 | Створити `UploadJob` dataclass | `src/ytaimbot_ml/schemas.py` | S | T-002 | — |
| T-295 | 🔲 | Реалізувати `UploadScheduler` клас (min-heap) | `modules/scheduler.py` | L | T-294 | — |
| T-296 | 🔲 | Реалізувати `schedule(job, at)` → None (O(log n) push) | `modules/scheduler.py` | M | T-295 | — |
| T-297 | 🔲 | Реалізувати `next_due()` → UploadJob | None (O(1) peek) | `modules/scheduler.py` | M | T-295 | — |
| T-298 | 🔲 | Реалізувати `MAX_UPLOADS_PER_DAY` ліміт (env var, default=1) | `modules/scheduler.py` | M | T-295 | — |
| T-299 | 🔲 | Реалізувати persist queue у SQLite (відновлення після рестарту) | `modules/scheduler.py` | L | T-295 | — |
| T-300 | 🔲 | Написати тести для UploadScheduler | `tests/test_scheduler.py` | M | T-295 | — |
| T-301 | 🔲 | Тест: schedule + next_due → повертає job коли час прийшов | `tests/test_scheduler.py` | M | T-300 | — |
| T-302 | 🔲 | Тест: MAX_UPLOADS_PER_DAY=1 → другий upload блокується | `tests/test_scheduler.py` | M | T-300 | — |
| T-303 | 🔲 | Тест: queue відновлюється після перезапуску (persist) | `tests/test_scheduler.py` | L | T-300 | — |

---

### 📌 EPIC 4.6 — Повна інтеграція Phase 4 у Pipeline

> **AI агенте:** Фінальна інтеграція всіх компонентів Phase 4.
> Pipeline тепер повний: Trend → Script → Audio → Video → Gate → Review → Publish.
> Оновити `PipelineResult` з `video_id`, `published_at`, `audit_entry`.
> Dry-run режим залишається — у DRY_RUN всі ці кроки симулюються.

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-304 | 🔲 | Розширити `PipelineResult` полями video_id, published_at, audit_entry | `src/ytaimbot_ml/schemas.py` | S | T-226 | — |
| T-305 | 🔲 | Інтегрувати SimilarityGate у Pipeline (Stage перед Bayes) | `modules/orchestrator.py` | M | T-275 | — |
| T-306 | 🔲 | Інтегрувати ManualReviewCLI у Pipeline (після Gate) | `modules/orchestrator.py` | M | T-286 | — |
| T-307 | 🔲 | Інтегрувати UploadScheduler у Pipeline | `modules/orchestrator.py` | M | T-297 | — |
| T-308 | 🔲 | Додати `MAX_UPLOADS_PER_DAY`, `YOUTUBE_CLIENT_SECRET_PATH` до .env.example | `.env.example` | S | T-295, T-263 | — |
| T-309 | 🔲 | Написати E2E тест: повний pipeline від trend до published (всі mock) | `tests/test_e2e_pipeline.py` | XL | T-304, T-306 | — |
| T-310 | 🔲 | Запустити `pytest -q --tb=short` → всі зелені | CI | S | T-309 | — |

**Acceptance для PHASE 4 (загалом):**
- [ ] Перші 50 відео → UNLISTED + Manual Review
- [ ] AI disclosure у кожному відео обов'язковий
- [ ] SimilarityGate + BayesGate — обидва повинні пройти перед publish
- [ ] AuditLog: кожне рішення записано у JSON Lines
- [ ] Token Bucket: max 1 upload / 6 хвилин
- [ ] E2E тест: повний pipeline з усіма моками → зелений
- [ ] Dry-run: YTAIMBOT_DRY_RUN=true → жодного реального upload

---

═══════════════════════════════════════════════════════════════════
## 📊 PHASE 5: METRICS FEEDBACK LOOP — 🔲 PENDING (залежить P4)
═══════════════════════════════════════════════════════════════════

**Ціль:** Збір метрик реальних відео → навчання на успіхах → покращення майбутнього контенту.
**Тиждень:** 10–12 | **Пріоритет:** 🟠 High
**Залежності:** Phase 5 → Phase 4 повністю ✅ (потрібні реальні video_id)

**Алгоритми в цій фазі:**
- **Exponential Moving Average (EMA):** Оновлення trend scores → `O(1)` per update
- **Chi-Square Test:** A/B статистична значимість → `O(n_variants)`
- **SQLite Indexes:** B-Tree індекс для швидких запитів → `O(log n)` lookup
- **Time Series Aggregation:** Rolling window stats → `O(window_size)`
- **Rank Correlation (Spearman):** Порівняння передбачених vs реальних scores → `O(n log n)`

---

### 📌 EPIC 5.1 — SQLite Storage Schema

> **AI агенте:** Замінюємо `InMemoryStorage` на SQLite для persistence.
> Файл: `YTAIMBOT_DATA_DIR/ytaimbot.db`
> Всі запити через параметризовані prepared statements (захист від SQL injection).
> Migrations: простий version table, застосовуємо при запуску.

**Схема БД:**
```sql
-- Таблиця відео (головна)
CREATE TABLE IF NOT EXISTS videos (
    video_id     TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    script_hash  TEXT NOT NULL,           -- SHA-256
    published_at TEXT,                    -- ISO-8601
    privacy      TEXT DEFAULT 'unlisted', -- unlisted|public
    niche        TEXT,
    keywords     TEXT,                    -- JSON array
    created_at   TEXT DEFAULT (datetime('now'))
);

-- Метрики відео (one-to-many)
CREATE TABLE IF NOT EXISTS metrics (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id     TEXT REFERENCES videos(video_id),
    views        INTEGER DEFAULT 0,
    ctr          REAL DEFAULT 0.0,        -- 0.0 – 1.0
    retention_30s REAL DEFAULT 0.0,       -- 0.0 – 1.0
    rpm          REAL DEFAULT 0.0,        -- revenue per 1K views
    watch_time_h REAL DEFAULT 0.0,        -- годин
    collected_at TEXT DEFAULT (datetime('now')),
    UNIQUE(video_id, collected_at)        -- не дублювати
);

-- A/B тести
CREATE TABLE IF NOT EXISTS ab_tests (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id     TEXT REFERENCES videos(video_id),
    variant_type TEXT,                    -- 'title'|'thumbnail'
    variant_val  TEXT,
    ctr          REAL,
    sample_size  INTEGER DEFAULT 0,
    created_at   TEXT DEFAULT (datetime('now'))
);

-- Audit log (append-only)
CREATE TABLE IF NOT EXISTS audit_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id     TEXT,
    operator     TEXT,
    decision     TEXT,                    -- approve|reject
    reason       TEXT,
    content_hash TEXT,
    created_at   TEXT DEFAULT (datetime('now'))
);

-- Індекси для швидких запитів — B-Tree O(log n)
CREATE INDEX IF NOT EXISTS idx_metrics_video_id ON metrics(video_id);
CREATE INDEX IF NOT EXISTS idx_metrics_collected ON metrics(collected_at);
CREATE INDEX IF NOT EXISTS idx_videos_published ON videos(published_at);
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-311 | 🔲 | Реалізувати `SQLiteStorageAdapter` клас | `modules/adapters/sqlite_storage.py` | L | T-006 | — |
| T-312 | 🔲 | Реалізувати schema migration system (version table) | `modules/adapters/sqlite_storage.py` | M | T-311 | — |
| T-313 | 🔲 | Реалізувати `create_tables()` — DDL з вище | `modules/adapters/sqlite_storage.py` | M | T-311 | — |
| T-314 | 🔲 | Реалізувати `save_video(video)` → None (upsert) | `modules/adapters/sqlite_storage.py` | M | T-311 | — |
| T-315 | 🔲 | Реалізувати `save_metrics(metrics)` → None (UNIQUE constraint) | `modules/adapters/sqlite_storage.py` | M | T-311 | — |
| T-316 | 🔲 | Реалізувати `get_video(video_id)` → Video | None | `modules/adapters/sqlite_storage.py` | M | T-311 | — |
| T-317 | 🔲 | Реалізувати `get_top_videos(n=10, metric="rpm")` → list[Video] | `modules/adapters/sqlite_storage.py` | M | T-311 | — |
| T-318 | 🔲 | Реалізувати `get_all_scripts()` → list[str] (для SimilarityGate) | `modules/adapters/sqlite_storage.py` | M | T-311 | — |
| T-319 | 🔲 | Реалізувати `save_ab_test(ab_test)` та `get_ab_tests(video_id)` | `modules/adapters/sqlite_storage.py` | M | T-311 | — |
| T-320 | 🔲 | Замінити `InMemoryStorage` на `SQLiteStorageAdapter` у Pipeline | `modules/orchestrator.py` | M | T-311 | — |
| T-321 | 🔲 | Додати `STORAGE_BACKEND=sqlite` env var логіку у Pipeline | `modules/orchestrator.py` | S | T-320 | — |
| T-322 | 🔲 | Написати тести для SQLiteStorageAdapter (in-memory SQLite `:memory:`) | `tests/test_sqlite_storage.py` | M | T-311 | — |
| T-323 | 🔲 | Тест: save_video + get_video → roundtrip без втрати даних | `tests/test_sqlite_storage.py` | M | T-322 | — |
| T-324 | 🔲 | Тест: UNIQUE constraint на metrics → дублікат ігнорується | `tests/test_sqlite_storage.py` | M | T-322 | — |
| T-325 | 🔲 | Тест: migration → таблиці створюються при першому запуску | `tests/test_sqlite_storage.py` | M | T-322 | — |

---

### 📌 EPIC 5.2 — Metrics Collector (YouTube Analytics API)

> **AI агенте:** YouTube Analytics API — окремий API від Data API v3.
> Збираємо метрики через 48 годин після публікації (дані стабілізуються).
> Розклад: daily cron (через `schedule` бібліотеку або системний cron).
> Обов'язково: обробка відсутніх даних (нові відео можуть ще не мати метрик).

**Алгоритм збору метрик з повторними спробами:**
```python
MetricsCollector.collect(video_id: str, published_at: datetime) -> MetricsSnapshot:
    """
    Збираємо лише якщо відео > 48 годин (дані стабілізувалися)
    Складність: O(1) per video — один API запит
    """
    age = datetime.utcnow() - published_at
    if age < timedelta(hours=48):
        raise TooEarlyError(f"Video {video_id} is only {age.hours}h old")

    response = analytics_api.reports().query(
        ids=f"channel==MINE",
        startDate=published_at.date().isoformat(),
        endDate=date.today().isoformat(),
        metrics="views,estimatedRevenue,averageViewDuration,clickThroughRate",
        filters=f"video=={video_id}"
    ).execute()

    return MetricsSnapshot.from_api_response(response)
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-326 | 🔲 | Створити `MetricsSnapshot` dataclass у schemas.py | `src/ytaimbot_ml/schemas.py` | S | T-002 | — |
| T-327 | 🔲 | Реалізувати `MetricsCollector` клас | `modules/metrics_collector.py` | L | T-241, T-326 | — |
| T-328 | 🔲 | Реалізувати `collect(video_id, published_at)` → MetricsSnapshot | `modules/metrics_collector.py` | L | T-327 | — |
| T-329 | 🔲 | Реалізувати 48-годинну затримку (TooEarlyError) | `modules/metrics_collector.py` | M | T-328 | — |
| T-330 | 🔲 | Реалізувати `collect_all_pending()` → list[MetricsSnapshot] | `modules/metrics_collector.py` | M | T-327 | — |
| T-331 | 🔲 | Реалізувати збереження у SQLiteStorageAdapter | `modules/metrics_collector.py` | M | T-315, T-328 | — |
| T-332 | 🔲 | Реалізувати `@retry` для Analytics API викликів | `modules/metrics_collector.py` | S | T-017, T-328 | — |
| T-333 | 🔲 | Написати тести (mock googleapiclient Analytics) | `tests/test_metrics_collector.py` | M | T-327 | — |
| T-334 | 🔲 | Тест: collect() для відео < 48h → TooEarlyError | `tests/test_metrics_collector.py` | S | T-333 | — |
| T-335 | 🔲 | Тест: collect() повертає MetricsSnapshot з усіма полями | `tests/test_metrics_collector.py` | M | T-333 | — |
| T-336 | 🔲 | Тест: дані зберігаються у SQLite після collect() | `tests/test_metrics_collector.py` | M | T-333 | — |
| T-337 | 🔲 | Тест: жодних реальних API викликів у тестах | `tests/test_metrics_collector.py` | S | T-333 | — |

---

### 📌 EPIC 5.3 — Feedback Scorer (оновлення trend scores)

> **AI агенте:** FeedbackScorer використовує реальні метрики для коригування
> ваг TrendAnalyzer. Алгоритм: Exponential Moving Average (EMA) — плавне
> оновлення без різких стрибків. Safety bounds: зміна score ≤ ±20% за тиждень.

**Алгоритм EMA для оновлення scores:**
```python
class FeedbackScorer:
    """
    Exponential Moving Average для оновлення trend weights.
    Складність: O(n_trends) per update cycle

    EMA формула:
    new_weight = alpha * performance_signal + (1 - alpha) * old_weight

    де:
    alpha = 0.3  (learning rate — конфігурується)
    performance_signal = normalize(rpm * views * retention_30s)

    Safety bounds (запобігають перенавчанню):
    new_weight = clip(new_weight, old_weight * 0.8, old_weight * 1.2)
    """
    def update(self, niche: str, metrics: MetricsSnapshot) -> float:
        old = self._weights.get(niche, 1.0)
        signal = self._performance_signal(metrics)   # O(1)
        raw = self.alpha * signal + (1 - self.alpha) * old  # O(1)
        bounded = max(old * 0.8, min(old * 1.2, raw))       # O(1)
        self._weights[niche] = bounded
        return bounded
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-338 | 🔲 | Створити `src/ytaimbot_ml/feedback/` пакет | `src/ytaimbot_ml/feedback/__init__.py` | S | T-003 | — |
| T-339 | 🔲 | Реалізувати `FeedbackScorer` клас | `src/ytaimbot_ml/feedback/scorer.py` | L | T-338, T-326 | — |
| T-340 | 🔲 | Реалізувати `update(niche, metrics)` → float (EMA) | `src/ytaimbot_ml/feedback/scorer.py` | M | T-339 | — |
| T-341 | 🔲 | Реалізувати `_performance_signal(metrics)` → float [0.0, 1.0] | `src/ytaimbot_ml/feedback/scorer.py` | M | T-339 | — |
| T-342 | 🔲 | Реалізувати safety bounds (±20% per week) | `src/ytaimbot_ml/feedback/scorer.py` | M | T-340 | — |
| T-343 | 🔲 | Реалізувати `get_weights()` → dict[str, float] | `src/ytaimbot_ml/feedback/scorer.py` | S | T-339 | — |
| T-344 | 🔲 | Реалізувати persist weights у SQLite | `src/ytaimbot_ml/feedback/scorer.py` | M | T-339 | — |
| T-345 | 🔲 | Написати тести для FeedbackScorer | `tests/test_feedback_scorer.py` | M | T-339 | — |
| T-346 | 🔲 | Тест: EMA — новий weight між old та signal | `tests/test_feedback_scorer.py` | M | T-345 | — |
| T-347 | 🔲 | Тест: safety bounds — зміна ≤ 20% | `tests/test_feedback_scorer.py` | M | T-345 | — |
| T-348 | 🔲 | Тест: детермінізм — однаковий seed → однакові weights | `tests/test_feedback_scorer.py` | M | T-345 | — |

---

### 📌 EPIC 5.4 — A/B Testing Framework

> **AI агенте:** A/B тест порівнює 2 варіанти title або thumbnail по CTR.
> Статистична значимість: Chi-Square test (p-value < 0.05 → є різниця).
> Структура даних: dict[variant_id → {clicks, impressions}] — O(1) update.
> Мінімальний розмір вибірки: 1000 показів на варіант (power analysis).

**Алгоритм Chi-Square для A/B тесту:**
```python
from scipy.stats import chi2_contingency

def is_significant(variant_a: dict, variant_b: dict,
                   alpha: float = 0.05) -> ABTestResult:
    """
    Chi-Square тест для порівняння двох CTR.
    Складність: O(1) — константна кількість комірок (2×2 таблиця)

    contingency_table = [
        [a_clicks,     a_impressions - a_clicks],   # variant A
        [b_clicks,     b_impressions - b_clicks],   # variant B
    ]
    """
    table = [
        [variant_a["clicks"], variant_a["impressions"] - variant_a["clicks"]],
        [variant_b["clicks"], variant_b["impressions"] - variant_b["clicks"]],
    ]
    chi2, p_value, dof, expected = chi2_contingency(table)
    winner = "a" if variant_a["ctr"] > variant_b["ctr"] else "b"
    return ABTestResult(
        significant=(p_value < alpha),
        p_value=p_value,
        winner=winner if p_value < alpha else "inconclusive"
    )
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-349 | 🔲 | Створити `ABTestResult` dataclass у schemas.py | `src/ytaimbot_ml/schemas.py` | S | T-002 | — |
| T-350 | 🔲 | Реалізувати `ABTester` клас | `src/ytaimbot_ml/feedback/ab_tester.py` | L | T-338, T-349 | — |
| T-351 | 🔲 | Реалізувати `record_impression(video_id, variant)` → None (O(1)) | `src/ytaimbot_ml/feedback/ab_tester.py` | M | T-350 | — |
| T-352 | 🔲 | Реалізувати `record_click(video_id, variant)` → None (O(1)) | `src/ytaimbot_ml/feedback/ab_tester.py` | M | T-350 | — |
| T-353 | 🔲 | Реалізувати `analyze(video_id)` → ABTestResult (Chi-Square) | `src/ytaimbot_ml/feedback/ab_tester.py` | L | T-350 | — |
| T-354 | 🔲 | Реалізувати мінімальний розмір вибірки (1000 показів) | `src/ytaimbot_ml/feedback/ab_tester.py` | M | T-350 | — |
| T-355 | 🔲 | Реалізувати persist у SQLite (ab_tests таблиця) | `src/ytaimbot_ml/feedback/ab_tester.py` | M | T-350, T-319 | — |
| T-356 | 🔲 | Написати тести для ABTester | `tests/test_ab_tester.py` | M | T-350 | — |
| T-357 | 🔲 | Тест: < 1000 показів → "inconclusive" (не робимо висновків) | `tests/test_ab_tester.py` | M | T-356 | — |
| T-358 | 🔲 | Тест: явна різниця в CTR → p_value < 0.05, winner визначено | `tests/test_ab_tester.py` | M | T-356 | — |
| T-359 | 🔲 | Тест: однакові CTR → "inconclusive" | `tests/test_ab_tester.py` | M | T-356 | — |

---

### 📌 EPIC 5.5 — Weekly Report Generator

> **AI агенте:** Автоматичний markdown звіт щотижня.
> Зберігається у `docs/WEEKLY_REPORTS/YYYY-WNN.md` (не в .gitignore — це business data).
> Включає: топ-5 відео, bottom-5, CTR trend, RPM trend, нові recommendations.
> Візуалізації: ASCII графіки (не matplotlib) — для простоти у terminal та Markdown.

**ASCII Bar Chart алгоритм:**
```python
def ascii_bar(value: float, max_val: float, width: int = 30) -> str:
    """
    Складність: O(width) = O(1) — константна ширина
    """
    filled = int((value / max_val) * width) if max_val > 0 else 0
    bar = "█" * filled + "░" * (width - filled)
    return f"|{bar}| {value:.2f}"

# Приклад виводу:
# Python Tutorial  |████████████░░░░░░░░░░░░░░░░░░| 8.50%
# AI Beginner 2026 |████████████████████░░░░░░░░░░| 11.20%
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-360 | 🔲 | Створити `modules/reporting/` пакет | `modules/reporting/__init__.py` | S | T-008 | — |
| T-361 | 🔲 | Реалізувати `WeeklyReportGenerator` клас | `modules/reporting/weekly_report.py` | L | T-360, T-317 | — |
| T-362 | 🔲 | Реалізувати `generate(week: int, year: int)` → str (markdown) | `modules/reporting/weekly_report.py` | L | T-361 | — |
| T-363 | 🔲 | Реалізувати `_top_videos(n=5)` → list[Video] (за RPM) | `modules/reporting/weekly_report.py` | M | T-361 | — |
| T-364 | 🔲 | Реалізувати `_bottom_videos(n=5)` → list[Video] (за retention) | `modules/reporting/weekly_report.py` | M | T-361 | — |
| T-365 | 🔲 | Реалізувати `ascii_bar(value, max_val, width=30)` → str | `modules/reporting/weekly_report.py` | S | T-361 | — |
| T-366 | 🔲 | Реалізувати `_recommendations()` → list[str] (на основі даних) | `modules/reporting/weekly_report.py` | M | T-361 | — |
| T-367 | 🔲 | Зберігати звіт у `docs/WEEKLY_REPORTS/YYYY-WNN.md` | `modules/reporting/weekly_report.py` | S | T-362 | — |
| T-368 | 🔲 | Написати тести для WeeklyReportGenerator | `tests/test_weekly_report.py` | M | T-361 | — |
| T-369 | 🔲 | Тест: generate() повертає непорожній markdown string | `tests/test_weekly_report.py` | S | T-368 | — |
| T-370 | 🔲 | Тест: звіт містить секції top/bottom/recommendations | `tests/test_weekly_report.py` | M | T-368 | — |
| T-371 | 🔲 | Тест: ascii_bar — заповненість пропорційна value/max_val | `tests/test_weekly_report.py` | S | T-368 | — |

---

### 📌 EPIC 5.6 — Спіральна інтеграція Phase 5 у Pipeline

> **AI агенте:** Метрики → Feedback → Scorer → покращені наступні відео.
> Це "замкнутий контур" (closed loop) — перша справжня ML-петля в проєкті.
> Додати `METRICS_COLLECTION_DELAY_HOURS=48` та `FEEDBACK_ALPHA=0.3` до .env.

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-372 | 🔲 | Інтегрувати FeedbackScorer у TrendAnalyzer (weighted scoring) | `src/ytaimbot_ml/trend_analyzer.py` | L | T-343, T-003 | — |
| T-373 | 🔲 | Реалізувати daily metrics collection job (scheduler) | `modules/metrics_collector.py` | M | T-330, T-299 | — |
| T-374 | 🔲 | Реалізувати weekly feedback update job | `modules/metrics_collector.py` | M | T-340, T-373 | — |
| T-375 | 🔲 | Додати `METRICS_COLLECTION_DELAY_HOURS`, `FEEDBACK_ALPHA` до .env.example | `.env.example` | S | T-329, T-340 | — |
| T-376 | 🔲 | Оновити docker-compose.yml з новими env vars | `docker-compose.yml` | S | T-375 | — |
| T-377 | 🔲 | Написати інтеграційний тест: collect → score → analyze → report | `tests/test_feedback_integration.py` | L | T-372, T-374 | — |
| T-378 | 🔲 | Тест: після 10 ітерацій — топ niches отримують вищий weight | `tests/test_feedback_integration.py` | L | T-377 | — |
| T-379 | 🔲 | Запустити `pytest -q --tb=short` → всі зелені | CI | S | T-378 | — |
| T-380 | 🔲 | Перевірити coverage ≥ 80% для всіх нових модулів Phase 5 | CI | S | T-379 | — |

**Acceptance для PHASE 5 (загалом):**
- [ ] SQLite persistence: дані виживають після рестарту контейнера
- [ ] Metrics збираються через 48h після публікації
- [ ] EMA feedback: топ niches отримують вищий weight (тест T-378)
- [ ] A/B тест: Chi-Square p-value < 0.05 для значимих результатів
- [ ] Weekly report генерується автоматично щотижня
- [ ] Closed loop: метрики → weights → кращі тренди → кращий контент
- [ ] `pytest -q` → всі тести зелені
- [ ] Spearman rank correlation між predicted та actual scores ≥ 0.6

---

═══════════════════════════════════════════════════════════════════
## 🧠 PHASE 6: RL LEARNER + BANDIT — 🔲 PENDING (залежить P5)
═══════════════════════════════════════════════════════════════════

**Ціль:** Автономна оптимізація вибору ніш через Reinforcement Learning та Bandit алгоритми.
**Тиждень:** 13–16 | **Пріоритет:** 🟠 High
**Залежності:** Phase 6 → Phase 5 повністю ✅ (потрібні реальні метрики)

**Алгоритми в цій фазі:**
- **UCB1 (Upper Confidence Bound):** Multi-Armed Bandit → `O(k)` per step, `k` = ніші
- **Kolmogorov-Smirnov Test:** Drift detection → `O(n log n)` comparison
- **PPO (Proximal Policy Optimization):** Policy gradient RL → `O(batch × features)`
- **Softmax Exploration:** Temperature-based exploration → `O(k)`
- **Reservoir Sampling:** Streaming вибірка для drift detection → `O(n)` single pass

---

### 📌 EPIC 6.1 — Multi-Armed Bandit (UCB1 алгоритм)

> **AI агенте:** Multi-Armed Bandit вирішує проблему exploration/exploitation —
> яку нішу обрати наступного разу: перевірену (exploit) або нову (explore)?
> UCB1 автоматично балансує: `score = mean_reward + C × sqrt(ln(t) / n_i)`
> де `t` = загальна кількість спроб, `n_i` = спроби для ніші i, `C` = константа дослідження.
> Кожна "рука" бандита = одна YouTube ніша.

**UCB1 алгоритм (Upper Confidence Bound):**
```python
class UCB1Bandit:
    """
    Класичний UCB1 для вибору оптимальної YouTube ніші.
    Складність: O(k) per select() де k = кількість ніш

    Математика:
    UCB_i(t) = X̄_i + C × √(ln(t) / n_i)

    X̄_i  = середня винагорода для ніші i (RPM × retention)
    t     = загальна кількість відео
    n_i   = кількість відео у ніші i
    C     = 2.0 (exploration constant, конфігурується)

    Гарантія: O(√(k × t × ln(t))) regret (sub-linear!)
    """
    def select(self) -> str:                    # O(k)
        t = sum(self._counts.values()) + 1
        scores = {}
        for niche, count in self._counts.items():
            if count == 0:
                return niche          # спочатку пробуємо кожну нішу
            mean = self._rewards[niche] / count
            confidence = self.C * sqrt(log(t) / count)
            scores[niche] = mean + confidence
        return max(scores, key=scores.get)      # O(k)

    def update(self, niche: str, reward: float) -> None:  # O(1)
        self._counts[niche] += 1
        self._rewards[niche] += reward
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-381 | 🔲 | Створити `src/ytaimbot_ml/learner/` пакет | `src/ytaimbot_ml/learner/__init__.py` | S | T-003 | — |
| T-382 | 🔲 | Реалізувати `UCB1Bandit` клас | `src/ytaimbot_ml/learner/bandit.py` | L | T-381 | — |
| T-383 | 🔲 | Реалізувати `select()` → str (ніша) з UCB1 формулою | `src/ytaimbot_ml/learner/bandit.py` | M | T-382 | — |
| T-384 | 🔲 | Реалізувати `update(niche, reward)` → None (O(1)) | `src/ytaimbot_ml/learner/bandit.py` | S | T-382 | — |
| T-385 | 🔲 | Реалізувати `_compute_reward(metrics)` → float [0.0, 1.0] | `src/ytaimbot_ml/learner/bandit.py` | M | T-382 | — |
| T-386 | 🔲 | Реалізувати `SoftmaxBandit` як альтернативу UCB1 | `src/ytaimbot_ml/learner/bandit.py` | M | T-382 | — |
| T-387 | 🔲 | Реалізувати persist bandit state у SQLite | `src/ytaimbot_ml/learner/bandit.py` | M | T-382, T-311 | — |
| T-388 | 🔲 | Реалізувати `get_stats()` → dict[niche → BanditStats] | `src/ytaimbot_ml/learner/bandit.py` | S | T-382 | — |
| T-389 | 🔲 | Реалізувати холодний старт: рівномірне дослідження перших `k` відео | `src/ytaimbot_ml/learner/bandit.py` | M | T-382 | — |
| T-390 | 🔲 | Написати тести для UCB1Bandit | `tests/test_bandit.py` | M | T-382 | — |
| T-391 | 🔲 | Тест: після 100 ітерацій — найкраща ніша обирається частіше | `tests/test_bandit.py` | L | T-390 | — |
| T-392 | 🔲 | Тест: нова ніша (count=0) обирається першою (exploration) | `tests/test_bandit.py` | M | T-390 | — |
| T-393 | 🔲 | Тест: UCB1 regret sub-linear відносно random policy | `tests/test_bandit.py` | L | T-390 | — |
| T-394 | 🔲 | Тест: детермінізм — seed → однакова послідовність виборів | `tests/test_bandit.py` | M | T-390 | — |
| T-395 | 🔲 | Тест: persist + restore → state не змінюється | `tests/test_bandit.py` | M | T-390 | — |

**Acceptance для EPIC 6.1:**
- [ ] UCB1 regret: sub-linear відносно random (тест T-393)
- [ ] Детермінізм при однаковому seed
- [ ] State persist у SQLite (відновлення після рестарту)
- [ ] Холодний старт: кожна ніша отримує ≥ 1 спробу перед exploitation

---

### 📌 EPIC 6.2 — Drift Detector (Kolmogorov-Smirnov Test)

> **AI агенте:** Drift = розподіл трендів змінився (наприклад, нова хвиля контенту).
> KS-тест порівнює два розподіли: поточний тиждень vs попередній місяць.
> Якщо p-value < 0.05 → drift detected → скидаємо bandit weights (reset exploration).
> Reservoir Sampling зберігає репрезентативну вибірку потоку даних.

**Kolmogorov-Smirnov Drift Detection:**
```python
from scipy.stats import ks_2samp

class KSDriftDetector:
    """
    KS-тест для detection дрейфу розподілу trend scores.
    Складність: O(n log n) для сортування двох вибірок

    Ідея:
    - reference_window: останні 30 днів метрик (baseline)
    - current_window:   останні 7 днів метрик (поточний)
    - KS statistic D = max|F1(x) - F2(x)| — максимальне відхилення CDF

    Якщо p_value < threshold (0.05) → drift → alert + reset bandit
    """
    def check(self,
              reference: list[float],
              current: list[float]) -> DriftReport:
        stat, p_value = ks_2samp(reference, current)   # O(n log n)
        drift = p_value < self.threshold
        return DriftReport(
            statistic=stat,
            p_value=p_value,
            drift_detected=drift,
            action="reset_bandit" if drift else "continue"
        )
```

**Reservoir Sampling (потокова вибірка):**
```python
def reservoir_sample(stream: Iterator[float],
                     k: int,
                     rng: np.random.Generator) -> list[float]:
    """
    Зберігаємо k елементів з потоку невідомої довжини.
    Кожен елемент має рівну ймовірність потрапити у вибірку.
    Складність: O(n) single pass, O(k) пам'ять

    Алгоритм Vitter's Algorithm R:
    """
    reservoir = []
    for i, item in enumerate(stream):
        if i < k:
            reservoir.append(item)        # перші k елементів
        else:
            j = rng.integers(0, i + 1)   # O(1)
            if j < k:
                reservoir[j] = item       # замінюємо випадковий
    return reservoir
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-396 | 🔲 | Створити `DriftReport` dataclass у schemas.py | `src/ytaimbot_ml/schemas.py` | S | T-002 | — |
| T-397 | 🔲 | Реалізувати `KSDriftDetector` клас | `src/ytaimbot_ml/learner/drift_detector.py` | L | T-381, T-396 | — |
| T-398 | 🔲 | Реалізувати `check(reference, current)` → DriftReport (KS-test) | `src/ytaimbot_ml/learner/drift_detector.py` | L | T-397 | — |
| T-399 | 🔲 | Реалізувати `reservoir_sample(stream, k, rng)` (Vitter's Algorithm R) | `src/ytaimbot_ml/learner/drift_detector.py` | M | T-397 | — |
| T-400 | 🔲 | Реалізувати `_collect_reference_window(days=30)` → list[float] | `src/ytaimbot_ml/learner/drift_detector.py` | M | T-397, T-317 | — |
| T-401 | 🔲 | Реалізувати `_collect_current_window(days=7)` → list[float] | `src/ytaimbot_ml/learner/drift_detector.py` | M | T-397, T-317 | — |
| T-402 | 🔲 | Реалізувати auto-reset bandit при drift_detected=True | `src/ytaimbot_ml/learner/drift_detector.py` | M | T-397, T-382 | — |
| T-403 | 🔲 | Написати тести для KSDriftDetector | `tests/test_drift_detector.py` | M | T-397 | — |
| T-404 | 🔲 | Тест: однакові розподіли → p_value > 0.05 → "continue" | `tests/test_drift_detector.py` | M | T-403 | — |
| T-405 | 🔲 | Тест: різні розподіли (N(0,1) vs N(5,1)) → drift detected | `tests/test_drift_detector.py` | M | T-403 | — |
| T-406 | 🔲 | Тест: reservoir_sample — всі елементи мають рівну ймовірність | `tests/test_drift_detector.py` | L | T-403 | — |
| T-407 | 🔲 | Тест: drift → bandit state скидається | `tests/test_drift_detector.py` | M | T-403 | — |

---

### 📌 EPIC 6.3 — PPO Policy Optimizer (Proximal Policy Optimization)

> **AI агенте:** PPO — lightweight RL для оптимізації вибору параметрів контенту
> (довжина відео, стиль thumbnail, тон скрипту).
> Це НЕ повноцінний deep RL — це табличний/лінійний PPO без нейромережі.
> State = feature vector ніші. Action = параметри контенту. Reward = RPM × retention.
> Clipping epsilon = 0.2 (стандарт PPO) для стабільного навчання.

**Лінійний PPO (без нейромережі, для CPU):**
```python
class LinearPPO:
    """
    Лінійна апроксимація policy для малих state/action просторів.
    Складність: O(state_dim × action_dim) per update

    Policy: π(a|s) = softmax(W @ s + b)
    Value:  V(s)   = v_W @ s + v_b

    PPO Clip Objective:
    L_CLIP = E[min(r_t × A_t, clip(r_t, 1-ε, 1+ε) × A_t)]

    де r_t = π_new(a|s) / π_old(a|s)  (probability ratio)
        A_t = advantage estimate (TD error)
        ε   = 0.2 (clipping parameter)
    """
    def update(self, trajectory: list[Transition]) -> float:  # O(T × dim)
        advantages = self._compute_advantages(trajectory)      # O(T)
        for epoch in range(self.n_epochs):                     # O(K)
            for batch in self._get_batches(trajectory):       # O(T/B)
                loss = self._ppo_loss(batch, advantages)       # O(B × dim)
                self._gradient_step(loss)                      # O(dim²)
        return loss.item()
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-408 | 🔲 | Визначити `ContentAction` та `ContentState` dataclasses | `src/ytaimbot_ml/schemas.py` | M | T-002 | — |
| T-409 | 🔲 | Реалізувати `LinearPPO` клас (без PyTorch для MVP) | `src/ytaimbot_ml/learner/optimizer.py` | XL | T-381 | — |
| T-410 | 🔲 | Реалізувати `select_action(state)` → ContentAction (softmax) | `src/ytaimbot_ml/learner/optimizer.py` | L | T-409 | — |
| T-411 | 🔲 | Реалізувати `update(trajectory)` → float (PPO loss) | `src/ytaimbot_ml/learner/optimizer.py` | XL | T-409 | — |
| T-412 | 🔲 | Реалізувати `_compute_advantages(trajectory)` → np.ndarray | `src/ytaimbot_ml/learner/optimizer.py` | L | T-409 | — |
| T-413 | 🔲 | Реалізувати PPO clip: `clip(r_t, 1-ε, 1+ε)` | `src/ytaimbot_ml/learner/optimizer.py` | M | T-409 | — |
| T-414 | 🔲 | Реалізувати `save_policy(path)` та `load_policy(path)` | `src/ytaimbot_ml/learner/optimizer.py` | M | T-409 | — |
| T-415 | 🔲 | Написати тести для LinearPPO | `tests/test_ppo_optimizer.py` | L | T-409 | — |
| T-416 | 🔲 | Тест: update() зменшує loss після кількох ітерацій | `tests/test_ppo_optimizer.py` | L | T-415 | — |
| T-417 | 🔲 | Тест: clipping — ratio не виходить за [1-ε, 1+ε] | `tests/test_ppo_optimizer.py` | M | T-415 | — |
| T-418 | 🔲 | Тест: save + load policy → ідентичні дії | `tests/test_ppo_optimizer.py` | M | T-415 | — |
| T-419 | 🔲 | Тест: детермінізм при однаковому seed | `tests/test_ppo_optimizer.py` | M | T-415 | — |

---

### 📌 EPIC 6.4 — Open-Sora Integration (GPU-gated, опціонально)

> **AI агенте:** Open-Sora — AI генерація відео (текст → відео).
> **УВАГА:** Вимагає GPU (мінімум NVIDIA T4, рекомендується A100).
> На Hetzner CX22 (CPU-only) — ПРОПУСКАЄМО, використовуємо MoviePy.
> Активується через `USE_OPEN_SORA=true` + `GPU_AVAILABLE=true`.
> Fallback завжди: якщо Open-Sora недоступна → MoviePy assembler.

**GPU Gate Pattern:**
```python
def create_video_backend(config: Config) -> VideoAssembler:
    """
    Factory function з GPU gate.
    Складність: O(1) — вибір бекенду

    Ієрархія якості (краще → гірше):
    1. OpenSoraGenerator  (AI відео, потрібен GPU)
    2. MoviePyAssembler   (слайд-шоу, CPU)
    3. StaticImageVideo   (одне зображення, CPU, fallback)
    """
    if config.use_open_sora and config.gpu_available:
        try:
            return OpenSoraGenerator(model=config.sora_model)
        except ImportError:
            logger.warning("Open-Sora not installed, falling back to MoviePy")
    return MoviePyAssembler()  # default CPU path
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-420 | 🔲 | Реалізувати `OpenSoraGenerator` клас (GPU-gated) | `modules/video/ai_generator.py` | XL | T-162, T-163 | — |
| T-421 | 🔲 | Реалізувати `generate(prompt, duration)` → Path (.mp4) | `modules/video/ai_generator.py` | XL | T-420 | — |
| T-422 | 🔲 | Реалізувати GPU availability check (`torch.cuda.is_available()`) | `modules/video/ai_generator.py` | S | T-420 | — |
| T-423 | 🔲 | Реалізувати `create_video_backend(config)` factory function | `modules/video/ai_generator.py` | M | T-420, T-164 | — |
| T-424 | 🔲 | Реалізувати fallback: Open-Sora недоступна → MoviePy | `modules/video/ai_generator.py` | M | T-423 | — |
| T-425 | 🔲 | Додати `USE_OPEN_SORA`, `GPU_AVAILABLE`, `SORA_MODEL` до .env.example | `.env.example` | S | T-420 | — |
| T-426 | 🔲 | Написати тести (GPU gate повністю замоканий) | `tests/test_ai_generator.py` | M | T-420 | — |
| T-427 | 🔲 | Тест: GPU недоступний → fallback до MoviePy | `tests/test_ai_generator.py` | M | T-426 | — |
| T-428 | 🔲 | Тест: USE_OPEN_SORA=false → MoviePy незалежно від GPU | `tests/test_ai_generator.py` | S | T-426 | — |

---

### 📌 EPIC 6.5 — Інтеграція Phase 6 у Pipeline

> **AI агенте:** Phase 6 замикає повний автономний цикл:
> Bandit вибирає нішу → Pipeline генерує відео → Metrics збираються → Bandit оновлюється.
> Додати `BANDIT_EXPLORATION_C`, `DRIFT_THRESHOLD`, `PPO_EPSILON` до .env.

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-429 | 🔲 | Інтегрувати `UCB1Bandit.select()` у Pipeline._ingest() | `modules/orchestrator.py` | L | T-383, T-008 | — |
| T-430 | 🔲 | Інтегрувати `UCB1Bandit.update()` після metrics collection | `modules/orchestrator.py` | M | T-384, T-373 | — |
| T-431 | 🔲 | Інтегрувати `KSDriftDetector` у weekly feedback job | `modules/orchestrator.py` | M | T-398, T-374 | — |
| T-432 | 🔲 | Інтегрувати `LinearPPO` для вибору content parameters | `modules/orchestrator.py` | L | T-410, T-408 | — |
| T-433 | 🔲 | Замінити video backend на `create_video_backend(config)` factory | `modules/orchestrator.py` | M | T-423 | — |
| T-434 | 🔲 | Додати `BANDIT_EXPLORATION_C=2.0` до .env.example | `.env.example` | S | T-383 | — |
| T-435 | 🔲 | Додати `DRIFT_THRESHOLD=0.05` до .env.example | `.env.example` | S | T-398 | — |
| T-436 | 🔲 | Додати `PPO_EPSILON=0.2`, `PPO_LR=0.001` до .env.example | `.env.example` | S | T-411 | — |
| T-437 | 🔲 | Написати інтеграційні тести: Bandit + Pipeline + Metrics loop | `tests/test_rl_integration.py` | XL | T-429, T-430 | — |
| T-438 | 🔲 | Тест: після 20 циклів — bandit конвергує до топ ніші | `tests/test_rl_integration.py` | L | T-437 | — |
| T-439 | 🔲 | Запустити `pytest -q --tb=short` → всі зелені | CI | S | T-438 | — |
| T-440 | 🔲 | Перевірити coverage ≥ 80% для `src/ytaimbot_ml/learner/` | CI | S | T-439 | — |

**Acceptance для PHASE 6 (загалом):**
- [ ] UCB1: sub-linear regret vs random (тест T-393)
- [ ] KS drift detector: правильно виявляє зміну розподілу
- [ ] PPO loss: зменшується після 10+ iterations (тест T-416)
- [ ] Bandit конвергує до кращих ніш за 20 циклів (тест T-438)
- [ ] GPU gate: завжди fallback до MoviePy на CPU-only системах
- [ ] State persist: bandit відновлюється після рестарту контейнера

---

═══════════════════════════════════════════════════════════════════
## 🔧 PHASE 7: INFRASTRUCTURE + DEVOPS — 🔲 PENDING
═══════════════════════════════════════════════════════════════════

**Ціль:** Production-ready інфраструктура на Hetzner CX22 з моніторингом та автовідновленням.
**Тиждень:** 8–16 (паралельно з P4–P6) | **Пріоритет:** 🟠 High
**Залежності:** Phase 7 може виконуватись ПАРАЛЕЛЬНО з P4–P6

**Алгоритми в цій фазі:**
- **Exponential Backoff (systemd):** Restart delay: `2^attempt` seconds → cap 300s
- **Ring Buffer (logs):** Logrotate з фіксованим розміром → `O(1)` write, `O(n)` drain
- **Bloom Filter (dedup alerts):** Уникати дублікатів Slack повідомлень → `O(k)` hash functions
- **Consistent Hashing (backups):** Рівномірний розподіл навантаження → `O(log n)`
- **Health Check FSM:** Finite State Machine (healthy→degraded→critical→down) → `O(1)` transitions

---

### 📌 EPIC 7.1 — Hetzner CX22 Deployment

> **AI агенте:** Автоматизовані скрипти розгортання для Hetzner CX22.
> Ubuntu 22.04 LTS, Docker + docker-compose, systemd watchdog.
> Zero-downtime deploy: blue-green через docker-compose profiles.
> Всі скрипти в `scripts/deploy/` — ідемпотентні (можна запускати повторно).

**Blue-Green Deployment Flow:**
```
scripts/deploy/deploy.sh:

1. git pull origin main                     # оновлення коду
2. docker compose build --no-cache bot      # build new image
3. docker compose --profile green up -d     # запуск нового контейнера
4. health_check green (retry 5×, 10s)      # перевірка
5. if healthy:
     docker compose --profile blue down    # зупинка старого
     echo "Deploy successful"
6. else:
     docker compose --profile green down   # rollback
     echo "Deploy FAILED, old version still running"
     exit 1
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-441 | 🔲 | Створити `scripts/deploy/` директорію | `scripts/deploy/` | S | T-014 | — |
| T-442 | 🔲 | Написати `scripts/deploy/setup_server.sh` (apt, Docker, user) | `scripts/deploy/setup_server.sh` | L | T-441 | — |
| T-443 | 🔲 | Написати `scripts/deploy/deploy.sh` (blue-green deploy) | `scripts/deploy/deploy.sh` | L | T-441 | — |
| T-444 | 🔲 | Написати `scripts/deploy/rollback.sh` (відкат до попереднього тегу) | `scripts/deploy/rollback.sh` | M | T-443 | — |
| T-445 | 🔲 | Написати `scripts/deploy/health_check.sh` (retry 5×, timeout 30s) | `scripts/deploy/health_check.sh` | M | T-441 | — |
| T-446 | 🔲 | Налаштувати systemd service `ytaimbot.service` | `scripts/deploy/ytaimbot.service` | M | T-441 | — |
| T-447 | 🔲 | Налаштувати systemd watchdog (restart=on-failure, max 5 restarts/5хв) | `scripts/deploy/ytaimbot.service` | M | T-446 | — |
| T-448 | 🔲 | Налаштувати logrotate для docker logs (max 100MB, 7 днів) | `scripts/deploy/ytaimbot-logrotate` | S | T-441 | — |
| T-449 | 🔲 | Оновити `docker-compose.yml` з blue-green profiles | `docker-compose.yml` | M | T-014 | — |
| T-450 | 🔲 | Додати `DEPLOY_TAG`, `HETZNER_IP` до .env.example | `.env.example` | S | T-443 | — |
| T-451 | 🔲 | Документувати deploy process у docs/DEPLOYMENT_GUIDE | `docs/DEPLOYMENT_GUIDE_HETZNER_LOCAL_FIRST.md` | M | T-443 | — |
| T-452 | 🔲 | Тест: health_check.sh повертає 0 коли контейнер запущений | `tests/test_deploy_scripts.sh` | M | T-445 | — |

---

### 📌 EPIC 7.2 — Prometheus + Grafana Monitoring

> **AI агенте:** Prometheus збирає метрики, Grafana візуалізує дашборди.
> Додати `prometheus-client` до Python для custom metrics.
> Ключові метрики: pipeline_runs_total, pipeline_duration_seconds, publish_errors_total.
> Alertmanager: alert якщо pipeline не запускався > 25 годин (missed daily run).

**Custom Prometheus Metrics:**
```python
from prometheus_client import Counter, Histogram, Gauge

# Pipeline metrics
PIPELINE_RUNS = Counter(
    'ytaimbot_pipeline_runs_total',
    'Total pipeline runs',
    ['status']          # labels: success, error, dry_run
)
PIPELINE_DURATION = Histogram(
    'ytaimbot_pipeline_duration_seconds',
    'Pipeline execution time',
    buckets=[30, 60, 120, 300, 600]  # 30s → 10хв
)
PUBLISH_ERRORS = Counter(
    'ytaimbot_publish_errors_total',
    'Publishing failures',
    ['reason']          # labels: quota, auth, compliance
)
TREND_SCORE_MAX = Gauge(
    'ytaimbot_trend_score_max',
    'Highest trend score in last run'
)
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-453 | 🔲 | Додати `prometheus-client` до pyproject.toml | `pyproject.toml` | S | T-001 | — |
| T-454 | 🔲 | Реалізувати `MetricsRegistry` з 4 custom метриками | `src/ytaimbot_ml/utils/metrics.py` | M | T-453 | — |
| T-455 | 🔲 | Інтегрувати metrics у Pipeline (increment/observe у кожній стадії) | `modules/orchestrator.py` | M | T-454, T-008 | — |
| T-456 | 🔲 | Запустити prometheus HTTP сервер на порту 9090 | `modules/orchestrator.py` | S | T-454 | — |
| T-457 | 🔲 | Написати `docker-compose.monitoring.yml` (Prometheus + Grafana) | `docker-compose.monitoring.yml` | L | T-014 | — |
| T-458 | 🔲 | Написати `prometheus.yml` конфіг (scrape interval 15s) | `scripts/monitoring/prometheus.yml` | M | T-457 | — |
| T-459 | 🔲 | Створити Grafana dashboard JSON (pipeline runs, duration, errors) | `scripts/monitoring/grafana_dashboard.json` | L | T-457 | — |
| T-460 | 🔲 | Налаштувати Alertmanager: alert якщо > 25год без запуску | `scripts/monitoring/alertmanager.yml` | M | T-457 | — |
| T-461 | 🔲 | Написати тести для MetricsRegistry (перевірити що метрики increment) | `tests/test_metrics_registry.py` | S | T-454 | — |
| T-462 | 🔲 | Тест: pipeline error → PUBLISH_ERRORS.labels("compliance").inc() | `tests/test_metrics_registry.py` | M | T-461 | — |

---

### 📌 EPIC 7.3 — Slack Notifications

> **AI агенте:** Slack webhook для алертів та щоденного звіту.
> Bloom Filter уникає дублікатів алертів (один і той самий error не спамить).
> Канали: `#ytaimbot-alerts` (errors), `#ytaimbot-daily` (daily summary).
> Webhook URL з env var `SLACK_WEBHOOK_URL` (never hardcode!).

**Bloom Filter для dedup алертів:**
```python
class AlertDeduplicator:
    """
    Bloom Filter для уникнення дублікатів Slack повідомлень.
    False positive rate: ~1% при 1000 елементів, 10 hash функцій
    Складність: O(k) per check/add де k = кількість hash функцій

    Після 1 години — очищаємо фільтр (time-windowed Bloom Filter)
    """
    def __init__(self, capacity: int = 1000, error_rate: float = 0.01):
        # розмір бітового масиву: m = -n*ln(p) / (ln(2))^2
        self._bits = bitarray(self._optimal_size(capacity, error_rate))
        self._bits.setall(0)
        self._last_reset = time.time()

    def should_send(self, message: str) -> bool:
        key = sha256(message.encode()).hexdigest()
        if self._window_expired():
            self._bits.setall(0)  # reset window
        if self._contains(key):
            return False           # duplicate
        self._add(key)
        return True                # new message → send
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-463 | 🔲 | Реалізувати `SlackNotifier` клас | `modules/notifications/slack.py` | M | T-008 | — |
| T-464 | 🔲 | Реалізувати `send_alert(message, level)` → None (webhook POST) | `modules/notifications/slack.py` | M | T-463 | — |
| T-465 | 🔲 | Реалізувати `send_daily_summary(report)` → None | `modules/notifications/slack.py` | M | T-463 | — |
| T-466 | 🔲 | Реалізувати `AlertDeduplicator` (time-windowed Bloom Filter) | `modules/notifications/slack.py` | L | T-463 | — |
| T-467 | 🔲 | Інтегрувати SlackNotifier у Pipeline (error handler) | `modules/orchestrator.py` | M | T-463, T-008 | — |
| T-468 | 🔲 | Додати `SLACK_WEBHOOK_URL`, `SLACK_CHANNEL_ALERTS` до .env.example | `.env.example` | S | T-463 | — |
| T-469 | 🔲 | Написати тести (mock httpx.post) | `tests/test_slack_notifier.py` | M | T-463 | — |
| T-470 | 🔲 | Тест: duplicate alert → не відправляється (Bloom Filter) | `tests/test_slack_notifier.py` | M | T-469 | — |
| T-471 | 🔲 | Тест: SLACK_WEBHOOK_URL відсутній → graceful skip (не crash) | `tests/test_slack_notifier.py` | S | T-469 | — |

---

### 📌 EPIC 7.4 — Automated Backups

> **AI агенте:** Щоденний backup `./data/` на Hetzner Object Storage (S3-compatible).
> Шифрування backup перед завантаженням (AES-256 через `cryptography` бібліотеку).
> Retention policy: 7 щоденних, 4 тижневих, 3 місячних (Grandfather-Father-Son).
> Скрипт: `scripts/backup/backup.sh` — запускається через cron о 03:00 UTC.

**GFS Retention Policy (Grandfather-Father-Son):**
```
GFS алгоритм:
  Щоденні (Son):    зберігаємо 7 останніх  → видаляємо 8+
  Тижневі (Father): зберігаємо 4 останніх  → (кожна неділя)
  Місячні (Grandfather): зберігаємо 3 останніх → (перший день місяця)

  Загальний storage: ~14 backup файлів максимум
  Складність: O(n_backups) для cleanup = O(14) = O(1)
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-472 | 🔲 | Написати `scripts/backup/backup.sh` (tar + encrypt + upload) | `scripts/backup/backup.sh` | L | T-441 | — |
| T-473 | 🔲 | Написати `scripts/backup/restore.sh` (download + decrypt + untar) | `scripts/backup/restore.sh` | L | T-472 | — |
| T-474 | 🔲 | Реалізувати GFS retention cleanup у backup.sh | `scripts/backup/backup.sh` | M | T-472 | — |
| T-475 | 🔲 | Налаштувати cron job: `0 3 * * * /app/scripts/backup/backup.sh` | `scripts/deploy/setup_server.sh` | S | T-472 | — |
| T-476 | 🔲 | Додати `S3_BUCKET`, `S3_ENDPOINT`, `BACKUP_ENCRYPTION_KEY` до .env.example | `.env.example` | S | T-472 | — |
| T-477 | 🔲 | Тест: backup.sh створює зашифрований .tar.gz.enc файл | `tests/test_backup.sh` | M | T-472 | — |
| T-478 | 🔲 | Тест: restore.sh відновлює дані без втрати | `tests/test_backup.sh` | M | T-473 | — |

---

### 📌 EPIC 7.5 — GitHub Actions CI/CD Розширення

> **AI агенте:** Розширити існуючий `ci.yml` з новими workflows.
> Додати: lint (ruff), security scan (bandit), docker build перевірка, coverage badge.
> Release workflow: при тегу `v*` → build + push до GitHub Container Registry (GHCR).

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-479 | 🔲 | Додати `ruff` linter до pyproject.toml та CI | `pyproject.toml`, `.github/workflows/ci.yml` | S | T-013 | — |
| T-480 | 🔲 | Додати `bandit` security scanner до CI | `.github/workflows/ci.yml` | S | T-013 | — |
| T-481 | 🔲 | Додати docker build перевірку до CI | `.github/workflows/ci.yml` | S | T-014 | — |
| T-482 | 🔲 | Додати coverage badge до README.md | `README.md`, `.github/workflows/ci.yml` | S | T-013 | — |
| T-483 | 🔲 | Написати `release.yml` workflow (tag v* → GHCR push) | `.github/workflows/release.yml` | L | T-013 | — |
| T-484 | 🔲 | Налаштувати Dependabot для auto-update залежностей | `.github/dependabot.yml` | S | T-013 | — |
| T-485 | 🔲 | Додати `pytest --cov` coverage звіт до PR коментарів | `.github/workflows/ci.yml` | M | T-013 | — |
| T-486 | 🔲 | Написати `docker-compose.test.yml` для ізольованих тестів у CI | `docker-compose.test.yml` | M | T-014 | — |
| T-487 | 🔲 | Верифікувати: CI проходить на Python 3.11 та 3.12 | `.github/workflows/ci.yml` | S | T-479 | — |
| T-488 | 🔲 | Верифікувати: docker build < 5 хвилин у CI | `.github/workflows/ci.yml` | S | T-481 | — |
| T-489 | 🔲 | Запустити повний CI pipeline → зелений | CI | S | T-487, T-488 | — |
| T-490 | 🔲 | Документувати CI/CD процес у docs/DEPLOYMENT_GUIDE | `docs/DEPLOYMENT_GUIDE_HETZNER_LOCAL_FIRST.md` | S | T-483 | — |

**Acceptance для PHASE 7 (загалом):**
- [ ] `docker compose up -d` на чистому Ubuntu 22.04 → успішно
- [ ] systemd watchdog: контейнер перезапускається після crash
- [ ] Prometheus метрики доступні на `:9090/metrics`
- [ ] Grafana dashboard відображає pipeline runs та duration
- [ ] Slack alert при pipeline error (не duplicate)
- [ ] Daily backup до S3 о 03:00 UTC
- [ ] CI: ruff + bandit + pytest + docker build → все зелене
- [ ] Release tag `v0.1.0` → image у GHCR автоматично

---

═══════════════════════════════════════════════════════════════════
## 🔒 PHASE 8: SECURITY + COMPLIANCE — 🔲 PENDING
═══════════════════════════════════════════════════════════════════

**Ціль:** Захист від витоків секретів, валідація вхідних даних, YouTube/GDPR compliance.
**Тиждень:** 10–16 (паралельно з P5–P7) | **Пріоритет:** 🔴 Critical
**Залежності:** Phase 8 може виконуватись ПАРАЛЕЛЬНО з P5–P7

**Алгоритми в цій фазі:**
- **Regex DFA:** Детермінований скінченний автомат для валідації вхідних рядків → `O(n)`
- **HMAC-SHA256:** Підпис webhook payloads → `O(n)` де n = розмір payload
- **Trie:** Перевірка заблокованих слів у контенті → `O(m)` де m = довжина слова
- **Rate Limiter (Token Bucket):** Захист від brute-force на CLI → `O(1)`
- **Merkle Tree:** Верифікація цілісності evidence artifacts → `O(log n)`

---

### 📌 EPIC 8.1 — Secrets Management

> **AI агенте:** Жодних секретів у коді або логах. Ніколи.
> Всі credentials через env vars або encrypted vault.
> Перед кожним commit — автоматична перевірка через `detect-secrets`.
> Логи: маскуємо всі значення що схожі на API ключі (regex pattern).

**Алгоритм маскування секретів у логах:**
```python
import re

SECRET_PATTERNS = [
    r'AIza[0-9A-Za-z\-_]{35}',          # Google API key
    r'ya29\.[0-9A-Za-z\-_]+',           # OAuth2 access token
    r'[0-9]+-[0-9A-Za-z_]{32}\.apps',  # OAuth2 client ID
    r'sk-[a-zA-Z0-9]{48}',             # OpenAI key pattern
    r'(?i)(password|secret|token|key)\s*[=:]\s*\S+',  # generic
]

class SecretMaskingFilter(logging.Filter):
    """
    Logging filter що маскує секрети перед записом.
    Складність: O(n_patterns × len(message)) per log record
    Використовує DFA (regex compile) → O(n) per match
    """
    _compiled = [re.compile(p) for p in SECRET_PATTERNS]

    def filter(self, record: logging.LogRecord) -> bool:
        msg = str(record.getMessage())
        for pattern in self._compiled:            # O(n_patterns)
            msg = pattern.sub("***REDACTED***", msg)  # O(len(msg))
        record.msg = msg
        record.args = ()
        return True
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-491 | 🔲 | Додати `detect-secrets` до dev залежностей pyproject.toml | `pyproject.toml` | S | T-001 | — |
| T-492 | 🔲 | Створити `.secrets.baseline` файл (detect-secrets scan) | `.secrets.baseline` | S | T-491 | — |
| T-493 | 🔲 | Додати detect-secrets pre-commit hook до `.pre-commit-config.yaml` | `.pre-commit-config.yaml` | M | T-491 | — |
| T-494 | 🔲 | Реалізувати `SecretMaskingFilter` logging filter | `src/ytaimbot_ml/utils/logging.py` | M | T-008 | — |
| T-495 | 🔲 | Інтегрувати `SecretMaskingFilter` у всі logger instances | `modules/orchestrator.py`, `modules/adapters/` | M | T-494 | — |
| T-496 | 🔲 | Провести audit всіх env vars — жодного hardcoded значення | всі `.py` файли | L | T-494 | — |
| T-497 | 🔲 | Додати `bandit -r src/ modules/` до CI (security scan) | `.github/workflows/ci.yml` | S | T-480 | — |
| T-498 | 🔲 | Написати тести для SecretMaskingFilter | `tests/test_secret_masking.py` | M | T-494 | — |
| T-499 | 🔲 | Тест: API ключ у log message → замінюється на `***REDACTED***` | `tests/test_secret_masking.py` | M | T-498 | — |
| T-500 | 🔲 | Тест: `bandit` scan → zero HIGH severity issues | CI | M | T-497 | — |

---

### 📌 EPIC 8.2 — Input Validation та Sanitization

> **AI агенте:** Всі зовнішні вхідні дані (API responses, user input, env vars)
> повинні бути валідовані перед використанням.
> Використовуй Pydantic validators для schema-level validation.
> Trie структура для blocklist перевірки контенту (O(m) замість O(n×m) naive).

**Trie для blocklist перевірки (Content Safety):**
```python
class BlocklistTrie:
    """
    Trie (Prefix Tree) для швидкої перевірки заблокованих слів.
    Insert: O(m) де m = довжина слова
    Search: O(m) — незалежно від розміру списку!
    vs naive: O(n×m) де n = розмір списку

    Структура вузла: dict[char → TrieNode] + is_end: bool
    Пам'ять: O(ALPHABET_SIZE × n × m) worst case
    """
    def insert(self, word: str) -> None:      # O(m)
        node = self._root
        for char in word.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end = True

    def contains_blocked(self, text: str) -> tuple[bool, str]:
        """Шукає будь-яке заблоковане слово у тексті → O(n×m)"""
        words = text.lower().split()
        for word in words:          # O(n) words
            if self._search(word):  # O(m) per word
                return True, word
        return False, ""
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-501 | 🔲 | Реалізувати `BlocklistTrie` клас для content safety | `src/ytaimbot_ml/quality/blocklist.py` | L | T-004 | — |
| T-502 | 🔲 | Створити `blocklist.txt` (заблоковані слова/фрази) | `src/ytaimbot_ml/quality/blocklist.txt` | M | T-501 | — |
| T-503 | 🔲 | Реалізувати `ContentSanitizer` клас (Trie + regex) | `src/ytaimbot_ml/quality/sanitizer.py` | L | T-501 | — |
| T-504 | 🔲 | Реалізувати `sanitize_script(text)` → str (видаляє заблоковане) | `src/ytaimbot_ml/quality/sanitizer.py` | M | T-503 | — |
| T-505 | 🔲 | Реалізувати `validate_env_var(name, value, pattern)` → str | `src/ytaimbot_ml/utils/validation.py` | M | T-494 | — |
| T-506 | 🔲 | Додати Pydantic validators до всіх dataclasses у schemas.py | `src/ytaimbot_ml/schemas.py` | L | T-002 | — |
| T-507 | 🔲 | Реалізувати `validate_youtube_api_response(data)` → dict | `modules/adapters/youtube_search.py` | M | T-040 | — |
| T-508 | 🔲 | Написати тести для BlocklistTrie та ContentSanitizer | `tests/test_content_safety.py` | M | T-501 | — |
| T-509 | 🔲 | Тест: Trie search O(m) — не залежить від розміру списку | `tests/test_content_safety.py` | M | T-508 | — |
| T-510 | 🔲 | Тест: sanitize_script() видаляє всі заблоковані слова | `tests/test_content_safety.py` | M | T-508 | — |

---

### 📌 EPIC 8.3 — YouTube Terms of Service + GDPR Compliance

> **AI агенте:** YouTube ToS вимагає AI disclosure для AI-generated контенту.
> GDPR: не збираємо PII, логи зберігаємо ≤ 30 днів.
> Evidence artifacts для кожного відео (Merkle-like integrity chain).
> Compliance checklist виконується автоматично перед кожним publish.

**Evidence Artifact Chain (Merkle-inspired):**
```python
@dataclass
class EvidenceArtifact:
    """
    Ланцюг доказів для кожного відео.
    Merkle-like: кожен artifact хешує попередній → tamper-evident.
    Складність перевірки: O(n) де n = довжина ланцюга
    """
    video_id:         str
    script_hash:      str   # SHA-256 скрипту
    similarity_score: float # SimilarityGate result
    bayes_score:      float # BayesQualityFilter result
    operator_decision:str   # approve/reject
    previous_hash:    str   # hash попереднього artifact (chain!)
    timestamp:        str   # ISO-8601 UTC
    chain_hash:       str   # SHA-256(всіх полів + previous_hash)

    def verify(self, previous: "EvidenceArtifact") -> bool:
        """Перевіряє цілісність ланцюга → O(1)"""
        expected = sha256(f"{self.video_id}{self.script_hash}"
                         f"{previous.chain_hash}".encode()).hexdigest()
        return self.chain_hash == expected
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-511 | 🔲 | Реалізувати `EvidenceArtifact` dataclass з chain_hash | `src/ytaimbot_ml/schemas.py` | M | T-002 | — |
| T-512 | 🔲 | Реалізувати `EvidenceChain` клас (append-only, verifiable) | `src/ytaimbot_ml/quality/evidence.py` | L | T-511 | — |
| T-513 | 🔲 | Реалізувати `append(artifact)` → перевіряє та додає до ланцюга | `src/ytaimbot_ml/quality/evidence.py` | M | T-512 | — |
| T-514 | 🔲 | Реалізувати `verify_chain()` → bool (перевірка цілісності) | `src/ytaimbot_ml/quality/evidence.py` | M | T-512 | — |
| T-515 | 🔲 | Реалізувати `ComplianceChecker` — автоматичний pre-publish checklist | `src/ytaimbot_ml/quality/compliance.py` | L | T-512, T-270 | — |
| T-516 | 🔲 | Реалізувати перевірку AI disclosure у metadata | `src/ytaimbot_ml/quality/compliance.py` | M | T-515 | — |
| T-517 | 🔲 | Реалізувати перевірку відсутності PII у скрипті (regex) | `src/ytaimbot_ml/quality/compliance.py` | M | T-515 | — |
| T-518 | 🔲 | Реалізувати log retention cleanup (видалення логів > 30 днів) | `scripts/deploy/cleanup_logs.sh` | S | T-448 | — |
| T-519 | 🔲 | Написати тести для EvidenceChain та ComplianceChecker | `tests/test_compliance.py` | M | T-512 | — |
| T-520 | 🔲 | Тест: verify_chain() — підроблений artifact → False | `tests/test_compliance.py` | M | T-519 | — |
| T-521 | 🔲 | Тест: ComplianceChecker блокує відео без AI disclosure | `tests/test_compliance.py` | M | T-519 | — |
| T-522 | 🔲 | Тест: PII (email, phone) у скрипті → compliance fail | `tests/test_compliance.py` | M | T-519 | — |

---

### 📌 EPIC 8.4 — Security Hardening та Penetration Testing

> **AI агенте:** Hardening = мінімізація attack surface.
> Docker: non-root user, read-only filesystem де можливо, no-new-privileges.
> Перевірити: SQL injection через параметризовані запити (вже маємо, верифікуємо).
> OWASP Top 10 checklist для web-facing компонентів (Prometheus endpoint).

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-523 | 🔲 | Налаштувати Docker non-root user у Dockerfile | `Dockerfile` | M | T-014 | — |
| T-524 | 🔲 | Додати `--no-new-privileges` та read-only rootfs у docker-compose | `docker-compose.yml` | M | T-014 | — |
| T-525 | 🔲 | Верифікувати всі SQLite запити — параметризовані (no f-strings) | `modules/adapters/sqlite_storage.py` | M | T-311 | — |
| T-526 | 🔲 | Додати Basic Auth до Prometheus `/metrics` endpoint | `modules/orchestrator.py` | M | T-456 | — |
| T-527 | 🔲 | Запустити `safety check` (CVE scan залежностей) | CI | S | T-497 | — |
| T-528 | 🔲 | Запустити `trivy image` Docker image scan | CI | M | T-481 | — |
| T-529 | 🔲 | Провести OWASP checklist review (документувати результати) | `docs/SECURITY_ERROR_HANDLING_GUIDE.md` | M | T-523 | — |
| T-530 | 🔲 | Тест: `bandit` + `safety` + `trivy` → zero CRITICAL issues | CI | L | T-527, T-528 | — |

**Acceptance для PHASE 8 (загалом):**
- [ ] `bandit -r src/ modules/` → 0 HIGH issues
- [ ] `safety check` → 0 CRITICAL CVEs
- [ ] `trivy image` → 0 CRITICAL vulns у Docker image
- [ ] Жоден API ключ не з'являється у логах (тест T-499)
- [ ] EvidenceChain: verify_chain() → True для всіх artifacts
- [ ] Pre-publish ComplianceChecker: AI disclosure обов'язковий
- [ ] Docker: non-root user, no-new-privileges

---

═══════════════════════════════════════════════════════════════════
## 🧪 PHASE 9: TESTING + COVERAGE — 🔲 PENDING
═══════════════════════════════════════════════════════════════════

**Ціль:** Coverage ≥ 90%, E2E тести, load testing, mutation testing, property-based testing.
**Тиждень:** 14–16 | **Пріоритет:** 🟠 High
**Залежності:** Phase 9 → Phase 4 ✅ (потрібен повний pipeline для E2E)

**Алгоритми тестування:**
- **Property-Based Testing (Hypothesis):** Generative testing → перевіряє всі edge cases
- **Mutation Testing (mutmut):** Вбиває мутантів → перевіряє якість тестів
- **Load Testing (Locust):** Concurrent users simulation → `O(n_users × requests)`
- **Coverage via BFS:** Відстежує які гілки коду покриті → граф потоку керування

---

### 📌 EPIC 9.1 — End-to-End Tests (повний pipeline)

> **AI агенте:** E2E тести перевіряють повний цикл від TrendSignal до PipelineResult.
> Всі зовнішні залежності замоковані (YouTube API, Ollama, Edge-TTS).
> Використовувати pytest fixtures з `tmp_path` для ізоляції файлів.
> Parametrize: різні сценарії (dry_run, gate_fail, compliance_fail, success).

**Матриця E2E сценаріїв:**
```
┌─────────────────┬──────────┬───────────┬──────────────┬─────────────┐
│ Сценарій        │ DRY_RUN  │ Bayes Gate│ Similarity   │ Очікуваний  │
│                 │          │           │ Gate         │ Результат   │
├─────────────────┼──────────┼───────────┼──────────────┼─────────────┤
│ happy_path      │ false    │ pass      │ pass         │ published   │
│ dry_run         │ true     │ pass      │ pass         │ skipped     │
│ bayes_fail      │ false    │ fail      │ pass         │ blocked     │
│ similarity_fail │ false    │ pass      │ fail (>0.85) │ blocked     │
│ llm_down        │ false    │ pass      │ pass         │ template_fb │
│ tts_down        │ false    │ pass      │ pass         │ coqui_fb    │
│ quota_exceeded  │ false    │ pass      │ pass         │ synthetic_fb│
│ empty_trends    │ false    │ —         │ —            │ error       │
└─────────────────┴──────────┴───────────┴──────────────┴─────────────┘
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-531 | 🔲 | Створити `tests/e2e/` директорію та `conftest.py` | `tests/e2e/conftest.py` | M | T-309 | — |
| T-532 | 🔲 | Написати E2E fixture: `full_mock_pipeline` (всі залежності mock) | `tests/e2e/conftest.py` | L | T-531 | — |
| T-533 | 🔲 | Тест E2E: `happy_path` → PipelineResult.status == "published" | `tests/e2e/test_e2e_pipeline.py` | L | T-532 | — |
| T-534 | 🔲 | Тест E2E: `dry_run=True` → publish НЕ викликається | `tests/e2e/test_e2e_pipeline.py` | M | T-532 | — |
| T-535 | 🔲 | Тест E2E: Bayes gate fail → status == "blocked_quality" | `tests/e2e/test_e2e_pipeline.py` | M | T-532 | — |
| T-536 | 🔲 | Тест E2E: similarity > 0.85 → status == "blocked_duplicate" | `tests/e2e/test_e2e_pipeline.py` | M | T-532 | — |
| T-537 | 🔲 | Тест E2E: Ollama down → fallback до template → pipeline продовжується | `tests/e2e/test_e2e_pipeline.py` | L | T-532 | — |
| T-538 | 🔲 | Тест E2E: Edge-TTS down → fallback до Coqui → pipeline продовжується | `tests/e2e/test_e2e_pipeline.py` | L | T-532 | — |
| T-539 | 🔲 | Тест E2E: quota exceeded → synthetic fallback → pipeline продовжується | `tests/e2e/test_e2e_pipeline.py` | M | T-532 | — |
| T-540 | 🔲 | Тест E2E: порожні trends → PipelineResult.status == "error" | `tests/e2e/test_e2e_pipeline.py` | S | T-532 | — |
| T-541 | 🔲 | Тест E2E: AuditLog містить запис після кожного publish attempt | `tests/e2e/test_e2e_pipeline.py` | M | T-532 | — |
| T-542 | 🔲 | Тест E2E: EvidenceChain цілісна після повного run | `tests/e2e/test_e2e_pipeline.py` | M | T-532 | — |

---

### 📌 EPIC 9.2 — Property-Based Testing (Hypothesis)

> **AI агенте:** Property-based тести генерують тисячі випадкових вхідних даних
> і перевіряють інваріанти. Це знаходить edge cases яких ти не очікуєш.
> Приклад: для будь-якого TrendSignal → TrendAnalyzer завжди повертає sorted list.

**Ключові інваріанти для перевірки:**
```python
from hypothesis import given, strategies as st

# Інваріант 1: TrendAnalyzer завжди повертає відсортований результат
@given(st.lists(st.floats(0.0, 1.0, allow_nan=False), min_size=3, max_size=50))
def test_scores_always_sorted(raw_scores):
    signals = [TrendSignal(keyword=f"kw{i}", raw_score=s) for i, s in enumerate(raw_scores)]
    rankings = analyzer.score_trends(signals)
    scores = [r.score for r in rankings]
    assert scores == sorted(scores, reverse=True)  # ЗАВЖДИ відсортовано!

# Інваріант 2: BayesFilter score завжди в [0.0, 1.0]
@given(st.dictionaries(st.text(), st.floats(0.0, 10.0)))
def test_bayes_score_bounded(features):
    report = filter.decide(ContentPlan(features=features))
    assert 0.0 <= report.score <= 1.0  # ЗАВЖДИ в межах!
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-543 | 🔲 | Додати `hypothesis` до dev залежностей pyproject.toml | `pyproject.toml` | S | T-001 | — |
| T-544 | 🔲 | Property тест: TrendAnalyzer → завжди sorted list (будь-який вхід) | `tests/test_trend_analyzer.py` | M | T-543 | — |
| T-545 | 🔲 | Property тест: BayesFilter score завжди ∈ [0.0, 1.0] | `tests/test_bayes_filter.py` | M | T-543 | — |
| T-546 | 🔲 | Property тест: ctr_score(title) завжди ∈ [0.0, 1.0] | `tests/test_title_generator.py` | M | T-543 | — |
| T-547 | 🔲 | Property тест: SimilarityGate score завжди ∈ [0.0, 1.0] | `tests/test_similarity_gate.py` | M | T-543 | — |
| T-548 | 🔲 | Property тест: UCB1 select() завжди повертає валідну нішу | `tests/test_bandit.py` | M | T-543 | — |
| T-549 | 🔲 | Property тест: content_hash — різні тексти → різні хеші | `tests/test_similarity_gate.py` | M | T-543 | — |
| T-550 | 🔲 | Property тест: TitleGenerator → title довжина ЗАВЖДИ 40–60 символів | `tests/test_title_generator.py` | M | T-543 | — |
| T-551 | 🔲 | Property тест: LRU Cache → get після put ЗАВЖДИ повертає значення (до TTL) | `tests/test_cache.py` | M | T-543 | — |
| T-552 | 🔲 | Property тест: EvidenceChain verify_chain() → True для валідного ланцюга | `tests/test_compliance.py` | M | T-543 | — |

---

### 📌 EPIC 9.3 — Mutation Testing (mutmut)

> **AI агенте:** Mutation testing вбиває "мутантів" (змінює `>` на `>=`, `+` на `-` тощо)
> і перевіряє, чи тести це виявляють. Ціль: mutation score ≥ 80%.
> Запускай лише для критичних модулів (ML, quality) — повний mutmut дуже повільний.

**Що таке мутант:**
```python
# Оригінальний код:
if similarity > self.THRESHOLD:
    return "block"

# Мутант 1 (>=):    якщо тест не впав → тест слабкий!
if similarity >= self.THRESHOLD:
    return "block"

# Мутант 2 (<):     якщо тест не впав → тест слабкий!
if similarity < self.THRESHOLD:
    return "block"

# Мутант 3 (return "pass"): якщо тест не впав → КРИТИЧНА ДІРКА!
if similarity > self.THRESHOLD:
    return "pass"
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-553 | 🔲 | Додати `mutmut` до dev залежностей pyproject.toml | `pyproject.toml` | S | T-001 | — |
| T-554 | 🔲 | Запустити mutmut для `src/ytaimbot_ml/quality/` | CI | L | T-553 | — |
| T-555 | 🔲 | Досягнути mutation score ≥ 80% для `bayes_filter.py` | `tests/test_bayes_filter.py` | L | T-554 | — |
| T-556 | 🔲 | Досягнути mutation score ≥ 80% для `similarity_gate.py` | `tests/test_similarity_gate.py` | L | T-554 | — |
| T-557 | 🔲 | Досягнути mutation score ≥ 80% для `trend_analyzer.py` | `tests/test_trend_analyzer.py` | L | T-554 | — |
| T-558 | 🔲 | Досягнути mutation score ≥ 80% для `bandit.py` | `tests/test_bandit.py` | L | T-554 | — |
| T-559 | 🔲 | Додати mutmut до CI як non-blocking check (warning, не fail) | `.github/workflows/ci.yml` | M | T-554 | — |

---

### 📌 EPIC 9.4 — Load Testing (Locust)

> **AI агенте:** Load test перевіряє чи pipeline витримує 1 запуск/хвилину.
> На Hetzner CX22 (2 vCPU, 4GB RAM) — мета: ≤ 5 хвилин на один run.
> Locust симулює concurrent pipeline runs і вимірює throughput + latency.

**Load Test сценарій:**
```python
from locust import User, task, between

class PipelineUser(User):
    """
    Симулює concurrent pipeline runs.
    wait_time = between(60, 300)  # 1-5 хв між запусками
    """
    wait_time = between(60, 300)

    @task
    def run_pipeline(self):
        """
        Запускає pipeline з mock adapters.
        Вимірює: response_time (ms), throughput (runs/min)
        """
        start = time.time()
        result = pipeline.run(dry_run=True)  # dry_run для load test
        elapsed = (time.time() - start) * 1000
        if result.status == "error":
            self.environment.events.request.fire(
                request_type="pipeline",
                name="run",
                response_time=elapsed,
                response_length=0,
                exception=RuntimeError(result.error)
            )
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-560 | 🔲 | Додати `locust` до dev залежностей pyproject.toml | `pyproject.toml` | S | T-001 | — |
| T-561 | 🔲 | Написати `tests/load/locustfile.py` з PipelineUser | `tests/load/locustfile.py` | L | T-560 | — |
| T-562 | 🔲 | Налаштувати load test параметри: 10 users, 60s ramp-up | `tests/load/locustfile.py` | M | T-561 | — |
| T-563 | 🔲 | Верифікувати: pipeline run ≤ 5 хвилин під навантаженням | `tests/load/locustfile.py` | L | T-562 | — |
| T-564 | 🔲 | Верифікувати: RAM використання ≤ 3.5GB (з резервом на Hetzner CX22) | `tests/load/locustfile.py` | L | T-562 | — |
| T-565 | 🔲 | Верифікувати: error rate < 1% при 10 concurrent users | `tests/load/locustfile.py` | M | T-562 | — |
| T-566 | 🔲 | Задокументувати load test результати у docs/ | `docs/TEST_PLAN.md` | M | T-563 | — |

---

### 📌 EPIC 9.5 — Coverage ≥ 90% та фінальний audit тестів

> **AI агенте:** Мета — 90% coverage для `src/ytaimbot_ml/` та `modules/`.
> Використовуй `pytest --cov=src --cov=modules --cov-report=term-missing`
> щоб побачити які рядки не покриті. Пиши тести для кожного непокритого рядка.

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-567 | 🔲 | Виміряти поточне coverage: `pytest --cov --cov-report=term-missing` | CI | S | T-542 | — |
| T-568 | 🔲 | Покрити непокриті гілки у `trend_analyzer.py` до 90% | `tests/test_trend_analyzer.py` | M | T-567 | — |
| T-569 | 🔲 | Покрити непокриті гілки у `bayes_filter.py` до 90% | `tests/test_bayes_filter.py` | M | T-567 | — |
| T-570 | 🔲 | Покрити непокриті гілки у `orchestrator.py` до 90% | `tests/test_orchestrator.py` | M | T-567 | — |
| T-571 | 🔲 | Покрити непокриті гілки у `feedback/scorer.py` до 90% | `tests/test_feedback_scorer.py` | M | T-567 | — |
| T-572 | 🔲 | Покрити непокриті гілки у `learner/bandit.py` до 90% | `tests/test_bandit.py` | M | T-567 | — |
| T-573 | 🔲 | Покрити непокриті гілки у `quality/similarity_gate.py` до 90% | `tests/test_similarity_gate.py` | M | T-567 | — |
| T-574 | 🔲 | Додати `--cov-fail-under=90` до pyproject.toml pytest config | `pyproject.toml` | S | T-567 | — |
| T-575 | 🔲 | Верифікувати: `pytest --cov` → coverage ≥ 90% (CI block if less) | CI | S | T-574 | — |
| T-576 | 🔲 | Верифікувати: `pytest -q` → 0 failures, 0 errors | CI | S | T-575 | — |
| T-577 | 🔲 | Верифікувати: `pytest` час виконання < 120 секунд (fast test suite) | CI | M | T-575 | — |
| T-578 | 🔲 | Верифікувати: всі тести детерміновані (однаковий результат 3×) | CI | M | T-575 | — |
| T-579 | 🔲 | Запустити повний `pytest -q --tb=short` фінальний run | CI | S | T-578 | — |
| T-580 | 🔲 | Оновити тест-бейдж у README.md (passing/coverage %) | `README.md` | S | T-579 | — |

**Acceptance для PHASE 9 (загалом):**
- [ ] Coverage `src/ + modules/` ≥ 90%
- [ ] E2E: всі 8 сценаріїв з матриці → правильний результат
- [ ] Property тести: 10 інваріантів → жодного counterexample
- [ ] Mutation score ≥ 80% для критичних модулів
- [ ] Load test: ≤ 5 хв pipeline run, ≤ 3.5GB RAM, < 1% error rate
- [ ] `pytest -q` → 0 failures, час < 120s, детермінований

---

═══════════════════════════════════════════════════════════════════
## 📚 PHASE 10: DOCS + FINALIZATION — 🔲 PENDING
═══════════════════════════════════════════════════════════════════

**Ціль:** Фінальна документація, архітектурні діаграми та launch перший $5k місяць.
**Тиждень:** 15–16 | **Пріоритет:** 🟡 Medium
**Залежності:** Phase 10 → всі попередні фази ✅

---

### 📌 EPIC 10.1 — API Documentation (Sphinx + docstrings audit)

> **AI агенте:** Перевір що кожна публічна функція/клас має:
> 1. Docstring (Google style)  2. Type annotations  3. Big-O complexity
> 4. Приклад використання  5. Raises секція (якщо є exceptions)
> Згенеруй HTML документацію через Sphinx → `docs/_build/html/`.

**Стандарт docstring (обов'язковий для всіх публічних методів):**
```python
def score_trends(self, signals: list[TrendSignal]) -> list[TrendRanking]:
    """
    Ранжує TrendSignal за L2 нормою після SVD-трансформації.

    Алгоритм:
        1. Featurize signals → np.ndarray   O(n × d)
        2. Apply fitted SVD → reduced space  O(n × k)
        3. Compute L2 norm per row           O(n × k)
        4. Sort descending                   O(n log n)

    Складність: O(n × d + n log n) де n = сигнали, d = features

    Args:
        signals: Список TrendSignal для ранжування. Мінімум 1 елемент.

    Returns:
        list[TrendRanking]: Відсортований список (найвищий score першим).

    Raises:
        ValueError: Якщо signals порожній.
        NotFittedError: Якщо fit_transform не був викликаний раніше.

    Example:
        >>> rng = make_rng(42)
        >>> analyzer = TrendAnalyzer(rng=rng)
        >>> signals = [TrendSignal(keyword="python", raw_score=0.8)]
        >>> rankings = analyzer.score_trends(signals)
        >>> assert rankings[0].keyword == "python"
    """
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-581 | 🔲 | Audit: перевірити всі публічні методи мають повний docstring | всі `.py` файли | L | T-579 | — |
| T-582 | 🔲 | Додати відсутні docstrings (Big-O + Args + Returns + Example) | `src/ytaimbot_ml/` | L | T-581 | — |
| T-583 | 🔲 | Додати `sphinx`, `sphinx-autodoc` до dev залежностей | `pyproject.toml` | S | T-001 | — |
| T-584 | 🔲 | Налаштувати `docs/conf.py` для Sphinx | `docs/conf.py` | M | T-583 | — |
| T-585 | 🔲 | Згенерувати HTML docs: `sphinx-build -b html docs/ docs/_build/` | `docs/_build/` | M | T-584 | — |
| T-586 | 🔲 | Верифікувати: Sphinx генерує без warnings | CI | S | T-585 | — |

---

### 📌 EPIC 10.2 — Architecture Diagrams (Mermaid)

> **AI агенте:** Mermaid діаграми вбудовані прямо у Markdown — не потрібні зовнішні інструменти.
> GitHub рендерить Mermaid нативно. Оновити всі архітектурні docs.

**Діаграми для створення:**
```
1. Pipeline Flow Diagram (flowchart LR)
2. Class Hierarchy Diagram (classDiagram)
3. Database Schema (erDiagram)
4. Deployment Diagram (C4Context)
5. State Machine: PipelineResult.status (stateDiagram-v2)
6. Sequence: publish flow (sequenceDiagram)
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-587 | 🔲 | Написати Mermaid flowchart: 12-стадійний pipeline | `docs/ARCHITECTURE_DATAFLOW.md` | M | T-585 | — |
| T-588 | 🔲 | Написати Mermaid classDiagram: всі dataclasses + adapters | `docs/ARCHITECTURE_OVERVIEW.md` | M | T-585 | — |
| T-589 | 🔲 | Написати Mermaid erDiagram: SQLite schema (4 таблиці) | `docs/DESIGN_STORAGE_SCHEMA.md` | M | T-585 | — |
| T-590 | 🔲 | Написати Mermaid stateDiagram: PipelineResult.status FSM | `docs/ARCHITECTURE_OVERVIEW.md` | M | T-585 | — |
| T-591 | 🔲 | Написати Mermaid sequenceDiagram: повний publish flow | `docs/ARCHITECTURE_DATAFLOW.md` | L | T-585 | — |
| T-592 | 🔲 | Верифікувати: всі Mermaid діаграми рендеряться на GitHub | `docs/` | S | T-591 | — |

---

### 📌 EPIC 10.3 — Launch Preparation та Revenue Milestone

> **AI агенте:** Фінальний checklist перед першим реальним запуском.
> Ціль: перше відео опубліковано, перший $1 зароблено.
> Після 50 відео (manual review пройдено) → повний автопілот.

**Launch Checklist (виконати по порядку):**
```
PRE-LAUNCH (GitHub Actions CI):
  □ T-593: pytest -q → 0 failures
  □ T-594: docker compose build → образ збирається без помилок
  □ T-595: DRY_RUN=true → перший тестовий run у CI (перевірити logs)
  □ T-596: Перевірити .env — всі секрети встановлені

DEPLOY (Hetzner/DigitalOcean VPS):
  □ T-597: Hetzner CX22 створено, SSH підключення OK
  □ T-598: Docker встановлено, git clone виконано
  □ T-599: .env налаштовано на VPS (YOUTUBE_API_KEY, GROQ_API_KEY)
  □ T-600: docker compose up -d → бот запущений на VPS

POST-LAUNCH:
  □ T-601: Перше відео опубліковано як UNLISTED
  □ T-602: Manual review → перевірити якість
  □ T-603: Перевести на PUBLIC → перший реальний глядач
  □ T-604: Тиждень 1 звіт: CTR, retention, views
  □ T-605: Місяць 1 звіт: revenue, top niches
  □ T-606: 50 відео milestone → увімкнути autopilot
  □ T-607: YPP заявка (1K subs + 4K watch hours)
  □ T-608: Перший $1 → milestone celebration 🎉
  □ T-609: Перший $1K місяць → масштабування
  □ T-610: Перший $5K місяць → ціль досягнута! 🚀
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-593 | 🔲 | Фінальний `pytest -q --tb=short` → 0 failures | CI | S | T-579 | — |
| T-594 | 🔲 | `docker compose build` → образ збирається без помилок | CI/VPS | M | T-449 | — |
| T-595 | 🔲 | Перший dry-run: `YTAIMBOT_DRY_RUN=true python -m modules.orchestrator` | VPS | M | T-594 | — |
| T-596 | 🔲 | Security audit: всі .env значення встановлені, жодного дефолту | `.env` | M | T-500 | — |
| T-597 | 🔲 | Hetzner CX22 створено, SSH підключення OK | Hetzner | L | T-442 | — |
| T-598 | 🔲 | Виконати `deploy.sh v0.1.0` → перший production deploy | Hetzner | L | T-443, T-597 | — |
| T-599 | 🔲 | Верифікувати Prometheus `:9090` + Grafana `:3000` доступні | Hetzner | M | T-457, T-598 | — |
| T-600 | 🔲 | Перший реальний run: `YTAIMBOT_DRY_RUN=false` | Hetzner | XL | T-598 | — |
| T-601 | 🔲 | Верифікувати: перше відео з'явилось у YouTube Studio (UNLISTED) | YouTube | M | T-600 | — |
| T-602 | 🔲 | Manual review #1: перевірити якість title/thumbnail/script | YouTube | M | T-601 | — |
| T-603 | 🔲 | Перевести відео на PUBLIC після manual review | YouTube | S | T-602 | — |
| T-604 | 🔲 | Тиждень 1: зафіксувати CTR, retention_30s, views у docs/ | `docs/WEEKLY_REPORTS/` | M | T-603 | — |
| T-605 | 🔲 | Місяць 1: зафіксувати revenue, top niches, bandit stats | `docs/WEEKLY_REPORTS/` | M | T-604 | — |
| T-606 | 🔲 | 50 відео milestone: вимкнути manual review → повний autopilot | `modules/dashboard/manual_review.py` | M | T-288 | — |
| T-607 | 🔲 | Подати заявку на YouTube Partner Program (YPP) | YouTube | S | T-606 | — |
| T-608 | 🔲 | 🎉 Перший $1 зароблено → milestone у README.md | `README.md` | S | T-607 | — |
| T-609 | 🔲 | Перший $1K/міс → масштабувати: більше ніш, вища частота | Hetzner | M | T-608 | — |
| T-610 | 🔲 | 🚀 Перший $5K/міс → ЦІЛЬ ДОСЯГНУТА! Задокументувати lessons learned | `docs/` | M | T-609 | — |

**Acceptance для PHASE 10 (загалом):**
- [ ] Sphinx docs генеруються без warnings
- [ ] Всі Mermaid діаграми рендеряться на GitHub
- [ ] Перше відео опубліковано на YouTube
- [ ] CTR ≥ 4% (ціль ≥ 6%) за перший місяць
- [ ] Retention 30s ≥ 60% (ціль ≥ 70%)
- [ ] Revenue ≥ $1K/місяць за Місяць 2–3
- [ ] Revenue ≥ $5K/місяць за Місяць 4–6 🚀

---

## 📈 МЕТРИКИ УСПІХУ

| Метрика | Мінімум | Ціль | Вимір |
|---------|---------|------|-------|
| **CTR** | ≥ 4% | ≥ 6% | YouTube Studio |
| **Retention 30s** | ≥ 60% | ≥ 70% | YouTube Analytics |
| **Upload cadence** | 1/3 дні | 1/день | Автоматично |
| **Test coverage** | ≥ 80% | ≥ 90% | pytest --cov |
| **Uptime** | ≥ 99% | ≥ 99.9% | Hetzner monitor |
| **Processing time** | ≤ 10 хв | ≤ 5 хв | logs |
| **Revenue** | $1k/міс | $5k+/міс | AdSense |
| **Bayes precision** | ≥ 80% | ≥ 95% | test_bayes_filter |
| **Trend overlap** | ≥ 80% | ≥ 95% | test_trend_analyzer |
| **Build time CI** | ≤ 3 хв | ≤ 2 хв | GitHub Actions |

---

## 🔗 ГРАФІК ЗАЛЕЖНОСТЕЙ (Dependency Graph)

```
P0 (✅) ─────┬──▶ P1 (Trend Adapters)
              │         │
              │         ▼
              │    P2 (Content Gen) ──▶ P3 (Video Assembly)
              │                               │
              │                               ▼
              │                         P4 (Publishing) ──▶ P5 (Metrics)
              │                                                    │
              └──▶ P7 (DevOps) ◀──────────────────────────────────┤
              │                                                    │
              └──▶ P8 (Security) ◀─────────────────────────────────┤
              │                                                    │
              └──▶ P9 (Testing) ◀──────────────────────────────────┘
                                        │
                                        ▼
                               P6 (RL Learner) ──▶ P10 (Finalize)
```

---

═══════════════════════════════════════════════════════════════════
## 🔬 ALGORITHMS SUPPLEMENT — ДОДАТКОВІ ЗАДАЧІ (T-611–T-640)
═══════════════════════════════════════════════════════════════════

> **AI агенте:** Цей розділ додає просунуті алгоритми яких не вистачало у P1–P10.
> Після огляду виявлено що відсутні: Aho-Corasick, Kalman Filter, Edit Distance,
> ARIMA, Monte Carlo Simulation, Gaussian NB, Greedy Knapsack, PageRank, HyperLogLog, MinHash LSH.
> Ці задачі ПОКРАЩУЮТЬ існуючі компоненти — замінюють або доповнюють їх.

---

### 📌 SUPPLEMENT A — Aho-Corasick (замінює Trie у blocklist)

> **Чому краще за Trie:** Trie шукає слова по одному → O(n_words × len_text).
> Aho-Corasick будує automaton одного разу і шукає ВСІ слова за O(n) — один прохід!
> Критично для blocklist з 5000+ слів.

**Aho-Corasick Automaton:**
```python
# Aho-Corasick — алгоритм Aho і Corasick (1975)
# Базується на KMP + Trie + failure функція
#
# Побудова:  O(sum(len(pattern_i))) — один раз
# Пошук:     O(n + m + z)
#   n = len(text), m = sum(len(patterns)), z = кількість збігів
#
# vs Trie:   O(n_words × n) — значно гірше для великих текстів

from pyahocorasick import Automaton

class AhoCorasickBlocklist:
    def __init__(self, words: list[str]):
        self._auto = Automaton()
        for i, word in enumerate(words):
            self._auto.add_word(word.lower(), (i, word))
        self._auto.make_automaton()   # O(sum(len(words))) — будуємо один раз

    def find_all(self, text: str) -> list[str]:
        """
        O(n + z) де n=len(text), z=кількість збігів
        Повертає всі заблоковані слова що знайдені у тексті
        """
        return [word for _, (_, word) in self._auto.iter(text.lower())]
```

| ID | Статус | Задача | Файл(и) | Склад. | Замінює | Виконано |
|----|--------|--------|---------|--------|--------|---------|
| T-611 | 🔲 | Замінити `BlocklistTrie` на `AhoCorasickBlocklist` | `src/ytaimbot_ml/quality/blocklist.py` | M | T-501 | — |
| T-612 | 🔲 | Додати `pyahocorasick` до pyproject.toml | `pyproject.toml` | S | T-001 | — |
| T-613 | 🔲 | Написати тести: Aho-Corasick O(n) vs Trie O(n×m) benchmark | `tests/test_content_safety.py` | M | T-611 | — |
| T-614 | 🔲 | Тест: 5000-слівний blocklist → один прохід по тексту | `tests/test_content_safety.py` | M | T-613 | — |

---

### 📌 SUPPLEMENT B — Edit Distance / Levenshtein (доповнює SimilarityGate)

> **Чому потрібен:** TF-IDF cosine similarity погано виявляє перефразований контент.
> "5 ways to learn Python" vs "how to start learning Python" — TF-IDF низька схожість,
> але Edit Distance (з нормалізацією) виявить структурну схожість.
> Гібридний підхід: TF-IDF для семантики + Edit Distance для структури.

**Wagner-Fischer Algorithm (DP Edit Distance):**
```python
def levenshtein(s1: str, s2: str) -> int:
    """
    Wagner-Fischer DP алгоритм.
    Складність: O(n × m) час, O(min(n,m)) пам'ять (оптимізована)

    dp[i][j] = мінімальна вартість перетворення s1[:i] → s2[:j]
    Операції: insert=1, delete=1, replace=1 (або 0 якщо символи однакові)
    """
    n, m = len(s1), len(s2)
    # Оптимізація пам'яті: зберігаємо лише два рядки DP
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        curr = [i] + [0] * m
        for j in range(1, m + 1):
            if s1[i-1] == s2[j-1]:
                curr[j] = prev[j-1]           # символи однакові → безкоштовно
            else:
                curr[j] = 1 + min(
                    prev[j],                  # delete
                    curr[j-1],                # insert
                    prev[j-1]                 # replace
                )
        prev = curr
    return prev[m]   # нормалізація: distance / max(n,m) → [0.0, 1.0]
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-615 | 🔲 | Реалізувати `levenshtein(s1, s2)` з оптимізацією пам'яті O(min(n,m)) | `src/ytaimbot_ml/quality/similarity_gate.py` | M | T-270 | — |
| T-616 | 🔲 | Реалізувати `normalized_edit_distance(s1, s2)` → float [0.0, 1.0] | `src/ytaimbot_ml/quality/similarity_gate.py` | S | T-615 | — |
| T-617 | 🔲 | Інтегрувати як hybrid: якщо TF-IDF < 0.5 → fallback до Edit Distance | `src/ytaimbot_ml/quality/similarity_gate.py` | M | T-615, T-273 | — |
| T-618 | 🔲 | Тест: перефразований текст → edit_distance виявляє схожість > 0.7 | `tests/test_similarity_gate.py` | M | T-615 | — |

---

### 📌 SUPPLEMENT C — Kalman Filter (згладжування метрик)

> **Чому потрібен:** CTR та RPM мають шум (1000 views → статистично ненадійно).
> Kalman Filter — оптимальний лінійний estimator для зашумлених вимірювань.
> Значно краще за EMA: адаптує uncertainty (Kalman gain) автоматично.

**Scalar Kalman Filter:**
```python
class ScalarKalmanFilter:
    """
    Kalman Filter для скалярного часового ряду (CTR, RPM, retention).
    Складність: O(1) per update — ідеально для streaming metrics

    Стан: x (оцінка), P (невизначеність)
    Predict: x = x,           P = P + Q   (процесний шум Q)
    Update:  K = P/(P+R)      (Kalman gain)
             x = x + K*(z-x)  (корекція вимірюванням z)
             P = (1-K)*P       (оновлення невизначеності)

    Перевага над EMA:
    - EMA: фіксований alpha незалежно від якості вимірювання
    - Kalman: gain адаптується → при малій вибірці більше вірить прогнозу,
              при великій вибірці більше вірить вимірюванню
    """
    def __init__(self, process_var: float = 1e-3,
                       measurement_var: float = 0.1,
                       initial_estimate: float = 0.05):
        self.x = initial_estimate   # початкова оцінка (avg CTR ~5%)
        self.P = 1.0                # початкова невизначеність
        self.Q = process_var        # шум процесу (наскільки швидко змінюється CTR)
        self.R = measurement_var    # шум вимірювання (статистична помилка)

    def update(self, measurement: float) -> float:  # O(1)
        self.P += self.Q                            # predict
        K = self.P / (self.P + self.R)             # Kalman gain
        self.x += K * (measurement - self.x)       # correct
        self.P *= (1 - K)                          # update uncertainty
        return self.x
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-619 | 🔲 | Реалізувати `ScalarKalmanFilter` клас | `src/ytaimbot_ml/utils/kalman.py` | M | T-003 | — |
| T-620 | 🔲 | Інтегрувати Kalman у `MetricsCollector` для CTR/RPM/retention | `modules/metrics_collector.py` | M | T-619, T-327 | — |
| T-621 | 🔲 | Замінити raw metrics у `FeedbackScorer._performance_signal()` на Kalman-filtered | `src/ytaimbot_ml/feedback/scorer.py` | M | T-619, T-339 | — |
| T-622 | 🔲 | Тест: Kalman filter зменшує variance на 50%+ vs raw metrics | `tests/test_kalman.py` | M | T-619 | — |
| T-623 | 🔲 | Тест: після 10 спостережень Kalman estimate ближче до true value ніж EMA | `tests/test_kalman.py` | M | T-619 | — |

---

### 📌 SUPPLEMENT D — ARIMA (прогнозування трендів)

> **Чому потрібен:** ARIMA = AutoRegressive Integrated Moving Average.
> YouTube тренди мають сезонність (тижнева, місячна), ARIMA її враховує.
> Дозволяє передбачати які ніші будуть трендити НАСТУПНОГО ТИЖНЯ.
> Використовуємо `statsmodels.tsa.arima.model.ARIMA`.

**ARIMA(p,d,q) інтерпретація:**
```python
from statsmodels.tsa.arima.model import ARIMA
import numpy as np

class TrendForecaster:
    """
    ARIMA для прогнозування trend scores наступного тижня.
    Складність: O(n × (p+q)^2) навчання, O(p+q) прогноз

    Параметри ARIMA(p, d, q):
      p = порядок авторегресії (AR) — скільки минулих значень враховувати
      d = порядок інтеграції (I)   — скільки разів різниця для стаціонарності
      q = порядок ковзного середнього (MA) — вплив минулих помилок

    Для YouTube трендів: ARIMA(1, 1, 1) — початкова оцінка
    Вибір параметрів: AIC (Akaike Information Criterion) → min AIC

    Сезонність: SARIMA(1,1,1)(1,1,0)[7] — тижнева сезонність
    """
    def fit(self, history: list[float]) -> None:
        self._model = ARIMA(history, order=(1, 1, 1))
        self._result = self._model.fit()   # O(n × (p+q)^2)

    def forecast(self, steps: int = 7) -> np.ndarray:
        """Прогнозує наступні `steps` значень → O(steps × (p+q))"""
        return self._result.forecast(steps=steps)
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-624 | 🔲 | Додати `statsmodels` до pyproject.toml | `pyproject.toml` | S | T-001 | — |
| T-625 | 🔲 | Реалізувати `TrendForecaster` клас (ARIMA(1,1,1)) | `src/ytaimbot_ml/feedback/forecaster.py` | L | T-338, T-624 | — |
| T-626 | 🔲 | Реалізувати `fit(history)` → навчання на останніх 30 точках | `src/ytaimbot_ml/feedback/forecaster.py` | M | T-625 | — |
| T-627 | 🔲 | Реалізувати `forecast(steps=7)` → np.ndarray прогноз | `src/ytaimbot_ml/feedback/forecaster.py` | M | T-625 | — |
| T-628 | 🔲 | Інтегрувати TrendForecaster у WeeklyReportGenerator | `modules/reporting/weekly_report.py` | M | T-625, T-361 | — |
| T-629 | 🔲 | Тест: forecast на відомому синусоїдальному ряді → MAE < 10% | `tests/test_trend_forecaster.py` | M | T-625 | — |

---

### 📌 SUPPLEMENT E — Monte Carlo Simulation (прогноз доходу)

> **Чому потрібен:** Дохід $5K/міс — невизначена ціль. Monte Carlo дає
> діапазон можливих результатів з ймовірностями (confidence intervals).
> Симулюємо 10,000 сценаріїв: різні CTR, RPM, views → розподіл доходів.
> Це не gambling — це статистично обґрунтований бізнес-план.

**Monte Carlo Revenue Simulation:**
```python
class MonteCarloRevenueSimulator:
    """
    Monte Carlo simulation для прогнозу місячного доходу.
    Складність: O(n_simulations × n_videos)

    Параметри (розподіли на основі реальних YouTube даних):
      views_per_video ~ LogNormal(mu=7.5, sigma=1.2)   # медіана ~1800 views
      ctr             ~ Beta(alpha=2, beta=30)          # медіана ~6%
      rpm             ~ LogNormal(mu=0.5, sigma=0.8)   # медіана ~$1.6/1K
      retention_30s   ~ Beta(alpha=5, beta=5)          # медіана ~50%

    Модель доходу:
      revenue_i = views_i × rpm_i / 1000

    Aggregate (місяць = 30 відео):
      monthly_revenue = sum(revenue_i for i in range(30))
    """
    def simulate(self, n_simulations: int = 10_000,
                        n_videos_per_month: int = 30,
                        rng: np.random.Generator = None) -> SimulationResult:
        revenues = []
        for _ in range(n_simulations):                 # O(n_simulations)
            monthly = 0.0
            for _ in range(n_videos_per_month):        # O(n_videos)
                views = rng.lognormal(7.5, 1.2)
                rpm   = rng.lognormal(0.5, 0.8)
                monthly += views * rpm / 1000
            revenues.append(monthly)

        arr = np.array(revenues)
        return SimulationResult(
            median=np.median(arr),                     # O(n log n)
            p10=np.percentile(arr, 10),                # 10% шанс менше цього
            p90=np.percentile(arr, 90),                # 90% шанс менше цього
            prob_5k=np.mean(arr >= 5000),              # P(revenue ≥ $5K)
        )
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-630 | 🔲 | Створити `SimulationResult` dataclass у schemas.py | `src/ytaimbot_ml/schemas.py` | S | T-002 | — |
| T-631 | 🔲 | Реалізувати `MonteCarloRevenueSimulator` клас | `src/ytaimbot_ml/feedback/monte_carlo.py` | L | T-338, T-630 | — |
| T-632 | 🔲 | Реалізувати `simulate(n_simulations=10_000)` → SimulationResult | `src/ytaimbot_ml/feedback/monte_carlo.py` | L | T-631 | — |
| T-633 | 🔲 | Інтегрувати у WeeklyReport: показувати P(revenue ≥ $5K) | `modules/reporting/weekly_report.py` | M | T-631, T-361 | — |
| T-634 | 🔲 | Тест: 10K симуляцій → P(revenue > 0) ≈ 1.0 (детермінований seed) | `tests/test_monte_carlo.py` | M | T-631 | — |
| T-635 | 🔲 | Тест: p10 < median < p90 (базова санітарна перевірка) | `tests/test_monte_carlo.py` | S | T-631 | — |

---

### 📌 SUPPLEMENT F — Gaussian NB Enhancement + PageRank + HyperLogLog

> **AI агенте:** Три невеликих покращення для підвищення якості коду.

**Gaussian Naive Bayes** — покращення BayesQualityFilter:
```python
# Поточний BayesFilter: дискретний Naive Bayes (категоріальні ознаки)
# Покращення: Gaussian NB для неперервних ознак (raw_score, ctr_estimate)
#
# P(x_i | C) = (1/√(2π σ²)) × exp(-(x_i - μ)²/(2σ²))
#
# Перевага: не потрібна дискретизація неперервних ознак
# Складність: O(n_features) — та ж що і дискретний NB
```

**PageRank для keyword важливості:**
```python
# Keyword Graph: вузол = keyword, ребро = co-occurrence у топ відео
# PageRank визначає "авторитетність" кожного keyword
#
# PR(u) = (1-d) + d × Σ(PR(v) / L(v))
# d = 0.85 (damping factor), L(v) = out-degree вузла v
# Складність: O(k × E) де k = ітерації (~20), E = ребра
# Збіжність: зазвичай < 20 ітерацій
```

**HyperLogLog для unique keyword counting:**
```python
# HyperLogLog оцінює кількість унікальних keywords без збереження всіх
# Точність: ±1.5% при 1.2KB пам'яті (vs O(n) для точного підрахунку)
# Алгоритм Flajolet-Martin з покращенням HyperLogLog++
# Застосування: скільки унікальних keywords використано за місяць?
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-636 | 🔲 | Розширити `BayesQualityFilter` Gaussian likelihood для float ознак | `src/ytaimbot_ml/quality/bayes_filter.py` | L | T-004 | — |
| T-637 | 🔲 | Тест: Gaussian NB точніше для float features ніж дискретний NB | `tests/test_bayes_filter.py` | M | T-636 | — |
| T-638 | 🔲 | Реалізувати `PageRankKeywordScorer` (замінює `relevance_score` у SEO) | `src/ytaimbot_ml/seo/optimizer.py` | L | T-203 | — |
| T-639 | 🔲 | Тест: PageRank keyword scores стабільно збігаються (< 20 ітерацій) | `tests/test_seo_optimizer.py` | M | T-638 | — |
| T-640 | 🔲 | Реалізувати `HyperLogLogCounter` для підрахунку унікальних keywords | `src/ytaimbot_ml/utils/hyperloglog.py` | M | T-005 | — |

---

═══════════════════════════════════════════════════════════════════
---

### 📌 SUPPLEMENT G — Greedy Algorithms (жадібні алгоритми)

> **AI агенте:** Greedy = на кожному кроці обираємо локально найкращий варіант.
> ДОВЕДЕНО оптимальні для: Fractional Knapsack, Activity Selection, Huffman, Maximum Coverage (≥63% OPT).
> НЕ оптимальні для: 0/1 Knapsack, TSP — там потрібен DP або точний пошук.

**Greedy Maximum Coverage для SEO keywords:**
```python
def greedy_max_coverage(candidates: list[str],
                        coverage_sets: dict[str, set[str]],
                        budget: int = 10) -> list[str]:
    """
    Задача Maximum Coverage: обрати budget ключових слів що покривають
    якомога більше унікальних пошукових запитів.

    Жадібна апроксимація:
    1. Обираємо keyword з найбільшим marginal gain (нові покриті запити)
    2. Оновлюємо множину покритих запитів
    3. Повторюємо budget разів

    Гарантія: результат ≥ (1 - 1/e) ≈ 63% від оптимального
    Складність: O(budget × n) де n = кількість кандидатів

    Приклад:
    candidates = ["python tutorial", "python beginner", "learn python"]
    coverage = {"python tutorial": {"how to python", "python course"},
                "learn python":    {"how to python", "python for free"}}
    greedy_select(candidates, coverage, budget=1) → ["python tutorial"]
    # покриває {"how to python", "python course"} — більше ніж інші
    """
    selected, covered = [], set()
    for _ in range(budget):                              # O(budget)
        best, best_gain = None, -1
        for kw in candidates:
            if kw in selected:
                continue
            gain = len(coverage_sets.get(kw, set()) - covered)  # O(|set|)
            if gain > best_gain:
                best, best_gain = kw, gain
        if best is None or best_gain == 0:
            break
        selected.append(best)
        covered |= coverage_sets.get(best, set())        # O(|set|)
    return selected
```

**Activity Selection (Greedy) для розкладу завантажень:**
```python
def activity_selection(jobs: list[UploadJob]) -> list[UploadJob]:
    """
    Класична задача Activity Selection: максимальна кількість
    несумісних задач (кожна займає часовий слот).
    ДОВЕДЕНО оптимальний жадібний алгоритм:
    Сортуємо за finish_time → завжди обираємо задачу з найраннішим кінцем.

    Складність: O(n log n) — сортування домінує
    Оптимальність: ТОЧНО оптимальний (не просто апроксимація!)

    Застосування: вибрати максимальну кількість відео для публікації
    у межах YouTube quota windows (кожне відео займає quota-slot).
    """
    sorted_jobs = sorted(jobs, key=lambda j: j.finish_time)  # O(n log n)
    selected, last_finish = [], -1
    for job in sorted_jobs:                                   # O(n)
        if job.start_time >= last_finish:
            selected.append(job)
            last_finish = job.finish_time                     # O(1)
    return selected  # максимальна кількість сумісних завантажень
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-641 | 🔲 | Реалізувати `greedy_max_coverage(candidates, coverage_sets, budget)` | `src/ytaimbot_ml/seo/optimizer.py` | L | T-201 | — |
| T-642 | 🔲 | Довести в docstring: greedy ≥ (1-1/e)×OPT для submodular functions | `src/ytaimbot_ml/seo/optimizer.py` | M | T-641 | — |
| T-643 | 🔲 | Реалізувати `fractional_knapsack(items, capacity)` для token budget | `src/ytaimbot_ml/content/generator.py` | L | T-125 | — |
| T-644 | 🔲 | Замінити DP token budget на `fractional_knapsack` у ScriptGenerator | `src/ytaimbot_ml/content/generator.py` | M | T-643 | — |
| T-645 | 🔲 | Реалізувати `activity_selection(jobs)` для upload scheduling | `modules/scheduler.py` | L | T-295 | — |
| T-646 | 🔲 | Замінити Priority Queue scheduler на `activity_selection` де доцільно | `modules/scheduler.py` | M | T-645 | — |
| T-647 | 🔲 | Реалізувати `huffman_encode(text)` для стиснення скриптів у storage | `src/ytaimbot_ml/utils/compression.py` | L | T-311 | — |
| T-648 | 🔲 | Написати тести для Greedy алгоритмів | `tests/test_greedy.py` | M | T-641 | — |
| T-649 | 🔲 | Тест: `greedy_max_coverage` покриває ≥ 63% від exhaustive optimal | `tests/test_greedy.py` | L | T-648 | — |
| T-650 | 🔲 | Тест: `fractional_knapsack` — сума ваг ≤ capacity, value максимальна | `tests/test_greedy.py` | M | T-648 | — |
| T-651 | 🔲 | Тест: `activity_selection` повертає максимальну кількість задач | `tests/test_greedy.py` | M | T-648 | — |
| T-652 | 🔲 | Тест: `huffman_encode` → стиснений розмір < оригінальний | `tests/test_greedy.py` | M | T-648 | — |

---

### 📌 SUPPLEMENT H — Graph Algorithms: Dijkstra + Union-Find (DSU)

> **AI агенте:** YouTube ніші — це граф. Dijkstra — оптимальний маршрут між темами.
> Union-Find — кластеризація ніш за схожістю (уникаємо канібалізму аудиторії).
> Обидва алгоритми доповнюють UCB1 Bandit у Phase 6.

**Dijkstra для Topic Content Graph:**
```python
import heapq

class TopicGraph:
    """
    Граф тем: вузол = YouTube ніша, ребро = аудиторне перекриття.
    Вага ребра w(u,v) = 1 - cosine_sim(u_vec, v_vec) ∈ [0.0, 1.0]
    Менша вага = більш пов'язані теми (легше конвертувати аудиторію).

    Dijkstra: найкоротший шлях = оптимальна серія відео
    від "beginner python" до "advanced python ML" без втрати аудиторії.

    Складність: O((V + E) log V) з min-heap
    де V = кількість ніш (~50), E = зв'язки (~500)
    """
    def shortest_content_path(self, start: str, end: str) -> list[str]:
        dist = {v: float('inf') for v in self._adj}     # O(V)
        dist[start] = 0.0
        heap = [(0.0, start)]
        prev: dict[str, str] = {}

        while heap:
            d, u = heapq.heappop(heap)                   # O(log V)
            if d > dist[u]:
                continue                                  # stale entry
            for v, weight in self._adj[u].items():       # O(deg(u))
                new_dist = dist[u] + weight
                if new_dist < dist[v]:
                    dist[v] = new_dist
                    prev[v] = u
                    heapq.heappush(heap, (new_dist, v))  # O(log V)

        # Відновлення шляху через backtracking O(path_len)
        path, cur = [], end
        while cur in prev:
            path.append(cur)
            cur = prev[cur]
        return list(reversed([start] + path))
```

**Union-Find (DSU) з path compression + union by rank:**
```python
class NicheDSU:
    """
    Disjoint Set Union для кластеризації пов'язаних YouTube ніш.
    Дві ніші об'єднуємо якщо cosine_similarity > threshold (default: 0.7).

    Операції — майже O(1) завдяки двом оптимізаціям:
    1. Path Compression: find(x) скорочує шлях до кореня → O(α(n))
    2. Union by Rank:    менше дерево приєднується до більшого → O(α(n))
    α(n) = inverse Ackermann function ≈ 4 для всіх практичних n

    Застосування: якщо "Python tips" та "Python tricks" в одному кластері
    → не публікуємо обидва за тиждень (аудиторний канібалізм!)
    """
    def find(self, x: str) -> str:           # O(α(n)) amortized
        if self._parent[x] != x:
            self._parent[x] = self.find(self._parent[x])  # path compression
        return self._parent[x]

    def union(self, x: str, y: str) -> bool:  # O(α(n)) amortized
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False                       # вже в одному кластері
        if self._rank[rx] < self._rank[ry]:
            rx, ry = ry, rx
        self._parent[ry] = rx                  # union by rank
        if self._rank[rx] == self._rank[ry]:
            self._rank[rx] += 1
        return True                            # об'єднано

    def same_cluster(self, x: str, y: str) -> bool:
        return self.find(x) == self.find(y)    # O(α(n))
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-653 | 🔲 | Реалізувати `TopicGraph` клас (adjacency dict) | `src/ytaimbot_ml/learner/topic_graph.py` | L | T-381 | — |
| T-654 | 🔲 | Реалізувати `add_edge(u, v, similarity)` → weight = 1 - sim | `src/ytaimbot_ml/learner/topic_graph.py` | S | T-653 | — |
| T-655 | 🔲 | Реалізувати `shortest_content_path(start, end)` → list[str] (Dijkstra) | `src/ytaimbot_ml/learner/topic_graph.py` | L | T-653 | — |
| T-656 | 🔲 | Реалізувати `build_from_trends(signals, analyzer)` → TopicGraph | `src/ytaimbot_ml/learner/topic_graph.py` | M | T-653, T-003 | — |
| T-657 | 🔲 | Реалізувати `NicheDSU` клас (path compression + union by rank) | `src/ytaimbot_ml/learner/topic_graph.py` | L | T-653 | — |
| T-658 | 🔲 | Реалізувати `cluster_all(signals, threshold=0.7)` → list[set[str]] | `src/ytaimbot_ml/learner/topic_graph.py` | M | T-657 | — |
| T-659 | 🔲 | Інтегрувати NicheDSU у Pipeline — блокувати кластерний канібалізм | `modules/orchestrator.py` | M | T-657, T-008 | — |
| T-660 | 🔲 | Написати тести для TopicGraph + NicheDSU | `tests/test_topic_graph.py` | M | T-653 | — |
| T-661 | 🔲 | Тест: Dijkstra — правильний shortest path (hand-crafted граф) | `tests/test_topic_graph.py` | M | T-660 | — |
| T-662 | 🔲 | Тест: DSU union(A,B); find(A)==find(B) — в одному кластері | `tests/test_topic_graph.py` | S | T-660 | — |
| T-663 | 🔲 | Тест: path compression — глибина дерева ≤ 2 після 100 union | `tests/test_topic_graph.py` | M | T-660 | — |

---

### 📌 SUPPLEMENT I — Fenwick Tree + Simulated Annealing + Newton-Raphson

> **AI агенте:** Три потужні інструменти для advanced operations.
> Fenwick Tree: O(log n) range queries для метрик (замість O(n) prefix sum).
> Simulated Annealing: глобальна оптимізація гіперпараметрів (уникає local minima).
> Newton-Raphson: квадратична збіжність для числової оптимізації EMA alpha.

**Fenwick Tree (Binary Indexed Tree):**
```python
class FenwickTree:
    """
    BIT для ефективних prefix sum запитів з point updates.
    Зберігає часткові суми у спеціальній структурі.

    Ключова ідея: lowbit(i) = i & (-i) — найменший встановлений біт.
    Кожен вузол i відповідає за діапазон [i - lowbit(i) + 1, i].

    Складність:
    update(i, delta):    O(log n)  — оновлення точки
    prefix_sum(i):       O(log n)  — сума [1..i]
    range_sum(l, r):     O(log n)  — сума [l..r]
    vs наївний масив:    O(n) для prefix_sum або O(n) для update

    Застосування у YTAIMBot:
    daily_ctr_tree.update(day, new_ctr_value)    # щодня
    weekly_avg = daily_ctr_tree.range_sum(1, 7) / 7  # за тиждень
    """
    def __init__(self, n: int):
        self._n = n
        self._t = [0.0] * (n + 1)

    def update(self, i: int, delta: float) -> None:  # O(log n)
        while i <= self._n:
            self._t[i] += delta
            i += i & (-i)           # lowbit: наступний відповідальний вузол

    def prefix_sum(self, i: int) -> float:           # O(log n)
        s = 0.0
        while i > 0:
            s += self._t[i]
            i -= i & (-i)           # lowbit: батьківський вузол
        return s

    def range_sum(self, l: int, r: int) -> float:    # O(log n)
        return self.prefix_sum(r) - self.prefix_sum(l - 1)
```

**Simulated Annealing для гіперпараметрів:**
```python
def simulated_annealing(loss_fn: Callable[[dict], float],
                        params: dict[str, float],
                        T0: float = 1.0,
                        T_min: float = 1e-4,
                        cooling: float = 0.995,
                        n_iter: int = 5_000,
                        rng: np.random.Generator = None) -> dict:
    """
    SA для пошуку оптимальних гіперпараметрів.
    Уникає локальних мінімумів через probabilistic acceptance.

    Схема охолодження (геометрична): T_k = T0 × cooling^k
    Критерій Метрополіса: P(accept worse) = exp(-ΔL / T)

    Застосування у YTAIMBot:
    - Підібрати UCB1.C (exploration constant)
    - Підібрати EMA.alpha (learning rate)
    - Підібрати PPO.epsilon (clipping threshold)

    Складність: O(n_iter) — кожна ітерація O(1) для простих loss_fn
    """
    best, best_loss = params.copy(), loss_fn(params)
    current, T = params.copy(), T0
    rng = rng or np.random.default_rng(42)

    while T > T_min:                                    # O(n_iter)
        candidate = {
            k: v + rng.normal(0, T * 0.1)              # perturbation ~ N(0, T)
            for k, v in current.items()
        }
        delta = loss_fn(candidate) - loss_fn(current)  # O(loss_fn)
        if delta < 0 or rng.random() < np.exp(-delta / T):
            current = candidate
            if loss_fn(current) < best_loss:
                best, best_loss = current.copy(), loss_fn(current)
        T *= cooling                                    # O(1) cooling step
    return best
```

**Newton-Raphson для підгонки EMA alpha:**
```python
def newton_raphson(f: Callable[[float], float],
                   df: Callable[[float], float],
                   x0: float = 0.3,
                   tol: float = 1e-8,
                   max_iter: int = 50) -> float:
    """
    Метод Ньютона для пошуку оптимального EMA alpha.
    Квадратична збіжність: похибка зменшується як (похибка)² кожної ітерації!

    Задача: знайти alpha що мінімізує MSE між EMA прогнозом та реальними метриками.
    f(alpha)  = d MSE / d alpha = 0  ← ставимо похідну в нуль
    df(alpha) = d² MSE / d alpha²   ← друга похідна

    Ітерація: alpha_{n+1} = alpha_n - f(alpha_n) / df(alpha_n)

    Збіжність: зазвичай < 10 ітерацій (vs бісекція: ~50 ітерацій)
    Складність: O(max_iter × cost(f)) — зазвичай O(n) для MSE
    """
    x = x0
    for _ in range(max_iter):
        fx, dfx = f(x), df(x)
        if abs(fx) < tol:
            return x                    # збіглось!
        if dfx == 0.0:
            break                       # уникаємо ділення на нуль
        x -= fx / dfx                  # Newton step
    return x                           # повертаємо найкраще знайдене
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-664 | 🔲 | Реалізувати `FenwickTree` клас (lowbit trick) | `src/ytaimbot_ml/utils/data_structures.py` | L | T-005 | — |
| T-665 | 🔲 | Реалізувати `update(i, delta)` та `range_sum(l, r)` → O(log n) | `src/ytaimbot_ml/utils/data_structures.py` | M | T-664 | — |
| T-666 | 🔲 | Інтегрувати FenwickTree у MetricsCollector для CTR range queries | `modules/metrics_collector.py` | M | T-664, T-327 | — |
| T-667 | 🔲 | Реалізувати `simulated_annealing(loss_fn, params, T0, cooling)` | `src/ytaimbot_ml/utils/optimization.py` | L | T-381 | — |
| T-668 | 🔲 | Використати SA для auto-tune UCB1.C на historical data | `src/ytaimbot_ml/learner/bandit.py` | L | T-667, T-382 | — |
| T-669 | 🔲 | Реалізувати `newton_raphson(f, df, x0, tol)` для EMA alpha | `src/ytaimbot_ml/utils/optimization.py` | M | T-667 | — |
| T-670 | 🔲 | Використати Newton-Raphson для підгонки `FeedbackScorer.alpha` | `src/ytaimbot_ml/feedback/scorer.py` | M | T-669, T-339 | — |
| T-671 | 🔲 | Написати тести для FenwickTree | `tests/test_data_structures.py` | M | T-664 | — |
| T-672 | 🔲 | Тест: `range_sum(l,r)` = Σ values[l..r] для всіх l,r (property test) | `tests/test_data_structures.py` | M | T-671 | — |
| T-673 | 🔲 | Тест: FenwickTree O(log n) — benchmark vs naive O(n) prefix sum | `tests/test_data_structures.py` | L | T-671 | — |
| T-674 | 🔲 | Тест: SA знаходить мінімум `(x-3)²` з похибкою < 0.01 | `tests/test_optimization.py` | M | T-667 | — |
| T-675 | 🔲 | Тест: Newton-Raphson збігається за < 10 ітерацій (квадратична) | `tests/test_optimization.py` | M | T-669 | — |

---

### 📌 SUPPLEMENT J — MCTS + Bootstrap CI

> **AI агенте:** MCTS — розширення UCB1 Bandit для довгострокової стратегії.
> UCB1 обирає нішу для ОДНОГО наступного відео.
> MCTS планує СЕРІЮ відео наперед (дерево рішень з симуляцією).
> Bootstrap CI дає статистично обґрунтовані довірчі інтервали без припущень про розподіл.

**Monte Carlo Tree Search (MCTS) для серії відео:**
```python
class MCTSContentPlanner:
    """
    MCTS для планування серії відео (горизонт = 10 відео).
    4 фази стандартного MCTS:

    1. SELECTION:  обходимо дерево за UCT = X̄ + C√(ln N / n_i)
       (X̄ = середній reward ніші, N = total visits, n_i = visits вузла)

    2. EXPANSION:  якщо вузол не повністю розгорнутий → додаємо дитину
       (нова ніша, яку ще не пробували на цьому рівні)

    3. SIMULATION: random rollout від нового вузла до горизонту
       (симулюємо 10 відео з random niches → рахуємо сумарний RPM)

    4. BACKPROP:   оновлюємо X̄ і N для всіх вузлів вгору по дереву

    Складність: O(n_sims × depth × branching_factor)
    Перевага: врахо вує ДОВГОСТРОКОВІ наслідки (аудиторний ріст, YPP)
    """
    @dataclass
    class Node:
        niche: str
        visits: int = 0
        total_reward: float = 0.0
        parent: "MCTSContentPlanner.Node | None" = None
        children: list = field(default_factory=list)

        def uct_score(self, C: float = 1.414) -> float:
            if self.visits == 0:
                return float('inf')         # невідвіданий → пріоритет
            return (self.total_reward / self.visits +
                    C * sqrt(log(self.parent.visits) / self.visits))
```

**Bootstrap Confidence Intervals:**
```python
def bootstrap_ci(data: np.ndarray,
                 stat_fn: Callable = np.mean,
                 n_boot: int = 10_000,
                 alpha: float = 0.05,
                 rng: np.random.Generator = None) -> tuple[float, float]:
    """
    Bootstrap метод: не робить припущень про розподіл даних!
    Resample with replacement → empirical distribution of statistic.

    Перевага над параметричними методами (t-test, z-test):
    - Робастний до outliers
    - Працює для будь-якої статистики (median, trimmed mean, etc.)
    - Не вимагає нормальності

    Складність: O(n_boot × n) де n = розмір вибірки

    Приклад:
    rpm_data = np.array([1.2, 3.4, 2.1, 0.8, 4.2])  # RPM 5 відео
    low, high = bootstrap_ci(rpm_data)  # 95% CI для середнього RPM
    # → (0.9, 3.8) — широкий CI через малу вибірку
    """
    rng = rng or np.random.default_rng(42)
    boot_stats = np.array([
        stat_fn(rng.choice(data, size=len(data), replace=True))
        for _ in range(n_boot)
    ])
    return (float(np.percentile(boot_stats, 100 * alpha / 2)),
            float(np.percentile(boot_stats, 100 * (1 - alpha / 2))))
```

| ID | Статус | Задача | Файл(и) | Склад. | Залежить від | Виконано |
|----|--------|--------|---------|--------|-------------|---------|
| T-676 | 🔲 | Реалізувати `MCTSContentPlanner` клас (4 фази MCTS) | `src/ytaimbot_ml/learner/mcts.py` | XL | T-381 | — |
| T-677 | 🔲 | Реалізувати `_select(node)` → Node (UCT formula з C=√2) | `src/ytaimbot_ml/learner/mcts.py` | L | T-676 | — |
| T-678 | 🔲 | Реалізувати `_expand(node)` → нова дочірня ніша | `src/ytaimbot_ml/learner/mcts.py` | M | T-676 | — |
| T-679 | 🔲 | Реалізувати `_simulate(node, depth=10)` → float (rollout reward) | `src/ytaimbot_ml/learner/mcts.py` | L | T-676 | — |
| T-680 | 🔲 | Реалізувати `_backpropagate(node, reward)` → None | `src/ytaimbot_ml/learner/mcts.py` | M | T-676 | — |
| T-681 | 🔲 | Реалізувати `plan(horizon=10, n_sims=500)` → list[str] (серія ніш) | `src/ytaimbot_ml/learner/mcts.py` | L | T-676 | — |
| T-682 | 🔲 | Реалізувати `bootstrap_ci(data, stat_fn, n_boot, alpha)` | `src/ytaimbot_ml/utils/math_utils.py` | M | T-326 | — |
| T-683 | 🔲 | Інтегрувати bootstrap_ci у WeeklyReport (RPM та CTR intervals) | `modules/reporting/weekly_report.py` | M | T-682, T-361 | — |
| T-684 | 🔲 | Написати тести для MCTSContentPlanner + bootstrap_ci | `tests/test_mcts.py` | M | T-676 | — |
| T-685 | 🔲 | Тест: MCTS після 200 симуляцій — краща ніша відвідується частіше | `tests/test_mcts.py` | L | T-684 | — |
| T-686 | 🔲 | Тест: bootstrap_ci — true mean у CI у ≥95% bootstrap runs | `tests/test_mcts.py` | L | T-684 | — |
| T-687 | 🔲 | Тест: MCTS plan(horizon=10) повертає 10 різних ніш (диверсифікація) | `tests/test_mcts.py` | M | T-684 | — |

**Acceptance для SUPPLEMENT G–J:**
- [ ] Greedy max coverage ≥ (1-1/e)×OPT (тест T-649)
- [ ] Fractional knapsack: сума ваг ≤ capacity (тест T-650)
- [ ] Activity selection: максимальна кількість задач (тест T-651)
- [ ] Dijkstra shortest path: коректний на hand-crafted графі (тест T-661)
- [ ] Union-Find: find(A)==find(B) після union(A,B) (тест T-662)
- [ ] FenwickTree range_sum точний для всіх запитів (тест T-672)
- [ ] SA знаходить мінімум з похибкою < 0.01 (тест T-674)
- [ ] Newton-Raphson збіжність < 10 ітерацій (тест T-675)
- [ ] MCTS: краща ніша відвідується найчастіше (тест T-685)
- [ ] Bootstrap CI: 95% coverage probability (тест T-686)

---

## 📐 ПОВНА ТАБЛИЦЯ АЛГОРИТМІВ ПРОЄКТУ
═══════════════════════════════════════════════════════════════════

> **AI агенте:** Тут зведені ВСІ алгоритми та структури даних що використовуються.
> Перед реалізацією будь-якого компонента — перевіряй цю таблицю.
> Не винаходь велосипед — використовуй правильний алгоритм для задачі.

### Категорія 1: Сортування та пошук

| Алгоритм | Складність | Де використовується | Файл |
|----------|-----------|-------------------|------|
| **QuickSort** (NumPy) | O(n log n) avg | Ранжування трендів | `trend_analyzer.py` |
| **Kahn's Topological Sort** | O(V+E) | Порядок виконання задач | roadmap metadata |
| **Binary Search** | O(log n) | SQLite B-Tree queries | SQLite built-in |
| **Aho-Corasick** | O(n+m+z) | Blocklist multi-pattern | `blocklist.py` |
| **BFS (breadth-first)** | O(V+E) | SEO keyword expansion | `optimizer.py` |
| **Levenshtein Edit Distance** | O(n×m) | Plagiarism detection | `similarity_gate.py` |

### Категорія 2: Структури даних

| Структура | Big-O | Де використовується | Файл |
|-----------|-------|-------------------|------|
| **LRU Cache** (OrderedDict) | O(1) get/put | Trend adapter caching | `cache.py` |
| **Min-Heap** (heapq) | O(log n) push/pop | Upload scheduler | `scheduler.py` |
| **Sliding Window** (deque) | O(1) amortized | Quota tracking | `youtube_search.py` |
| **Bloom Filter** | O(k) | Alert dedup, cache hints | `slack.py` |
| **Trie → Aho-Corasick** | O(m) build | Content safety | `blocklist.py` |
| **Append-Only Log** | O(1) write | Audit trail | `audit_log.py` |
| **Merkle Chain** | O(n) verify | Evidence artifacts | `evidence.py` |
| **HyperLogLog** | O(1) update | Unique keyword count | `hyperloglog.py` |

### Категорія 3: Машинне навчання

| Алгоритм | Складність | Де використовується | Файл |
|----------|-----------|-------------------|------|
| **TruncatedSVD** | O(min(n,d)×n×d) | Trend feature reduction | `trend_analyzer.py` |
| **Naive Bayes (Gaussian NB)** | O(n_features) | Quality gate | `bayes_filter.py` |
| **TF-IDF Vectorization** | O(vocab) | Similarity computation | `similarity_gate.py` |
| **Cosine Similarity** | O(vocab) | Content dedup + template select | `similarity_gate.py` |
| **L2 Normalization** | O(n×k) | Trend scoring | `trend_analyzer.py` |
| **PageRank** | O(k×E) | Keyword importance graph | `optimizer.py` |

### Категорія 4: Статистика та часові ряди

| Алгоритм | Складність | Де використовується | Файл |
|----------|-----------|-------------------|------|
| **EMA** (Exponential Moving Avg) | O(1) | Trend weight update | `scorer.py` |
| **Kalman Filter** | O(1) | Metrics noise smoothing | `kalman.py` |
| **ARIMA(1,1,1)** | O(n×(p+q)²) | Trend forecasting | `forecaster.py` |
| **Chi-Square Test** | O(1) | A/B test significance | `ab_tester.py` |
| **Kolmogorov-Smirnov** | O(n log n) | Distribution drift | `drift_detector.py` |
| **Spearman Correlation** | O(n log n) | Score validation | `scorer.py` |
| **Monte Carlo Simulation** | O(N×V) | Revenue forecasting | `monte_carlo.py` |

### Категорія 5: Reinforcement Learning

| Алгоритм | Складність | Де використовується | Файл |
|----------|-----------|-------------------|------|
| **UCB1 Bandit** | O(k) | Niche selection | `bandit.py` |
| **Softmax Exploration** | O(k) | Temperature-based explore | `bandit.py` |
| **Linear PPO** | O(batch×dim) | Content param optimization | `optimizer.py` |
| **Reservoir Sampling** | O(n) | Streaming data sample | `drift_detector.py` |

### Категорія 6: Алгоритми оптимізації (Greedy + DP + Meta-heuristics)

| Алгоритм | Складність | Де використовується | Файл |
|----------|-----------|-------------------|------|
| **Token Budget DP** (0-1 Knapsack) | O(n×W) | Script section allocation | `generator.py` |
| **Fractional Knapsack** (Greedy) | O(n log n) | Token budget (continuous) | `generator.py` |
| **Greedy Max Coverage** | O(budget×n) | SEO keyword selection | `optimizer.py` |
| **Activity Selection** (Greedy) | O(n log n) | Upload scheduling | `scheduler.py` |
| **Huffman Coding** (Greedy) | O(n log n) | Script compression | `compression.py` |
| **Dijkstra** | O((V+E) log V) | Topic content path | `topic_graph.py` |
| **Union-Find (DSU)** | O(α(n)) ≈ O(1) | Niche clustering | `topic_graph.py` |
| **Simulated Annealing** | O(n_iter) | Hyperparameter tuning | `optimization.py` |
| **Newton-Raphson** | O(max_iter) | EMA alpha fitting | `optimization.py` |
| **Exponential Backoff** | O(2^k) | API retry delays | `retry.py` |
| **Token Bucket** (Greedy refill) | O(1) | Rate limiting | `youtube_publisher.py` |

### Категорія 7: Криптографія та безпека

| Алгоритм | Складність | Де використовується | Файл |
|----------|-----------|-------------------|------|
| **SHA-256** | O(n) | Content hashing | `similarity_gate.py` |
| **HMAC-SHA256** | O(n) | Webhook signature | `youtube_auth.py` |
| **AES-256** | O(n) | Backup encryption | `backup.sh` |
| **Regex DFA** | O(n) | Secret masking in logs | `logging.py` |

### Категорія 8: Медіа та відео

| Алгоритм | Складність | Де використовується | Файл |
|----------|-----------|-------------------|------|
| **FFmpeg DAG** | O(frames×res) | Video assembly | `assembler.py` |
| **Layer Stack (Z-order)** | O(W×H×layers) | Thumbnail generation | `thumbnail.py` |
| **Sliding Window (subtitles)** | O(n_words) | SRT timing | `subtitles.py` |
| **CTR Scoring (weighted sum)** | O(n_features) | Title optimization | `title_generator.py` |

### Категорія 9: Планування та графові алгоритми

| Алгоритм | Складність | Де використовується | Файл |
|----------|-----------|-------------------|------|
| **Dijkstra** | O((V+E) log V) | Optimal content series path | `topic_graph.py` |
| **Kahn's Topological Sort** | O(V+E) | Task dependency ordering | roadmap |
| **BFS** | O(V+E) | SEO keyword expansion | `optimizer.py` |
| **Union-Find DSU** | O(α(n)) | Niche cluster detection | `topic_graph.py` |
| **MCTS** | O(n_sims×depth×branch) | Content series planning | `mcts.py` |

### Категорія 10: Додаткові структури даних

| Структура | Big-O | Де використовується | Файл |
|-----------|-------|-------------------|------|
| **Fenwick Tree (BIT)** | O(log n) update/query | Daily CTR range queries | `data_structures.py` |
| **HyperLogLog** | O(1) update | Unique keyword counting | `hyperloglog.py` |
| **Min-Heap** (heapq) | O(log n) push/pop | Upload scheduler | `scheduler.py` |
| **Bloom Filter** | O(k) | Alert dedup | `slack.py` |
| **LRU Cache** (OrderedDict) | O(1) | Trend adapter caching | `cache.py` |
| **Merkle Chain** | O(n) verify | Evidence artifacts | `evidence.py` |

---

## 📊 ОНОВЛЕНИЙ ЗАГАЛЬНИЙ ПРОГРЕС

| Фаза | Назва | Всього | ✅ Done | 🔲 Pending |
|------|-------|--------|---------|-----------|
| **P0** | Foundation | 15 | 15 | 0 |
| **P1** | Real Trend Adapters | 65 | 0 | 65 |
| **P2** | Content Generation | 80 | 0 | 80 |
| **P3** | Video Assembly + SEO | 80 | 0 | 80 |
| **P4** | Publishing Pipeline | 70 | 0 | 70 |
| **P5** | Metrics Feedback Loop | 70 | 0 | 70 |
| **P6** | RL Learner + Bandit | 60 | 0 | 60 |
| **P7** | Infrastructure + DevOps | 50 | 0 | 50 |
| **P8** | Security + Compliance | 40 | 0 | 40 |
| **P9** | Testing + Coverage | 50 | 0 | 50 |
| **P10** | Docs + Finalization | 30 | 0 | 30 |
| **SUPP A–F** | Algorithms (Aho-Corasick, Kalman, ARIMA, MC, GNB, PageRank) | 30 | 0 | 30 |
| **SUPP G–J** | Algorithms (Greedy, Dijkstra, DSU, BIT, SA, Newton, MCTS, Bootstrap) | 47 | 0 | 47 |
| **TOTAL** | | **687** | **15** | **672** |

---

*Цей файл автоматично оновлюється AI агентом після виконання кожної задачі.*
*Версія 2.0 — доповнено алгоритмами: Aho-Corasick, Kalman Filter, ARIMA, Monte Carlo, Gaussian NB, PageRank, HyperLogLog, Edit Distance (2026-03-10)*
