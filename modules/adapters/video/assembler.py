"""Phase 4 — VideoAssembler: MoviePy + FFmpeg video assembly pipeline.

Roadmap tasks: T-182 through T-195 (EPIC 4.1 Video Assembly)
Depends on:   moviepy (optional), Script, VideoAsset schema

Assembly pipeline:
  1. Validate inputs (audio exists, script non-empty)   → O(n_sections)
  2. Load audio clips per section (MP3 via pydub)        → O(n_sections)
  3. Generate background clip (gradient or stock image)  → O(duration)
  4. Concatenate audio into single track                  → O(n_sections)
  5. Burn-in subtitles via FFmpeg (subprocess, optional)  → O(frames)
  6. Export: H.264 + AAC → MP4, CRF=23, 30fps           → O(frames)

Output spec:
  Resolution: 1920×1080 (16:9)
  FPS: 30
  Codec: libx264, CRF=23
  Audio: AAC 192kbps
  Target duration: 8–12 minutes

Graceful degradation:
  - MoviePy not installed → raises ImportError with install instructions
  - FFmpeg not on PATH → subtitle burn-in skipped (video still produced)
  - Audio file missing → raises FileNotFoundError

Complexity: O(frames × quality) = O(duration × fps × resolution)
"""
from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from pathlib import Path

from ytaimbot_ml.schemas import Script, VideoAsset

logger = logging.getLogger(__name__)

# Output spec constants
_DEFAULT_FPS = 30
_DEFAULT_CRF = 23  # H.264 quality: 0=lossless, 51=worst; 23=visually lossless
_DEFAULT_WIDTH = 1920
_DEFAULT_HEIGHT = 1080
_DEFAULT_AUDIO_BITRATE = "192k"

# Background color for gradient (dark navy)
_BG_COLOR = (10, 10, 30)  # RGB


class VideoAssembler:
    """MoviePy + FFmpeg video assembly adapter.

    Parameters
    ----------
    output_dir:
        Directory for output MP4 files.
    fps:
        Output frame rate (default 30).
    crf:
        H.264 CRF quality (default 23).
    resolution:
        Output (width, height) in pixels (default 1920×1080).

    Complexity
    ----------
    assemble(): O(frames) = O(duration × fps) — FFmpeg render bound

    Examples
    --------
    >>> assembler = VideoAssembler(output_dir="/tmp")
    >>> assembler.fps
    30
    """

    def __init__(
        self,
        output_dir: str | Path = "data/videos",
        fps: int = _DEFAULT_FPS,
        crf: int = _DEFAULT_CRF,
        resolution: tuple[int, int] = (_DEFAULT_WIDTH, _DEFAULT_HEIGHT),
    ) -> None:
        self.output_dir = Path(output_dir)
        self.fps = fps
        self.crf = crf
        self.resolution = resolution

    def assemble(
        self,
        script: Script,
        audio_path: Path,
        thumbnail_path: Path | None = None,
        subtitle_path: Path | None = None,
    ) -> VideoAsset:
        """Assemble a full video from script + audio + optional assets.

        Parameters
        ----------
        script:
            Generated Script (used for metadata and duration estimation).
        audio_path:
            Path to the full MP3 audio (produced by EdgeTTSAdapter).
        thumbnail_path:
            Optional path to 1280×720 PNG thumbnail.
        subtitle_path:
            Optional path to SRT subtitle file.

        Returns
        -------
        VideoAsset
            Dataclass with video_path, thumbnail_path, duration_seconds.

        Raises
        ------
        FileNotFoundError
            If audio_path does not exist.
        ImportError
            If moviepy is not installed.
        RuntimeError
            If FFmpeg is not available and video rendering fails.

        Complexity
        ----------
        O(duration × fps) — FFmpeg render time

        Examples
        --------
        >>> # (requires moviepy + FFmpeg — see CI integration tests)
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        try:
            from moviepy import AudioFileClip, ColorClip, CompositeVideoClip  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "moviepy not installed. Install with: pip install moviepy"
            ) from exc

        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"{script.plan_id}.mp4"

        logger.info(
            "VideoAssembler: assembling video for plan_id=%s", script.plan_id
        )

        # Load audio
        audio_clip = AudioFileClip(str(audio_path))
        duration = audio_clip.duration

        # Create background clip (solid color for MVP)
        bg_clip = ColorClip(
            size=self.resolution,
            color=_BG_COLOR,
            duration=duration,
        )
        bg_clip = bg_clip.with_audio(audio_clip)

        # Subtitle burn-in (if SRT provided and FFmpeg available)
        if subtitle_path and subtitle_path.exists():
            output_path = self._burn_subtitles(bg_clip, subtitle_path, output_path)
        else:
            bg_clip.write_videofile(
                str(output_path),
                fps=self.fps,
                codec="libx264",
                audio_codec="aac",
                bitrate=_DEFAULT_AUDIO_BITRATE,
                preset="medium",
                ffmpeg_params=["-crf", str(self.crf)],
                logger=None,
            )

        logger.info("VideoAssembler: video saved → %s (%.1fs)", output_path, duration)

        return VideoAsset(
            plan_id=script.plan_id,
            video_path=str(output_path),
            thumbnail_path=str(thumbnail_path) if thumbnail_path else "",
            subtitle_path=str(subtitle_path) if subtitle_path else "",
            duration_seconds=round(duration, 2),
        )

    def _burn_subtitles(
        self,
        clip,
        srt_path: Path,
        output_path: Path,
    ) -> Path:
        """Burn SRT subtitles into video via FFmpeg subprocess. O(frames).

        Falls back to writing without subtitles if FFmpeg not on PATH.

        Parameters
        ----------
        clip:
            MoviePy VideoClip with audio.
        srt_path:
            Path to .srt subtitle file.
        output_path:
            Destination MP4 path.

        Returns
        -------
        Path
            Final output path.
        """
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        clip.write_videofile(
            str(tmp_path),
            fps=self.fps,
            codec="libx264",
            audio_codec="aac",
            bitrate=_DEFAULT_AUDIO_BITRATE,
            preset="medium",
            ffmpeg_params=["-crf", str(self.crf)],
            logger=None,
        )

        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", str(tmp_path),
            "-vf", f"subtitles={srt_path}:force_style='Fontsize=24,PrimaryColour=&H00ffffff&'",
            "-c:a", "copy",
            str(output_path),
        ]

        try:
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True, timeout=300)
            tmp_path.unlink(missing_ok=True)
            logger.info("VideoAssembler: subtitles burned in via FFmpeg")
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            logger.warning(
                "VideoAssembler: FFmpeg subtitle burn-in failed (%s) — using video without subtitles",
                exc,
            )
            tmp_path.rename(output_path)

        return output_path

