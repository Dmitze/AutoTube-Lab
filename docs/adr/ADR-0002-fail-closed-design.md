# ADR-0002: Fail-Closed Publishing Design

**Date:** 2026-01-W1  
**Status:** ✅ Accepted

## Context

The pipeline can generate harmful or low-quality content. Publishing it automatically without a safety gate is risky.

## Decision

Publishing is **fail-closed**: video is NEVER uploaded unless ALL of these are true:
1. `ComplianceReport.decision == "pass"` (Bayesian gate approved)
2. `YTAIMBOT_DRY_RUN == "false"` (explicitly disabled dry run)
3. `QuotaGuard.allow() == True` (upload quota not exhausted)

```python
# In Pipeline._publish_approved():
if report.decision != "pass":
    continue  # skip — never publish
if self._dry_run:
    continue  # skip — dry run mode
if not quota_guard.allow():
    continue  # skip — quota exhausted
publisher.publish(plan)  # only reaches here if ALL checks pass
```

## Consequences

**Good:**
- Zero accidental publishes during development/testing
- Compliance gate is mandatory, not optional
- Safe to deploy: default state is dry_run=true

**Bad:**
- False positives in gate = missed publishing opportunities (acceptable)
