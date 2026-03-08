# How to start a new task chat (YTAIMBot)

1) Обери роль агента:
- ML: `docs/AI_AGENT_PROMPT_ML_REFINED.md`
- Backend: `docs/AI_AGENT_PROMPT_BACKEND_REFINED.md`
- DevOps: `docs/AI_AGENT_PROMPT_DEVOPS_REFINED.md`
- Compliance: `docs/AI_AGENT_PROMPT_COMPLIANCE_REFINED.md`
- Frontend: `docs/AI_AGENT_PROMPT_FRONTEND_REFINED.md`

2) Встав промпт ролі в чат.

3) Відповідай на 3 перші питання (ніша/формат/метрики).

4) Вимагай формат відповіді:
Goal / Files / Implementation / Big‑O / Run / Tests / Acceptance / Risks.

5) Заборони зміни поза `src/ytaimbot_ml/`, `modules/`, `tests/`, `docs/`.

6) Якщо агент пропонує API виклики у тестах — зупини і попроси зробити mocks/fakes.
