"""Integration tests for YouTubeUploader (Phase 4, T-371).

All YouTube API calls mocked. No OAuth2 required.

Test cases:
  test_publish_returns_video_id          : returns string video_id
  test_dry_run_skips_upload              : DRY_RUN=true → no API call
  test_compliance_fail_skips_upload      : decision="fail" → no upload
  test_quota_guard_blocks_over_limit     : QuotaGuard rejects 7th upload
  test_unlisted_on_upload                : video initially set to unlisted

Status: 🔲 Pending — implement after T-371
"""
import pytest

# TODO: import YouTubeUploader after T-371 is implemented


@pytest.mark.skip(reason="T-371 not implemented yet")
def test_dry_run_skips_upload(tmp_path, monkeypatch):
    """With DRY_RUN=true, no YouTube API call is made."""
    monkeypatch.setenv("YTAIMBOT_DRY_RUN", "true")
    pass


@pytest.mark.skip(reason="T-371 not implemented yet")
def test_compliance_fail_skips_upload(tmp_path):
    """ComplianceReport.decision='fail' → publish() returns None."""
    pass


@pytest.mark.skip(reason="T-371 not implemented yet")
def test_quota_guard_blocks_over_limit():
    """7th upload in one day is rejected by QuotaGuard."""
    pass


@pytest.mark.skip(reason="T-371 not implemented yet")
def test_unlisted_on_upload():
    """New video uploaded with privacyStatus='unlisted'."""
    pass
