"""Phase 2 — TTS adapters sub-package.

Adapters
--------
TTSAdapter (base)  : ABC with speak(text) → Path
EdgeTTSAdapter     : Microsoft Edge TTS (primary, uk-UA-OstapNeural)
CoquiTTSAdapter    : Coqui TTS offline (fallback, no internet needed)

Selection logic (T-101):
  TTS_VOICE set        → EdgeTTSAdapter (cloud, free, high quality)
  COQUI_MODEL_PATH set → CoquiTTSAdapter (local, offline)
  Neither              → EdgeTTSAdapter with default voice

Output format: WAV 22050Hz mono → data/audio/<run_id>/<section>.wav

Status: 🔲 Pending — T-101 (Phase 2, EPIC 2.2)
"""
