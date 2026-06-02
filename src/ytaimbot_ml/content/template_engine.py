"""Phase 2 — TemplateEngine: dynamic content template selection and rendering.

Roadmap tasks: T-136 through T-150 (EPIC 2.5)

Algorithm
---------
Template Selection (Cosine Similarity):
  1. Load templates from src/ytaimbot_ml/content/templates/*.md
  2. Parse tags from front-matter
  3. Vectorize ContentPlan.keywords vs Template.tags (TF-IDF-like bag of words)
  4. Compute cosine similarity: score = (A · B) / (||A|| × ||B||)
  5. Select max score template (fallback: explainer.md)

  Complexity: O(n_templates × n_keywords)

Rendering:
  1. Replace {placeholder} with variables via string interpolation.
  2. Complexity: O(n) per character.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

import numpy as np

if TYPE_CHECKING:
    from ytaimbot_ml.schemas import ContentPlan

logger = logging.getLogger(__name__)

_DEFAULT_TEMPLATE_DIR = Path(__file__).parent / "templates"
_FALLBACK_TEMPLATE = "explainer.md"


@dataclass
class Template:
    """Represents a Markdown script template with tags."""
    name: str
    tags: List[str]
    content: str


class TemplateEngine:
    """Loads, selects, and renders script templates.

    Complexity
    ----------
    select_template(): O(n_templates × n_keywords)
    render(): O(chars)
    """

    def __init__(self, template_dir: str | Path | None = None) -> None:
        self._dir = Path(template_dir) if template_dir else _DEFAULT_TEMPLATE_DIR
        self._cache: Dict[str, Template] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load and parse templates from the directory.  O(n_files × n_chars)."""
        if not self._dir.exists():
            logger.warning("TemplateEngine: directory %s does not exist", self._dir)
            return

        for path in self._dir.glob("*.md"):
            try:
                content = path.read_text(encoding="utf-8")
                # Simple front-matter parser (T-143)
                match = re.search(r"^---\s*\ntags:\s*\[(.*?)\]\s*\n---\s*\n(.*)$", content, re.DOTALL | re.MULTILINE)
                if match:
                    tags_str, body = match.groups()
                    tags = [t.strip() for t in tags_str.split(",") if t.strip()]
                    self._cache[path.name] = Template(name=path.name, tags=tags, content=body)
                    logger.debug("TemplateEngine: loaded %s with tags %s", path.name, tags)
                else:
                    logger.warning("TemplateEngine: invalid front-matter in %s", path.name)
            except Exception as exc:
                logger.error("TemplateEngine: failed to load %s: %s", path.name, exc)

    def select_template(self, plan: ContentPlan) -> Template:
        """Select the best template for a ContentPlan via keyword similarity.

        Algorithm: Cosine Similarity (T-144) — O(n_templates × n_keywords).

        Parameters
        ----------
        plan:
            ContentPlan with keywords to match against template tags.

        Returns
        -------
        Template
            Best matching template or explainer.md fallback.
        """
        if not self._cache:
            logger.error("TemplateEngine: no templates loaded, returning dummy")
            return Template("dummy", [], "# {title}\n{hook}\n{body_1}\n{cta}")

        plan_keywords = set(k.lower().strip() for k in plan.keywords)
        best_score = -1.0
        best_template = self._cache.get(_FALLBACK_TEMPLATE) or next(iter(self._cache.values()))

        for template in self._cache.values():
            template_tags = set(t.lower().strip() for t in template.tags)
            
            # Simple Cosine Similarity proxy for sets: Jaccard-like or Overlap
            # score = len(A ∩ B) / sqrt(len(A) * len(B))
            intersection = plan_keywords.intersection(template_tags)
            if not intersection:
                score = 0.0
            else:
                score = len(intersection) / np.sqrt(len(plan_keywords) * len(template_tags))

            if score > best_score:
                best_score = score
                best_template = template

        logger.debug(
            "TemplateEngine: selected %s for plan %s (score=%.2f)",
            best_template.name,
            plan.trend_id,
            best_score,
        )
        return best_template

    def render(self, template: Template, variables: Dict[str, str]) -> str:
        """Replace {placeholder} in template with variables.  O(n_chars).

        Parameters
        ----------
        template:
            The template to render.
        variables:
            Mapping of placeholder name → value.

        Returns
        -------
        str
            Rendered markdown content.
        """
        content = template.content
        for key, val in variables.items():
            content = content.replace(f"{{{key}}}", val)
        return content
