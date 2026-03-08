# Storage Design (MVP)

## MVP storage
SQLite або file-based (поки немає коду — опис контрактів).

## Tables (proposal)
### runs
- run_id (PK)
- started_at
- finished_at
- status
- reason

### trends
- trend_id
- run_id (FK)
- raw_payload (json/text)
- features_hash

### compliance_reports
- report_id
- run_id (FK)
- similarity_score
- bayes_p_bad
- decision
- reasons (json/text)

## Acceptance
- idempotency: повтор одного run_id не дублює артефакти
