#!/bin/bash
# Phase 7 — deploy.sh: Blue-Green deployment on Hetzner (T-443).
#
# Usage:
#   ./deploy.sh [IMAGE_TAG]
#
# Algorithm
# ---------
# Blue-Green Switching (T-449):
# 1. Identify current active container (e.g. ytaimbot_blue).
# 2. Start target container (e.g. ytaimbot_green) on separate port.
# 3. Health check (health_check.sh).
# 4. Switch traffic (not applicable for worker-only mode, but handles container swap).
# 5. Stop old container.
#
# Complexity: O(image_size + health_check_timeout).

set -e

APP_DIR="/home/ytaimbot/app"
TAG=${1:-latest}
HEALTH_CHECK="./health_check.sh"

echo "--- YTAIMBot: Deployment Started (Tag: $TAG) ---"

# 1. Pull/Build image
# In production, we pull from GHCR. For local/testing, we build.
docker build -t ytaimbot:$TAG .

# 2. Determine Blue/Green
if [ "$(docker ps -q -f name=ytaimbot_blue)" ]; then
    TARGET="green"
    OLD="blue"
else
    TARGET="blue"
    OLD="green"
fi

echo "Deploying to target: $TARGET (replacing $OLD)"

# 3. Start target container
# Use docker-compose with profiles or separate commands
docker run -d \
    --name ytaimbot_$TARGET \
    --restart unless-stopped \
    -v $APP_DIR/data:/app/data \
    -v $APP_DIR/.env:/app/.env \
    ytaimbot:$TAG

# 4. Health Check (T-445)
echo "Running health check on $TARGET..."
if [ -f "$HEALTH_CHECK" ]; then
    bash "$HEALTH_CHECK" ytaimbot_$TARGET || (echo "Health check failed! Rolling back..." && docker stop ytaimbot_$TARGET && docker rm ytaimbot_$TARGET && exit 1)
else
    echo "Warning: health_check.sh not found, skipping..."
    sleep 5 # Grace period
fi

# 5. Cleanup Old
if [ "$(docker ps -aq -f name=ytaimbot_$OLD)" ]; then
    echo "Stopping and removing old container: $OLD"
    docker stop ytaimbot_$OLD
    docker rm ytaimbot_$OLD
fi

# 6. Save Deployment Info
echo "$(date -u) | Deployed $TAG to $TARGET" >> $APP_DIR/deployments.log

echo "--- YTAIMBot: Deployment Complete ($TARGET is now active) ---"
