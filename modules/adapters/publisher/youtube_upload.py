"""Phase 4 — YouTubeUploader: uploads videos via YouTube Data API v3.

Roadmap tasks: T-371 through T-400 (EPIC 4.1 Publishing Pipeline)
Depends on:   google-auth-oauthlib, google-api-python-client, PublisherAdapter ABC

Configuration:
  YOUTUBE_CLIENT_SECRET_PATH : path to client_secret.json (OAuth2)
  MAX_UPLOADS_PER_DAY        : safety cap (default 0 = disabled)

OAuth2 flow:
  1. Load credentials from YOUTUBE_CLIENT_SECRET_PATH
  2. If expired: refresh via google.auth.transport.requests.Request
  3. Build youtube = googleapiclient.discovery.build("youtube", "v3", ...)

Upload pipeline (Resumable Upload):
  1. QuotaGuard.allow() check          → O(1)
  2. ComplianceReport.decision == "pass" → O(1)
  3. Insert video (unlisted, AI-disclosed) → chunked upload
  4. Poll for processing completion     → O(retry_count)
  5. Set thumbnail                      → O(1)
  6. Schedule public (24h delay)        → O(1)

Algorithm
---------
Resumable upload: chunk_size=256KB, retry on 5xx
Token Bucket (QuotaGuard): allows burst=1, rate=6/day

Status: 🔲 Pending — T-371 (Phase 4)
"""
from __future__ import annotations

from pathlib import Path

# TODO: T-371 — implement YouTubeUploader(PublisherAdapter)
# TODO: T-372 — implement publish(plan, video_path, thumbnail_path) → str (video_id)
# TODO: T-373 — implement _get_credentials() → Credentials (OAuth2)
# TODO: T-374 — implement _upload_video(video_path, metadata) → str
# TODO: T-375 — implement _set_thumbnail(video_id, thumbnail_path) → None
# TODO: T-376 — implement _schedule_public(video_id, delay_hours=24) → None


class YouTubeUploader:
    """TODO: implement in T-371."""

    def publish(self, plan, video_path: Path, thumbnail_path: Path) -> str:  # type: ignore[override]
        """TODO: T-372. Returns YouTube video_id."""
        raise NotImplementedError("T-371 pending")
