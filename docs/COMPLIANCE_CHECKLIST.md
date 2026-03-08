# Compliance Checklist — YouTube AI Money Bot 2026 (UA/ЄС)

## Goal
Забезпечити “compliance-first” пайплайн: мінімізувати ризики банів, страйків, порушень авторських прав і проблем з даними.

## Non-negotiable rules
- Перші 50 відео: **unlisted-first + manual review**.
- Автопублікація тільки після **fail-closed** гейтів.
- Зберігати evidence артефакти: scores + reasons + hashes.

## Pre-publication gates (MVP)
1) Similarity gate (cosine similarity) проти **власного архіву** (script/title/desc).
2) Bayesian slop/quality gate (synthetic features, deterministic).
3) Metadata policy sanity checks (no misleading claims).

## Evidence artifacts (store)
- content hash (script/title/desc)
- similarity report (top matches + score)
- bayes report (P(bad) + threshold)
- operator decision (для перших 50)

## Acceptance Criteria
- [ ] Publish stage не викликається без gate results.
- [ ] Є детерміновані тести для гейтів.
- [ ] Немає секретів/PII в логах.
