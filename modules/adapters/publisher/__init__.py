"""Phase 4 — Publisher adapters sub-package.

Adapters
--------
YouTubeUploader : OAuth2 resumable upload to YouTube Data API v3
QuotaGuard      : Token bucket rate limiter (6 uploads/day max)

Safety rules:
  - YTAIMBOT_DRY_RUN=true → QuotaGuard.allow() always returns False
  - ComplianceReport.decision must be "pass" before any upload
  - Unlisted first (24h) → then set to public via cron

Status: 🔲 Pending — T-371 (Phase 4, EPIC 4.1)
"""
