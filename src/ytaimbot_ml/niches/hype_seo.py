"""SEO helpers for Hype niche (Phase P13, T-943)."""

from __future__ import annotations

from dataclasses import dataclass

from ytaimbot_ml.niches.hype_characters import HypeCharacter, HypeCharactersProfile


@dataclass(frozen=True)
class HypeThumbnailTemplate:
    """Thumbnail concept prompt for visual generation.

    Complexity: O(1).
    """

    prompt: str
    labels: tuple[str, str]


class HypeSEO:
    """Generate hype-specific title, tags, and thumbnail templates.

    Complexity
    ----------
    title(): O(1)
    tags(): O(1)
    thumbnail(): O(1)

    Examples
    --------
    >>> p = HypeSEO()
    >>> title = p.title("Judy Hopps", "betrayal_drama")
    >>> len(title) <= 100
    True
    """

    def __init__(self, profile: HypeCharactersProfile | None = None) -> None:
        self._profile = profile or HypeCharactersProfile()

    def title(self, character_name: str, story_template: str) -> str:
        """Generate CTR-oriented title. O(1)."""
        return self._profile.get_seo_title(character_name, story_template)

    def tags(self, character_name: str, franchise: str) -> list[str]:
        """Generate SEO tags list. O(1)."""
        return self._profile.get_seo_tags(character_name, franchise)

    def thumbnail(self, character: HypeCharacter, story_template: str) -> HypeThumbnailTemplate:
        """Build thumbnail prompt and label pair for editing overlays. O(1).

        Examples
        --------
        >>> from ytaimbot_ml.niches.hype_characters import HypeCharacter, HypeSource
        >>> c = HypeCharacter("Judy Hopps", "Zootopia 2", 0.9, HypeSource.MANUAL)
        >>> out = HypeSEO().thumbnail(c, "betrayal_drama")
        >>> "Judy Hopps" in out.prompt
        True
        """
        shock_label = "WHAT HAPPENED?!"
        emotion_label = "BETRAYAL" if "betrayal" in story_template else "NO WAY!"
        prompt = (
            f"Cinematic cartoon thumbnail, close-up {character.name} from {character.franchise}, "
            "tearful eyes, dramatic rim light, high contrast, vibrant colors, "
            f"story={story_template}, emotion={emotion_label}, clickbait-safe composition."
        )
        return HypeThumbnailTemplate(
            prompt=prompt,
            labels=(shock_label, emotion_label),
        )

