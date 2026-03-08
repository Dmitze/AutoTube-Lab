# Risk Register

This document outlines the identified risks and mitigation strategies.

---

## R-01 — YouTube API Rate Limits

| Field | Value |
|-------|-------|
| **Probability** | High |
| **Impact** | High |
| **Status** | Open |

**Description**: YouTube Data API v3 has a daily quota of 10 000 units.  Heavy polling can exhaust the quota quickly.

**Mitigation**:
- Implement exponential backoff with jitter on API errors.
- Fall back to `SyntheticTrendSource` when quota is exceeded.
- Cache results for at least 1 hour.

---

## R-02 — Content Duplication / Copyright

| Field | Value |
|-------|-------|
| **Probability** | Medium |
| **Impact** | Critical |
| **Status** | Mitigated (MVP) |

**Description**: Generated content could inadvertently duplicate existing videos or copyrighted material, triggering Content ID strikes.

**Mitigation**:
- Cosine-similarity check against known titles (similarity gate in `BayesQualityFilter`).
- Unlisted-first publish strategy (FR-04) provides a review window.
- `ComplianceReport.similarity_score` tracks duplication risk.

---

## R-03 — Budget Overrun

| Field | Value |
|-------|-------|
| **Probability** | Medium |
| **Impact** | Medium |
| **Status** | Open |

**Description**: Paid API calls (OpenAI, video rendering) can accumulate costs unexpectedly.

**Mitigation**:
- Prefer free/open-source models (local LLMs via Ollama) over paid APIs.
- Hard budget guard: environment variable `MAX_MONTHLY_SPEND_USD` (default: 0 = no paid calls).
- Cost dashboard tracked in `docs/FINANCE_BUDGET_ROI_CALCULATOR.md`.

---

## R-04 — Hetzner Outage

| Field | Value |
|-------|-------|
| **Probability** | Low |
| **Impact** | Medium |
| **Status** | Open |

**Description**: Hetzner CX22 instance becomes unavailable due to hardware failure or network issues.

**Mitigation**:
- `docker-compose` with `restart: unless-stopped` policy.
- Daily backup of `data/` directory to Hetzner Object Storage.
- systemd watchdog restarts the container on failure.
- Rollback: pull previous Docker image tag.

---

## R-05 — AI Slop / Low Quality Output

| Field | Value |
|-------|-------|
| **Probability** | High |
| **Impact** | High |
| **Status** | Mitigated (MVP) |

**Description**: Generative models can produce low-quality, repetitive, or factually incorrect content ("AI slop") that harms channel reputation.

**Mitigation**:
- `BayesQualityFilter` gates all content plans before publish.
- Unlisted-first strategy (FR-04) allows manual review.
- Content plans include structured outlines, not raw generated text, in MVP.
