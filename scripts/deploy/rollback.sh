#!/bin/bash
# Phase 7 — rollback.sh: Roll back to previous deployment tag (T-444).
#
# Usage:
#   ./rollback.sh
#
# Algorithm
# ---------
# 1. Identify previous tag from deployments.log.
# 2. Deploy that tag.
#
# Complexity: O(n_lines).

set -e

LOG_FILE="/home/ytaimbot/app/deployments.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "Rollback error: $LOG_FILE not found."
    exit 1
fi

# 1. Get the previous tag (second to last entry)
PREVIOUS_TAG=$(tail -n 2 "$LOG_FILE" | head -n 1 | awk '{print $4}')

if [ -z "$PREVIOUS_TAG" ]; then
    echo "Rollback error: No previous tag found in log."
    exit 1
fi

echo "--- YTAIMBot: Rolling Back to $PREVIOUS_TAG ---"

# 2. Execute deployment for that tag
bash ./deploy.sh "$PREVIOUS_TAG"

echo "--- YTAIMBot: Rollback Complete ---"
