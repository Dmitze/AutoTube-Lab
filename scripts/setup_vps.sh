#!/usr/bin/env bash
# setup_vps.sh — One-shot VPS provisioning for YTAIMBot
# Tested on: Ubuntu 22.04 LTS (Hetzner CX22)
#
# Usage:
#   chmod +x scripts/setup_vps.sh
#   sudo ./scripts/setup_vps.sh
#
# What this does:
#   1. Updates system packages
#   2. Installs Docker + Docker Compose plugin
#   3. Creates /opt/ytaimbot directory
#   4. Clones repository (or pulls latest)
#   5. Creates .env from .env.example
#   6. Adds 2GB swap file
#   7. Sets up systemd watchdog service
#   8. Starts docker-compose
#
# Roadmap: T-551 (Phase 7, EPIC 7.1 Infrastructure)
# Status: 🔲 Pending

set -euo pipefail

# TODO: T-551 — implement full provisioning script
echo "[YTAIMBot] setup_vps.sh — implementation pending (T-551)"

# --- PLACEHOLDER STRUCTURE ---
# apt_update()        { apt-get update && apt-get upgrade -y; }
# install_docker()    { curl -fsSL https://get.docker.com | sh; }
# clone_repo()        { git clone https://github.com/YOUR/YTAIMBot /opt/ytaimbot; }
# setup_env()         { cp .env.example .env && nano .env; }
# add_swap()          { fallocate -l 2G /swapfile && mkswap /swapfile && swapon /swapfile; }
# install_service()   { systemctl enable --now ytaimbot.service; }
# start_containers()  { docker compose up -d --build; }
