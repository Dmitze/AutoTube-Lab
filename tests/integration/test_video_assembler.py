"""Integration tests for VideoAssembler (Phase 3, T-300).

All MoviePy/FFmpeg calls mocked. No real rendering.

Test cases:
  test_assemble_returns_mp4_path         : returns Path ending in .mp4
  test_output_file_created               : output file exists (mocked)
  test_assembly_uses_all_audio_sections  : all audio paths consumed
  test_subtitles_generated               : SRT file created

Status: 🔲 Pending — implement after T-300
"""
import pytest

# TODO: import VideoAssembler after T-300 is implemented


@pytest.mark.skip(reason="T-300 not implemented yet")
def test_assemble_returns_mp4_path(tmp_path):
    """assemble() returns a Path ending in .mp4."""
    pass


@pytest.mark.skip(reason="T-300 not implemented yet")
def test_assembly_uses_all_audio_sections(tmp_path):
    """All audio sections are included in the final video."""
    pass


@pytest.mark.skip(reason="T-300 not implemented yet")
def test_subtitles_generated(tmp_path):
    """SRT subtitle file is created alongside the video."""
    pass
