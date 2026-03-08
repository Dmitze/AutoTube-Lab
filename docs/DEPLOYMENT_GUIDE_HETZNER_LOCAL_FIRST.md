# Deployment Guide: Hetzner Local First

This document outlines the steps to deploy the application.

---

## Prerequisites

### Server Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| Instance | Hetzner CX22 | Hetzner CX32 |
| CPU | 2 vCPU | 4 vCPU |
| RAM | 4 GB | 8 GB |
| Disk | 40 GB SSD | 80 GB SSD |
| OS | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |

---

## 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose plugin
sudo apt install docker-compose-plugin -y

# Verify
docker compose version
```

---

## 2. Deploy the Application

```bash
# Clone the repository
git clone https://github.com/Dmitze/YTAIMBot.git
cd YTAIMBot

# Configure environment
cp .env.example .env
nano .env   # Set YOUTUBE_API_KEY and other variables

# Build and start
docker compose build
docker compose up -d

# Check status
docker compose ps
docker compose logs -f bot
```

---

## 3. Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `YTAIMBOT_DRY_RUN` | `true` | Set to `false` to enable real publishing |
| `YTAIMBOT_SEED` | `42` | Random seed for ML reproducibility |
| `YTAIMBOT_DATA_DIR` | `/app/data` | Data persistence directory |
| `YOUTUBE_API_KEY` | *(empty)* | YouTube Data API v3 key |
| `STORAGE_BACKEND` | `memory` | Storage backend (`memory` or `sqlite`) |

---

## 4. Data Persistence and Backup

```bash
# Data is stored in ./data/ on the host (mounted as volume)
# Back up to Hetzner Object Storage (s3cmd example):
s3cmd sync ./data/ s3://ytaimbot-backup/data/

# Automated daily backup via cron
echo "0 3 * * * cd /home/ubuntu/YTAIMBot && s3cmd sync ./data/ s3://ytaimbot-backup/data/" | crontab -
```

---

## 5. Monitoring

```bash
# Basic health check — check container is running
docker compose ps

# Check last 100 log lines
docker compose logs --tail=100 bot

# Resource usage
docker stats
```

---

## 6. Rollback Procedure

```bash
# Roll back to a previous image
docker compose down
git checkout <previous-tag>
docker compose build
docker compose up -d
```

---

## 7. Updating

```bash
git pull origin main
docker compose build
docker compose up -d
```
