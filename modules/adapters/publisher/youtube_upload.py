"""YouTubeUploadAdapter: uploads videos via YouTube Data API v3.

Roadmap tasks: T-241 through T-268 (EPIC 4.1–4.2 Publishing Pipeline)
T-244 fix: publish() now returns UploadResult instead of bool.

Environment variables:
  YOUTUBE_CLIENT_SECRET_PATH : path to client_secret.json (OAuth2)
  YOUTUBE_TOKEN_PATH         : path to token.json (cached credentials)
  YOUTUBE_CATEGORY_ID        : default category (default "28" = Science & Technology)
  YOUTUBE_DEFAULT_LANGUAGE   : default language tag (default "uk")
  YTAIMBOT_DRY_RUN           : if "true", publish() returns empty UploadResult

Upload pipeline — Resumable Upload algorithm:
  1. QuotaGuard.allow()                    → O(1)
  2. ComplianceReport.decision == "pass"   → O(1)
  3. _get_credentials()                    → OAuth2 refresh if expired
  4. _upload_video(video_path, metadata)   → resumable, chunk_size=256 KB
  5. _set_thumbnail(video_id, thumbnail)   → thumbnail.set API call
  6. _schedule_public(video_id, delay_h)   → videos.update → publishAt
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from modules.adapters.base import PublisherAdapter
from modules.adapters.publisher.quota_guard import QuotaGuard
from ytaimbot_ml.schemas import (
    ComplianceReport,
    ContentPlan,
    PrivacyStatus,
    UploadResult,
    VideoAsset,
)

logger = logging.getLogger(__name__)

_CHUNK_SIZE = 256 * 1024  # 256 KB — minimum resumable chunk
_MAX_RETRIES = 3


class DryRunError(RuntimeError):
    """Raised when upload() is called in dry-run mode."""


class YouTubeUploadAdapter(PublisherAdapter):
    """Uploads video assets to YouTube using the Data API v3 (resumable upload).

    Parameters
    ----------
    quota_guard:
        Token Bucket guard.  Created automatically if not provided.
    client_secret_path:
        Path to ``client_secret.json`` for OAuth2.
    token_path:
        Path to cached OAuth2 token.
    category_id:
        YouTube category ID string (default ``"28"`` = Science & Technology).
    language:
        Video default language tag (default ``"uk"``).
    dry_run:
        When ``True``, publish() returns empty UploadResult (no API calls).

    Complexity
    ----------
    publish(): O(1) — plan-only interface, no video asset
    upload():  O(file_size / chunk_size) — network I/O bound

    Examples
    --------
    >>> import os; os.environ["YTAIMBOT_DRY_RUN"] = "true"
    >>> adapter = YouTubeUploadAdapter()
    >>> adapter.dry_run
    True
    """

    def __init__(
        self,
        quota_guard: QuotaGuard | None = None,
        client_secret_path: str | Path | None = None,
        token_path: str | Path | None = None,
        category_id: str | None = None,
        language: str | None = None,
        dry_run: bool | None = None,
    ) -> None:
        self._guard = quota_guard or QuotaGuard(
            max_per_day=int(os.environ.get("MAX_UPLOADS_PER_DAY", "6"))
        )
        self._client_secret = Path(
            client_secret_path
            or os.environ.get("YOUTUBE_CLIENT_SECRET_PATH", "data/client_secret.json")
        )
        self._token_path = Path(
            token_path
            or os.environ.get("YOUTUBE_TOKEN_PATH", "data/token.json")
        )
        self._category_id = category_id or os.environ.get("YOUTUBE_CATEGORY_ID", "28")
        self._language = language or os.environ.get("YOUTUBE_DEFAULT_LANGUAGE", "uk")

        if dry_run is not None:
            self.dry_run = dry_run
        else:
            self.dry_run = os.environ.get("YTAIMBOT_DRY_RUN", "true").lower() != "false"

    # ------------------------------------------------------------------
    # PublisherAdapter ABC — T-244 fix: returns UploadResult
    # ------------------------------------------------------------------

    def publish(
        self, plan: ContentPlan, compliance_report: ComplianceReport
    ) -> UploadResult:
        """Implement PublisherAdapter ABC — returns UploadResult (T-244 fix).

        Plan-only interface (no VideoAsset). Returns an UploadResult with
        empty video_id (success=False). Use upload() for full video publishing.

        Parameters
        ----------
        plan:
            Approved content plan.
        compliance_report:
            Must have ``decision == "pass"``.

        Returns
        -------
        UploadResult
            Empty result (video_id="") — success=False.

        Examples
        --------
        >>> adapter = YouTubeUploadAdapter(dry_run=True)
        >>> result = adapter.publish(
        ...     ContentPlan("t1", "Title", [], []),
        ...     ComplianceReport("h", 0.0, 0.1, "pass", [])
        ... )
        >>> result.success
        False
        """
        logger.info(
            "YouTubeUploadAdapter.publish() called via plan-only interface "
            "— no VideoAsset. Use upload() for real publishing."
        )
        return UploadResult(plan_id=plan.trend_id)

    # ------------------------------------------------------------------
    # Primary upload API
    # ------------------------------------------------------------------

    def upload(
        self,
        video_asset: VideoAsset,
        plan: ContentPlan,
        compliance_report: ComplianceReport,
        *,
        description: str = "",
        tags: list[str] | None = None,
        publish_delay_hours: int = 24,
    ) -> UploadResult:
        """Upload a video asset to YouTube.

        Parameters
        ----------
        video_asset:
            Assembled video with ``video_path`` and ``thumbnail_path``.
        plan:
            Source content plan (provides title, keywords).
        compliance_report:
            Must have ``decision == "pass"`` — fail-closed guard.
        description:
            Video description text.  Auto-generated from keywords if empty.
        tags:
            YouTube tags list.  Defaults to ``plan.keywords``.
        publish_delay_hours:
            Hours after upload to set video public (default 24).

        Returns
        -------
        UploadResult
            Contains ``video_id``, ``url``, ``quota_used``.

        Raises
        ------
        DryRunError
            If ``dry_run=True``.
        QuotaExhaustedError
            If the daily token bucket is empty.
        ValueError
            If compliance_report.decision != "pass".
        FileNotFoundError
            If the video file does not exist.

        Complexity
        ----------
        O(file_size / 262144) — one API call per 256 KB chunk
        """
        if self.dry_run:
            raise DryRunError(
                "YouTubeUploadAdapter.upload() called in dry-run mode. "
                "Set YTAIMBOT_DRY_RUN=false to enable real uploads."
            )

        if compliance_report.decision != "pass":
            raise ValueError(
                f"Cannot upload: compliance decision is '{compliance_report.decision}' (need 'pass')"
            )

        if not video_asset.video_path or not Path(video_asset.video_path).exists():
            raise FileNotFoundError(
                f"Video file not found: {video_asset.video_path!r}"
            )

        self._guard.require()  # raises QuotaExhaustedError if empty

        youtube = self._build_service()
        video_id = self._upload_video(
            youtube=youtube,
            video_path=Path(video_asset.video_path),
            title=plan.title,
            description=description or self._auto_description(plan),
            tags=tags or plan.keywords,
            category_id=self._category_id,
            language=self._language,
        )

        quota_used = QuotaGuard.COST_UPLOAD

        if video_asset.thumbnail_path and Path(video_asset.thumbnail_path).exists():
            self._set_thumbnail(youtube, video_id, Path(video_asset.thumbnail_path))
            quota_used += QuotaGuard.COST_THUMBNAIL

        if publish_delay_hours > 0:
            self._schedule_public(youtube, video_id, delay_hours=publish_delay_hours)

        url = f"https://youtu.be/{video_id}"
        logger.info(
            "Upload complete: video_id=%s url=%s quota_used=%d",
            video_id, url, quota_used,
        )

        return UploadResult(
            plan_id=plan.trend_id,
            video_id=video_id,
            url=url,
            privacy_status=PrivacyStatus.UNLISTED,
            quota_used=quota_used,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_credentials(self):
        """Load or refresh OAuth2 credentials.  Complexity: O(1)."""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
        except ImportError as exc:
            raise ImportError(
                "google-auth-oauthlib is required for YouTube uploads. "
                "Install with: pip install google-auth-oauthlib google-api-python-client"
            ) from exc

        scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        creds = None

        if self._token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self._token_path), scopes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self._client_secret.exists():
                    raise FileNotFoundError(
                        f"client_secret.json not found at {self._client_secret}. "
                        "Download from Google Cloud Console → APIs & Services → Credentials."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self._client_secret), scopes
                )
                creds = flow.run_local_server(port=0)

            self._token_path.parent.mkdir(parents=True, exist_ok=True)
            self._token_path.write_text(creds.to_json(), encoding="utf-8")

        return creds

    def _build_service(self):
        """Build the YouTube API service client.  Complexity: O(1)."""
        try:
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise ImportError(
                "google-api-python-client is required. "
                "Install with: pip install google-api-python-client"
            ) from exc

        creds = self._get_credentials()
        return build("youtube", "v3", credentials=creds)

    def _upload_video(
        self,
        youtube,
        video_path: Path,
        title: str,
        description: str,
        tags: list[str],
        category_id: str,
        language: str,
    ) -> str:
        """Execute resumable upload and return the YouTube video_id.

        Complexity: O(file_size / chunk_size)
        """
        try:
            from googleapiclient.errors import HttpError
            from googleapiclient.http import MediaFileUpload
        except ImportError as exc:
            raise ImportError("google-api-python-client required") from exc

        import time

        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags[:500],
                "categoryId": category_id,
                "defaultLanguage": language,
            },
            "status": {
                "privacyStatus": PrivacyStatus.UNLISTED,
                "selfDeclaredMadeForKids": False,
                "madeForKids": False,
            },
            "localizations": {},
        }

        media = MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            resumable=True,
            chunksize=_CHUNK_SIZE,
        )

        request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media,
        )

        response = None
        retry = 0
        while response is None:
            try:
                _, response = request.next_chunk()
            except HttpError as e:
                if e.resp.status in (500, 502, 503, 504) and retry < _MAX_RETRIES:
                    wait = 2 ** retry
                    logger.warning(
                        "Upload HTTP %s — retry %d/%d in %ds",
                        e.resp.status, retry + 1, _MAX_RETRIES, wait,
                    )
                    time.sleep(wait)
                    retry += 1
                else:
                    raise

        return response["id"]

    def _set_thumbnail(self, youtube, video_id: str, thumbnail_path: Path) -> None:
        """Set the custom thumbnail for an uploaded video.  Complexity: O(file_size)."""
        try:
            from googleapiclient.http import MediaFileUpload
        except ImportError as exc:
            raise ImportError("google-api-python-client required") from exc

        media = MediaFileUpload(str(thumbnail_path), mimetype="image/png")
        youtube.thumbnails().set(videoId=video_id, media_body=media).execute()
        logger.debug("Thumbnail set for video_id=%s", video_id)

    def _schedule_public(self, youtube, video_id: str, delay_hours: int = 24) -> None:
        """Schedule a video to go public after ``delay_hours`` hours.  Complexity: O(1)."""
        publish_at = (
            datetime.now(timezone.utc) + timedelta(hours=delay_hours)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        youtube.videos().update(
            part="status",
            body={
                "id": video_id,
                "status": {
                    "privacyStatus": PrivacyStatus.PRIVATE,
                    "publishAt": publish_at,
                },
            },
        ).execute()
        logger.info("Scheduled public for video_id=%s at %s", video_id, publish_at)

    @staticmethod
    def _auto_description(plan: ContentPlan) -> str:
        """Generate a basic video description from a ContentPlan.  Complexity: O(k)."""
        tags_line = " ".join(f"#{kw.replace(' ', '_')}" for kw in plan.keywords[:20])
        parts = [
            plan.title,
            "",
            "\n".join(plan.outline),
            "",
            tags_line,
            "",
            "AI-generated content. All characters are adults (18+). Fictional content only.",
            "✅ Created with YTAIMBot | Auto-generated content",
        ]
        return "\n".join(parts)
