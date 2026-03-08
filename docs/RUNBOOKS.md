# Runbooks (Ops)

## RB-01: Bot doesn't start
- перевірити env vars
- перевірити версію Python
- запустити `pytest -q` (як sanity)

## RB-02: Trend stage failing
- переключити на synthetic data mode
- перевірити adapter retries/timeouts

## RB-03: Compliance gate blocks everything
- перевірити thresholds
- перевірити similarity archive (порожній/зламаний)
- дозволяється manual override тільки для unlisted

## RB-04: Storage corruption (SQLite)
- restore from backup
- run minimal integrity check
