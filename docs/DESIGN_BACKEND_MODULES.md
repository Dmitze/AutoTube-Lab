# Detailed Design — Backend modules (MVP-first)

## Modules (planned)
- `modules/orchestrator.py`
- `modules/adapters/trend_source.py`
- `modules/adapters/storage.py`
- `modules/compliance/gate.py` (або ML quality layer, але decision — у backend)

## Orchestrator
### Responsibilities
- зібрати pipeline stage-by-stage
- підтримувати dry-run
- fail-closed на compliance

### Interfaces (must be mockable)
- TrendSourceAdapter
- StorageAdapter
- PublisherAdapter (stub)
- MetricsAdapter (stub)

## Error handling
- retries/timeouts — тільки на adapter layer
- orchestrator: fail fast + structured log + persist state
