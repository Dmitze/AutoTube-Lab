# ☁️ Розгортання YTAIMBot на хмарному VPS

> **Ціль:** Запустити бота на хмарному сервері (Hetzner / DigitalOcean) за 30 хвилин.
> **Вартість:** ~$5-6/місяць (Hetzner CX22 або DO Basic Droplet).
> **Вимоги:** Немає локального сервера — все в хмарі.

---

## 📋 Зміст

1. [Вибір хостингу та реєстрація](#1-вибір-хостингу-та-реєстрація)
2. [Створення сервера](#2-створення-сервера)
3. [Підключення по SSH](#3-підключення-по-ssh)
4. [Встановлення Docker](#4-встановлення-docker)
5. [Клонування проєкту](#5-клонування-проєкту)
6. [Налаштування .env](#6-налаштування-env)
7. [Запуск бота](#7-запуск-бота)
8. [Автостарт при перезавантаженні](#8-автостарт-при-перезавантаженні)
9. [Моніторинг логів](#9-моніторинг-логів)
10. [Резервні копії SQLite](#10-резервні-копії-sqlite)
11. [Оновлення бота](#11-оновлення-бота)
12. [Часті проблеми](#12-часті-проблеми)

---

## 1. Вибір хостингу та реєстрація

### Варіант A: Hetzner Cloud (рекомендовано 🇩🇪)

**Ціна:** €3.79/міс (CX22 — 2vCPU, 4GB RAM, 40GB SSD)

```
1. Зайди на https://console.hetzner.cloud
2. Зареєструйся (потрібна кредитна картка або PayPal)
3. Новий проєкт → "YTAIMBot"
```

> **Для України:** Hetzner приймає Visa/Mastercard українських банків.
> Якщо не проходить картка → використай PayPal або Wise.

### Варіант B: DigitalOcean 🌊

**Ціна:** $6/міс (Basic Droplet — 1vCPU, 1GB RAM, 25GB SSD)

```
1. Зайди на https://cloud.digitalocean.com
2. Зареєструйся → $200 кредитів на 60 днів для нових користувачів
3. Create → Droplet
```

> ⚠️ **1GB RAM** може бути замало для Coqui TTS.
> Якщо потрібен offline TTS → вибирай **$12/міс (2GB RAM)**.

---

## 2. Створення сервера

### Hetzner CX22 — покроково

```
Консоль Hetzner → "Add Server"
├── Location:    Nuremberg (EU) або Helsinki
├── OS:          Ubuntu 22.04 LTS
├── Type:        CX22 (2 vCPU, 4 GB RAM) — €3.79/міс
├── SSH Key:     Додати свій публічний ключ (div. нижче)
├── Firewall:    Створити правило (div. нижче)
└── Name:        ytaimbot-prod
```

### Генерація SSH ключа (на своєму ПК)

**Windows (PowerShell):**
```powershell
# Генеруємо ключ
ssh-keygen -t ed25519 -C "ytaimbot@vps" -f "$HOME\.ssh\ytaimbot_vps"

# Виводимо публічний ключ → копіюємо у Hetzner
Get-Content "$HOME\.ssh\ytaimbot_vps.pub"
```

**macOS/Linux:**
```bash
ssh-keygen -t ed25519 -C "ytaimbot@vps" -f ~/.ssh/ytaimbot_vps
cat ~/.ssh/ytaimbot_vps.pub
```

### Правила Firewall (Hetzner)

```
Inbound rules:
├── TCP 22    → 0.0.0.0/0   (SSH)
├── TCP 3000  → твій IP     (Grafana — тільки для тебе!)
├── TCP 9090  → твій IP     (Prometheus — тільки для тебе!)
└── ICMP      → 0.0.0.0/0   (ping)

Outbound rules:
└── All traffic → Allow (бот має виходити в інтернет)
```

---

## 3. Підключення по SSH

```bash
# Windows PowerShell / macOS / Linux
ssh -i ~/.ssh/ytaimbot_vps root@YOUR_SERVER_IP

# Приклад:
ssh -i ~/.ssh/ytaimbot_vps root@65.21.XX.XX
```

**Якщо підключення відмовляє:**
```bash
# Перевір права на ключ (Linux/macOS)
chmod 600 ~/.ssh/ytaimbot_vps

# Windows: правий клік на файл → Властивості → Безпека
# → Видали всіх окрім себе, залиш тільки "Повний доступ" для свого юзера
```

---

## 4. Встановлення Docker

```bash
# Один командний рядок — встановлює все:
curl -fsSL https://get.docker.com | sh

# Додаємо можливість запускати docker без sudo
usermod -aG docker $USER

# Встановлюємо docker-compose v2
apt-get install -y docker-compose-plugin

# Перевірка
docker --version           # Docker version 24.x.x
docker compose version     # Docker Compose version v2.x.x
```

---

## 5. Клонування проєкту

```bash
# Встановлюємо git (якщо нема)
apt-get update && apt-get install -y git

# Клонуємо репозиторій
cd /opt
git clone https://github.com/Dmitze/YTAIMBot.git
cd YTAIMBot

# Перевіряємо структуру
ls -la
```

---

## 6. Налаштування .env

```bash
# Копіюємо шаблон
cp .env.example .env

# Відкриваємо редактор (nano — простий, не потрібен досвід)
nano .env
```

**Заповни ці поля:**

```bash
# =====================================
# ОБОВ'ЯЗКОВІ (без них бот не запуститься)
# =====================================

# Режим роботи: true = тест (нічого не публікує), false = реальна публікація
YTAIMBOT_DRY_RUN=true

# Директорія для даних (SQLite, відео, logs)
YTAIMBOT_DATA_DIR=/opt/ytaimbot-data

# YouTube Data API v3 ключ (для пошуку трендів)
# Отримати: https://console.cloud.google.com → APIs → YouTube Data API v3
YOUTUBE_API_KEY=AIzaSy...

# =====================================
# ДЛЯ ПУБЛІКАЦІЇ ВІДЕО (після тестів)
# =====================================

# OAuth2 credentials для завантаження на YouTube
# Отримати: Google Cloud Console → OAuth 2.0 Client IDs → Desktop app
YOUTUBE_CLIENT_SECRET_PATH=/opt/ytaimbot-data/client_secret.json

# Ліміт публікацій (поки тестуємо → 0)
MAX_UPLOADS_PER_DAY=0

# =====================================
# LLM (для генерації сценарію)
# =====================================

# Варіант 1: Ollama на цьому ж VPS (потрібно 4GB+ RAM)
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:3b

# Варіант 2: Groq API (безкоштовно, швидко, не потрібен Ollama)
# GROQ_API_KEY=gsk_...
# LLM_PROVIDER=groq

# =====================================
# TTS (озвучення)
# =====================================
TTS_LANGUAGE=uk
TTS_VOICE=uk-UA-OstapNeural   # безкоштовний Edge-TTS

# =====================================
# МОНІТОРИНГ (опціонально)
# =====================================
SLACK_WEBHOOK_URL=https://hooks.slack.com/...

# =====================================
# ML ПАРАМЕТРИ (залишити за замовчуванням)
# =====================================
YTAIMBOT_SEED=42
FEEDBACK_ALPHA=0.3
BANDIT_EXPLORATION_C=2.0
DRIFT_THRESHOLD=0.05
```

**Зберегти файл:** `Ctrl+O` → `Enter` → `Ctrl+X`

---

## 7. Запуск бота

### Крок 7.1: Створити директорію для даних

```bash
mkdir -p /opt/ytaimbot-data
chmod 755 /opt/ytaimbot-data
```

### Крок 7.2: Запустити (тільки бот, без Ollama спочатку)

```bash
cd /opt/YTAIMBot

# Зібрати образ та запустити
docker compose up -d bot

# Перевірити що запустилось
docker compose ps
```

**Очікуваний результат:**
```
NAME           IMAGE          STATUS    PORTS
ytaimbot-bot   ytaimbot:dev   Up 2s
```

### Крок 7.3: Перевірити логи

```bash
docker compose logs bot --tail=50
```

**Якщо бачиш:**
```
INFO  Pipeline: dry_run=True, seed=42
INFO  TrendAnalyzer: loaded 10 synthetic signals
INFO  BayesFilter: decision=pass, p_bad=0.12
INFO  Pipeline: status=ok (dry_run, no upload)
```
→ ✅ Бот працює!

---

## 8. Автостарт при перезавантаженні

```bash
# Systemd сервіс для автозапуску
cat > /etc/systemd/system/ytaimbot.service << 'EOF'
[Unit]
Description=YTAIMBot YouTube Pipeline
Requires=docker.service
After=docker.service network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/YTAIMBot
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF

# Активуємо
systemctl daemon-reload
systemctl enable ytaimbot
systemctl start ytaimbot

# Перевіряємо
systemctl status ytaimbot
```

### Розклад (Cron) — один відео на день

```bash
# Редагувати crontab
crontab -e

# Додати рядок (запускати о 09:00 щодня)
0 9 * * * cd /opt/YTAIMBot && docker compose exec -T bot python -m modules.orchestrator >> /opt/ytaimbot-data/cron.log 2>&1
```

---

## 9. Моніторинг логів

### Дивитись логи в реальному часі

```bash
# Всі логи
docker compose logs -f

# Тільки бот
docker compose logs -f bot

# Останні 100 рядків
docker compose logs bot --tail=100
```

### Запустити Grafana дашборд (опціонально)

```bash
# Запустити Prometheus + Grafana
docker compose --profile monitoring up -d

# Відкрити у браузері
# http://YOUR_SERVER_IP:3000
# Login: admin / admin (змінити після першого входу!)
```

---

## 10. Резервні копії SQLite

### Автоматичний щоденний backup

```bash
# Скрипт backup
cat > /opt/backup_ytaimbot.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y-%m-%d)
BACKUP_DIR="/opt/ytaimbot-backups"
DATA_DIR="/opt/ytaimbot-data"

mkdir -p "$BACKUP_DIR"

# SQLite hot backup (thread-safe копія)
sqlite3 "$DATA_DIR/ytaimbot.db" ".backup $BACKUP_DIR/ytaimbot_$DATE.db"

# Стискаємо
gzip "$BACKUP_DIR/ytaimbot_$DATE.db"

# Видаляємо старі backup (залишаємо 30 днів)
find "$BACKUP_DIR" -name "*.db.gz" -mtime +30 -delete

echo "[$DATE] Backup complete: ytaimbot_$DATE.db.gz"
EOF

chmod +x /opt/backup_ytaimbot.sh

# Додати до cron (щодня о 03:00)
(crontab -l; echo "0 3 * * * /opt/backup_ytaimbot.sh >> /opt/ytaimbot-data/backup.log 2>&1") | crontab -
```

### Опціонально: відправляти backup на GitHub Releases або Cloudflare R2

```bash
# Cloudflare R2 (безкоштовно до 10GB/місяць)
# pip install boto3
# aws s3 cp backup.db.gz s3://ytaimbot-backup/ --endpoint-url=https://ACCOUNT.r2.cloudflarestorage.com
```

---

## 11. Оновлення бота

```bash
cd /opt/YTAIMBot

# Отримати нові зміни
git pull origin main

# Перезібрати образ та перезапустити
docker compose down
docker compose build --no-cache
docker compose up -d

# Перевірити
docker compose ps
docker compose logs bot --tail=20
```

---

## 12. Часті проблеми

### ❌ `docker: command not found`
```bash
# Встановити Docker
curl -fsSL https://get.docker.com | sh
```

### ❌ `Permission denied` при запуску Docker
```bash
usermod -aG docker $USER
newgrp docker
```

### ❌ `Out of memory` (Edge TTS не запускається)
```bash
# Перевірити пам'ять
free -h

# Якщо < 1GB free → додати swap
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

### ❌ YouTube API quota exceeded
```bash
# Перевірити квоту
# Google Cloud Console → APIs & Services → YouTube Data API v3 → Quotas
# Безкоштовна квота: 10,000 units/день
# Пошук відео: 100 units
# → можна робити до 100 пошуків/день безкоштовно
```

### ❌ Бот не публікує відео
```bash
# 1. Перевірити DRY_RUN
grep YTAIMBOT_DRY_RUN /opt/YTAIMBot/.env
# Має бути: YTAIMBOT_DRY_RUN=false

# 2. Перевірити OAuth2
docker compose exec bot python -c "from modules.adapters.youtube_auth import check_auth; check_auth()"
```

### ❌ `OLLAMA_URL connection refused`
```bash
# Запустити Ollama окремо
docker compose --profile ollama up -d ollama

# Або використати Groq (безкоштовно, не потрібен VPS!)
# Додати у .env: LLM_PROVIDER=groq, GROQ_API_KEY=gsk_...
```

---

## 💰 Підрахунок вартості

| Сервіс | Ціна/міс | Примітка |
|--------|---------|---------|
| **Hetzner CX22** | €3.79 | VPS (2vCPU, 4GB RAM) |
| **Hetzner CX32** | €5.77 | Якщо потрібен Ollama (4vCPU, 8GB RAM) |
| YouTube Data API | $0 | 10K units/день безкоштовно |
| Edge-TTS | $0 | Безкоштовний Microsoft |
| Groq API (LLM) | $0 | Безкоштовний tier (14K req/день) |
| Cloudflare R2 (backup) | $0 | До 10GB безкоштовно |
| **TOTAL** | **~$4-6/міс** | ≈ 200 грн/міс |

---

## 🚀 Швидка шпаргалка команд

```bash
# Статус
docker compose ps

# Логи в реальному часі
docker compose logs -f bot

# Ручний запуск конвеєра
docker compose exec bot python -m modules.orchestrator

# Зупинити
docker compose down

# Перезапустити
docker compose restart bot

# Зайти в контейнер
docker compose exec bot bash

# Перевірити базу даних
sqlite3 /opt/ytaimbot-data/ytaimbot.db ".tables"
sqlite3 /opt/ytaimbot-data/ytaimbot.db "SELECT * FROM pipeline_runs ORDER BY id DESC LIMIT 5;"

# Backup прямо зараз
/opt/backup_ytaimbot.sh

# Оновити бота
cd /opt/YTAIMBot && git pull && docker compose up -d --build
```

---

## 📞 Допомога

- **Roadmap задач:** [`docs/ROADMAP_AI_AGENT_TASKS.md`](ROADMAP_AI_AGENT_TASKS.md)
- **Runbooks:** [`docs/RUNBOOKS.md`](RUNBOOKS.md)
- **Ризики:** [`docs/RISK_REGISTER.md`](RISK_REGISTER.md)

---

*Версія: 1.0 | Оновлено: 2026-03-10 | Підтримувані ОС: Ubuntu 22.04 LTS*
