#!/usr/bin/env bash
# backup.sh — Backup SQLite database and data directory to remote storage
#
# Usage:
#   ./scripts/backup.sh
#
# Backs up:
#   - data/db/ytaimbot.db  → SQLite database (pipeline runs, videos)
#   - data/videos/         → Rendered videos (optional, large)
#
# Destinations (configure via env):
#   BACKUP_TYPE=local      → ./backups/ directory
#   BACKUP_TYPE=hetzner    → Hetzner Storage Box via rsync+SSH
#   BACKUP_TYPE=s3         → S3-compatible (rclone)
#
# Schedule: daily via cron → 0 3 * * * /opt/ytaimbot/scripts/backup.sh
#
# Roadmap: T-552 (Phase 7, EPIC 7.1 Infrastructure)
# Status: 🔲 Pending

set -euo pipefail

# TODO: T-552 — implement backup.sh
echo "[YTAIMBot] backup.sh — implementation pending (T-552)"

# --- PLACEHOLDER STRUCTURE ---
# TIMESTAMP=$(date +%Y%m%d_%H%M%S)
# BACKUP_DIR="./backups/${TIMESTAMP}"
# sqlite3 data/db/ytaimbot.db ".backup ${BACKUP_DIR}/ytaimbot.db"
# tar czf "${BACKUP_DIR}/data.tar.gz" data/videos/ data/thumbnails/
# [[ "$BACKUP_TYPE" == "hetzner" ]] && rsync -avz backups/ user@storage-box:~/ytaimbot/
