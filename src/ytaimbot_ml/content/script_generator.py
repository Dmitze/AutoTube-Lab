"""Phase 2 — ScriptGenerator: generates video scripts from ContentPlan via LLM.

Roadmap tasks: T-124 through T-135 (EPIC 2.3)
Depends on:   LLMAdapter (modules/adapters/llm/base.py)
              TokenBudget (src/ytaimbot_ml/content/token_budget.py)
              ContentPlan, Script, ScriptSection (schemas.py)

Script structure
----------------
  hook    (15s  ≈ 150–200 words)  — attention-grabbing opener
  intro   (30s  ≈ 75 words)       — context & credibility
  body_1  (60s  ≈ 150 words)      — main point 1
  body_2  (60s  ≈ 150 words)      — main point 2
  body_3  (60s  ≈ 150 words)      — main point 3
  cta     (30s  ≈ 75 words)       — subscribe / like / comment

  Total target: ≥ 500 words (acceptance criterion)

Algorithm
---------
generate() pipeline:
  1. TokenBudget.allocate(sections)          → O(n_sections)
  2. for each section:
       a. _build_prompt(section, plan)       → O(len(keywords))
       b. LLMAdapter.generate(prompt, budget)→ O(tokens) — network/local
       c. _inject_keywords(text, keywords)   → O(words × keywords)
       d. ScriptSection(name, text, ...)     → O(words)
  3. _validate_script(script)               → O(total_words)
  4. return Script(plan_id, sections, ...)

  Total: O(n_sections × tokens)

Keyword injection algorithm (Aho-Corasick-lite):
  Simple set-check → O(words × keywords) for MVP.
  Phase 6 will replace with Aho-Corasick O(words + keywords) for >50 keywords.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

from ytaimbot_ml.content.token_budget import TokenBudget
from ytaimbot_ml.schemas import ContentPlan, Script, ScriptSection

if TYPE_CHECKING:
    from modules.adapters.base import LLMAdapter

logger = logging.getLogger(__name__)

# Section order for the 6-part script structure
SECTION_ORDER: list[str] = ["hook", "intro", "body_1", "body_2", "body_3", "cta"]

# Minimum acceptable word count for the full script
MIN_TOTAL_WORDS = 500

# Number of keywords to inject per section (max)
_MAX_KEYWORDS_PER_SECTION = 3


class ScriptGenerator:
    """Generates video scripts from ContentPlan using an LLM adapter.

    Parameters
    ----------
    llm:
        LLMAdapter instance (GroqAdapter, LLMFallbackChain, etc.).
    budget:
        TokenBudget for proportional token allocation. Defaults to 2048 total.
    language:
        ISO 639-1 language code for prompts. Default "uk".

    Complexity
    ----------
    generate(): O(n_sections × tokens) — dominated by LLM calls

    Examples
    --------
    >>> from modules.adapters.llm.groq import GroqAdapter
    >>> gen = ScriptGenerator(llm=GroqAdapter(), language="en")
    >>> isinstance(gen, ScriptGenerator)
    True
    """

    def __init__(
        self,
        llm: "LLMAdapter",
        budget: TokenBudget | None = None,
        language: str = "uk",
    ) -> None:
        self._llm = llm
        self._budget = budget or TokenBudget(total_tokens=2048)
        self.language = language

    def generate(self, plan: ContentPlan, rng: np.random.Generator) -> Script:
        """Generate a full video script from a ContentPlan.

        Parameters
        ----------
        plan:
            ContentPlan with title, outline, keywords.
        rng:
            Seeded NumPy Generator for any stochastic decisions.

        Returns
        -------
        Script
            Completed Script with ≥ 500 words across 6 sections.

        Raises
        ------
        ValueError
            If generated script falls below MIN_TOTAL_WORDS.

        Complexity
        ----------
        O(n_sections × tokens)

        Examples
        --------
        >>> import numpy as np
        >>> from ytaimbot_ml.schemas import ContentPlan
        >>> # (requires live LLM; use MockLLMAdapter in tests)
        """
        allocations = self._budget.allocate(SECTION_ORDER)
        sections: list[ScriptSection] = []
        keywords = list(plan.keywords)

        for section_name in SECTION_ORDER:
            token_budget = allocations[section_name]
            prompt = self._build_prompt(section_name, plan, sections)
            logger.debug(
                "ScriptGenerator: generating section=%s budget=%d tokens",
                section_name,
                token_budget,
            )
            text = self._llm.generate(prompt, max_tokens=token_budget)
            # Inject keywords relevant to this section
            section_keywords = self._pick_keywords(keywords, section_name, rng)
            text = self._inject_keywords(text, section_keywords)
            sections.append(ScriptSection(
                name=section_name,
                text=text,
                keywords=section_keywords,
            ))

        script = Script(plan_id=plan.trend_id, sections=sections, language=self.language)
        self._validate_script(script)
        logger.info(
            "ScriptGenerator: script complete — %d words, plan_id=%s",
            script.total_words,
            plan.trend_id,
        )
        return script

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_prompt(
        self,
        section: str,
        plan: ContentPlan,
        prev_sections: list[ScriptSection],
    ) -> str:
        """Build a section-specific LLM prompt.

        Algorithm: O(len(outline) + len(keywords))

        Parameters
        ----------
        section:
            Name of the section to generate.
        plan:
            ContentPlan context.
        prev_sections:
            Previously generated sections (for continuity).

        Returns
        -------
        str
            Prompt string for the LLM.
        """
        keywords_str = ", ".join(plan.keywords[:5]) if plan.keywords else "—"
        outline_str = "\n".join(f"  - {o}" for o in plan.outline) if plan.outline else "  - (no outline)"

        if self.language == "uk":
            base = (
                f"Ти — YouTube сценарист. Напиши розділ '{section}' для відео.\n"
                f"Тема: {plan.title}\n"
                f"Ключові слова: {keywords_str}\n"
                f"Структура відео:\n{outline_str}\n"
            )
        else:
            base = (
                f"You are a YouTube scriptwriter. Write the '{section}' section.\n"
                f"Topic: {plan.title}\n"
                f"Keywords: {keywords_str}\n"
                f"Outline:\n{outline_str}\n"
            )

        instructions = self._section_instructions(section)
        return f"{base}\n{instructions}"

    def _section_instructions(self, section: str) -> str:
        """Return section-specific instructions for the LLM prompt.

        Complexity: O(1) — dict lookup
        """
        if self.language == "uk":
            instructions: dict[str, str] = {
                "hook": (
                    "Напиши захопливий хук (150–200 слів). "
                    "Почни з інтригуючого питання або шокуючого факту. "
                    "НЕ представляйся. Одразу захопи увагу глядача."
                ),
                "intro": (
                    "Напиши вступ (70–90 слів). "
                    "Представ себе і поясни чому ця тема важлива для глядача. "
                    "Скажи що вони дізнаються з цього відео."
                ),
                "body_1": (
                    "Напиши перший основний розділ (140–180 слів). "
                    "Розкрий перший ключовий пункт теми детально і з прикладами."
                ),
                "body_2": (
                    "Напиши другий основний розділ (140–180 слів). "
                    "Розкрий другий ключовий пункт теми детально і з прикладами."
                ),
                "body_3": (
                    "Напиши третій основний розділ (140–180 слів). "
                    "Розкрий третій ключовий пункт з практичними порадами."
                ),
                "cta": (
                    "Напиши заклик до дії (70–90 слів). "
                    "Попроси глядача підписатися, поставити лайк і написати коментар. "
                    "Поверни до питання з хуку і відповідай на нього одним реченням."
                ),
            }
        else:
            instructions = {
                "hook": (
                    "Write an engaging hook (150–200 words). "
                    "Start with a surprising fact or compelling question. "
                    "Do NOT introduce yourself. Grab attention immediately."
                ),
                "intro": (
                    "Write the intro (70–90 words). "
                    "Introduce yourself briefly and explain why this topic matters. "
                    "Tell viewers what they will learn."
                ),
                "body_1": (
                    "Write the first main section (140–180 words). "
                    "Cover the first key point with details and examples."
                ),
                "body_2": (
                    "Write the second main section (140–180 words). "
                    "Cover the second key point with details and examples."
                ),
                "body_3": (
                    "Write the third main section (140–180 words). "
                    "Cover the third point with practical tips."
                ),
                "cta": (
                    "Write the call-to-action (70–90 words). "
                    "Ask viewers to subscribe, like, and comment. "
                    "Circle back to the hook question with a one-sentence answer."
                ),
            }
        return instructions.get(section, "Write this section clearly and engagingly.")

    def _pick_keywords(
        self,
        keywords: list[str],
        section: str,
        rng: np.random.Generator,
    ) -> list[str]:
        """Select up to _MAX_KEYWORDS_PER_SECTION keywords for injection.

        Algorithm: reservoir sampling → O(k) where k = _MAX_KEYWORDS_PER_SECTION.

        Parameters
        ----------
        keywords:
            Full keyword list from ContentPlan.
        section:
            Section name (hook always gets the top keywords).
        rng:
            Seeded generator for reproducible selection.

        Returns
        -------
        list[str]
            Selected keywords for this section.
        """
        if not keywords:
            return []
        if section == "hook":
            return keywords[:_MAX_KEYWORDS_PER_SECTION]
        # Random sample for other sections
        n = min(_MAX_KEYWORDS_PER_SECTION, len(keywords))
        indices = rng.choice(len(keywords), size=n, replace=False)
        return [keywords[int(i)] for i in sorted(indices)]

    @staticmethod
    def _inject_keywords(text: str, keywords: list[str]) -> str:
        """Ensure keywords appear in the text at least once.

        Algorithm: set-intersection check + append missing keywords.
        O(words × keywords) — acceptable for ≤ 50 keywords (MVP).
        Phase 6: replace with Aho-Corasick for O(words + keywords).

        Parameters
        ----------
        text:
            Generated section text.
        keywords:
            Keywords that should appear in the text.

        Returns
        -------
        str
            Text with all keywords present (appended if missing).

        Examples
        --------
        >>> ScriptGenerator._inject_keywords("Hello world", ["Python"])
        'Hello world (Python)'
        """
        if not keywords:
            return text
        text_lower = text.lower()
        missing = [kw for kw in keywords if kw.lower() not in text_lower]
        if missing:
            keyword_str = ", ".join(missing)
            text = f"{text} ({keyword_str})"
        return text

    @staticmethod
    def _validate_script(script: Script) -> None:
        """Raise ValueError if script does not meet quality criteria.

        Criteria:
          - total_words ≥ MIN_TOTAL_WORDS (500)
          - all section names present in SECTION_ORDER

        Complexity: O(n_sections)

        Parameters
        ----------
        script:
            Script to validate.

        Raises
        ------
        ValueError
            If any criterion is not met.
        """
        if script.total_words < MIN_TOTAL_WORDS:
            raise ValueError(
                f"Script too short: {script.total_words} words "
                f"(minimum {MIN_TOTAL_WORDS}). "
                "Increase token budget or regenerate."
            )
        section_names = {s.name for s in script.sections}
        missing = [s for s in SECTION_ORDER if s not in section_names]
        if missing:
            raise ValueError(f"Script missing sections: {missing}")

