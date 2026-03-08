# Architecture — Dataflow (MVP)

## Entities / data artifacts
- TrendSignals (raw): synthetic або з adapter
- TrendFeatures: матриця ознак (n_samples x n_features)
- ReducedFeatures: PCA/SVD output (n_samples x k)
- TrendRanking: список candidate topics + scores
- ContentPlan (stub): title/outline/keywords
- ComplianceReport: similarity + bayes + decision
- PublishRequest (stub): unlisted + metadata
- MetricsSnapshot (stub): views/ctr/retention

## Stage flow
1) Ingest: TrendSource -> TrendSignals
2) Featurize: TrendSignals -> TrendFeatures
3) Reduce: TrendFeatures -> ReducedFeatures (PCA/SVD)
4) Score: ReducedFeatures -> TrendRanking
5) Plan: TrendRanking -> ContentPlan (stub)
6) Gate: ContentPlan -> ComplianceReport (fail-closed)
7) Publish (stub): ComplianceReport(decision=allow) -> PublishRequest(unlisted)
8) Learn (later): MetricsSnapshot -> learner updates

## Failure handling
- будь-який stage може fail; orchestrator має:
  - логувати причину
  - не “частково публікувати”
  - ретраї тільки на adapter layer
