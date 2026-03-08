# Software Requirements Specification (SRS)

## Introduction

This document defines the functional and non-functional requirements for **YouTube AI Money Bot 2026** (YTAIMBot) — an autonomous trend analysis and content pipeline that discovers high-potential YouTube niches, generates content plans, validates quality, and publishes videos with minimal human intervention.

---

## Functional Requirements

### FR-01 — Autonomous Trend Analysis

The system shall autonomously ingest trend signals from one or more sources (Google Trends, YouTube Data API, or synthetic fallback), score them using PCA/SVD-based dimensionality reduction, and produce a ranked list of the top N niches/topics without human input.

**Acceptance criteria:**
- At least 10 signals per pipeline run.
- Rankings are deterministic given the same random seed.
- Falls back to `SyntheticTrendSource` when external APIs are unavailable.

### FR-02 — Content Plan Generation

For each top-ranked trend, the system shall generate a `ContentPlan` containing a title, structured outline (≥ 3 sections), and a list of SEO keywords.

**Acceptance criteria:**
- At least one `ContentPlan` produced per pipeline run.
- Plans are persisted to storage via `StorageAdapter`.

### FR-03 — SEO Optimisation

Content plans shall include keyword suggestions derived from the trend signal.  A future SEO optimizer module (Phase 3) will expand and refine these keywords using search-volume proxies.

**Acceptance criteria (MVP):**
- Each plan includes ≥ 3 keywords.
- Keywords include the original trend keyword.

### FR-04 — Gated Publishing (Unlisted-First)

The system shall not publish content without a `ComplianceReport` with `decision = "pass"`.  On first publish, videos are set to *unlisted* and promoted to public only after a configurable delay.

**Acceptance criteria:**
- Pipeline is fail-closed: `PublisherAdapter.publish()` is never called for reports with `decision = "fail"`.
- `dry_run = True` suppresses all publish calls.

### FR-05 — Metrics Learning Loop

After publication, the system shall collect view/engagement metrics and feed them back into trend scoring.  (Deferred to Phase 5 — stub only in MVP.)

---

## Non-Functional Requirements

### NFR-01 — Uptime ≥ 99.9 %

The bot process shall be managed by Docker + systemd watchdog on Hetzner, targeting 99.9 % monthly uptime.

### NFR-02 — Deterministic ML

All ML components (`TrendAnalyzer`, `BayesQualityFilter`) shall produce identical outputs given identical inputs and the same random seed.  Tests verify this property explicitly.

### NFR-03 — Minimal Budget

The system shall prefer free or low-cost APIs (Google Trends scraping, YouTube Data API free tier) and avoid per-call charges where possible.

### NFR-04 — Cloud Deployment (Hetzner)

The system shall be deployable on a **Hetzner CX22** instance (2 vCPU, 4 GB RAM) using `docker-compose up -d` without manual configuration beyond setting environment variables.
