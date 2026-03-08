# Architecture Decisions (ADR log)

> Кожне рішення — коротко: контекст, рішення, наслідки.

## ADR-0001: Repo structure separation
**Context:** змішування ML/Backend/DevOps ускладнює тестування.  
**Decision:** ML в `src/ytaimbot_ml/`, backend в `modules/`, docs/tests окремо.  
**Consequences:** чисті межі, легше писати deterministic tests.

## ADR-0002: No network calls in unit tests
**Context:** flaky tests, rate limits, cost.  
**Decision:** всі інтеграції — через adapters + mocks.  
**Consequences:** треба підтримувати fake datasets/fixtures.