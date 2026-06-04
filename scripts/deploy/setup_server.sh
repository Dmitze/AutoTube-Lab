#!/bin/bash
# Phase 7 — setup_server.sh: Hetzner VPS initialization (T-442).
#
# Usage:
#   chmod +x setup_server.sh
#   sudo ./setup_server.sh
#
# Requirements:
#   - Ubuntu 22.04+ (Hetzner CX22)
#   - Root privileges
#
# Complexity: O(n_packages).

set -e # Exit on error

echo "--- YTAIMBot: Server Setup Started ---"

# 1. Update and basic tools
export DEBIAN_FRONTEND=noninteractive
apt-get update && apt-get upgrade -y
apt-get install -y \
    curl \
    git \
    ufw \
    fail2ban \
    python3-pip \
    python3-venv \
    sqlite3 \
    ffmpeg \
    ca-certificates \
    gnupg \
    lsb-release

# 2. Docker Installation
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
fi

# 3. User Setup
USER_NAME="ytaimbot"
if ! id "$USER_NAME" &>/dev/null; then
    echo "Creating user $USER_NAME..."
    useradd -m -s /bin/bash "$USER_NAME"
    usermod -aG docker "$USER_NAME"
fi

# 4. Firewall (UFW)
echo "Configuring Firewall..."
ufw allow 22/tcp    # SSH
ufw allow 8000/tcp  # Dashboard (optional)
ufw allow 9090/tcp  # Prometheus
ufw allow 3000/tcp  # Grafana
ufw --force enable

# 5. Directory Structure
echo "Preparing directories..."
APP_DIR="/home/$USER_NAME/app"
mkdir -p "$APP_DIR/data"/{audio,videos,thumbnails,subtitles,audit,models}
chown -R "$USER_NAME:$USER_NAME" "/home/$USER_NAME/app"

# 6. Logrotate configuration (T-448)
cat <<EOF > /etc/logrotate.d/ytaimbot
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size 100M
    missingok
    delaycompress
    copytruncate
}
EOF

echo "--- YTAIMBot: Server Setup Complete ---"
echo "Reboot recommended before deploying."
