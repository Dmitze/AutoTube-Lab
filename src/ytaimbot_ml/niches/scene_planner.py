"""Scene planner for Ghibli ASMR videos — Phase P11 (T-907–T-909).

Converts raw LLM output or deterministic templates into structured
Scene objects that drive image generation and video assembly.

Complexity notes
----------------
parse_llm_output:         O(n) where n = lines in raw_text
generate_template_scenes: O(n) where n = scenes_per_video
build_imagen_prompt:      O(k) where k = number of character_ids in scene
to_timeline:              O(n)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np

from ytaimbot_ml.niches.character_registry import CharacterRegistry
from ytaimbot_ml.niches.ghibli_asmr import GhibliASMRProfile

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Template bank for deterministic scene generation (no LLM fallback)
# ---------------------------------------------------------------------------

_SCENE_TEMPLATES: list[str] = [
    "a {character} prepares morning tea by a frosted window",
    "warm amber light spills across a wooden table cluttered with herbs",
    "a {character} tends to potted plants on a rain-dappled windowsill",
    "a cat curls up beside a glowing wood stove",
    "bread bakes in a stone oven, golden crust forming slowly",
    "lanterns sway gently in a light evening breeze",
    "a {character} reads a handwritten letter under a soft lamp",
    "rain taps steadily on old roof tiles outside",
    "a {character} embroiders by candlelight, needle glinting",
    "cherry blossoms drift past an open shoji screen",
]


@dataclass
class Scene:
    """One 6–7 second scene in a Ghibli ASMR video.

    Parameters
    ----------
    scene_id:
        1-indexed scene number within the video.
    total_scenes:
        Total number of scenes in the video.
    prompt:
        Full Imagen/Grok animation prompt for this scene.
    character_ids:
        IDs of characters referenced in this scene.
    ambient_sounds:
        List of ambient sound descriptors for the audio layer.
    duration_seconds:
        Duration of this scene in seconds (default: 7).

    Complexity
    ----------
    O(1) — data container

    Examples
    --------
    >>> s = Scene(scene_id=1, total_scenes=50,
    ...           prompt="Hanna pours tea by a frosted window, snow outside",
    ...           character_ids=["c1"])
    >>> s.label
    'Scene 1/50'
    """

    scene_id: int
    total_scenes: int
    prompt: str
    character_ids: list[str] = field(default_factory=list)
    ambient_sounds: list[str] = field(default_factory=lambda: ["wind", "fire crackling"])
    duration_seconds: int = 7

    @property
    def label(self) -> str:
        """Human-readable scene label.

        Complexity: O(1)

        Examples
        --------
        >>> Scene(scene_id=3, total_scenes=50, prompt="test").label
        'Scene 3/50'
        """
        return f"Scene {self.scene_id}/{self.total_scenes}"


class ScenePlanner:
    """Generates a list of Scene objects from LLM output or template bank.

    Takes raw LLM output (one scene per line) and structures it into
    Scene dataclasses with consistent character references.  Falls back
    to a deterministic template bank when no LLM output is available.

    Parameters
    ----------
    profile:
        GhibliASMRProfile controlling scene count and style.
    registry:
        CharacterRegistry providing character prompt fragments.

    Algorithm
    ---------
    parse_llm_output:         linear scan O(n)
    generate_template_scenes: O(n) template cycling
    build_imagen_prompt:      O(k) character lookups
    to_timeline:              O(n) sequential accumulation

    Examples
    --------
    >>> from ytaimbot_ml.niches.ghibli_asmr import GhibliASMRProfile
    >>> from ytaimbot_ml.niches.character_registry import CharacterRegistry
    >>> planner = ScenePlanner(profile=GhibliASMRProfile(), registry=CharacterRegistry("ch1"))
    >>> raw = "\\n".join(f"Scene description {i}" for i in range(50))
    >>> scenes = planner.parse_llm_output(raw)
    >>> len(scenes)
    50
    >>> scenes[0].scene_id
    1
    """

    def __init__(self, profile: GhibliASMRProfile, registry: CharacterRegistry) -> None:
        self._profile = profile
        self._registry = registry
        logger.debug(
            "ScenePlanner init: sub_niche=%s scenes=%d",
            profile.sub_niche.value,
            profile.scenes_per_video,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse_llm_output(self, raw_text: str) -> list[Scene]:
        """Parse raw LLM text into Scene objects (one scene per non-empty line).

        Lines are trimmed; empty lines are skipped.  If fewer lines than
        ``scenes_per_video`` are found, the available scenes are returned
        (no padding).  If more are found, only the first
        ``scenes_per_video`` are used.

        Parameters
        ----------
        raw_text:
            Raw newline-separated scene descriptions from the LLM.

        Returns
        -------
        list[Scene]
            Structured scene list, length ≤ scenes_per_video.

        Complexity: O(n) where n = number of lines

        Examples
        --------
        >>> planner = ScenePlanner(GhibliASMRProfile(), CharacterRegistry("ch1"))
        >>> scenes = planner.parse_llm_output("\\n".join(f"desc {i}" for i in range(50)))
        >>> len(scenes)
        50
        >>> scenes[0].label
        'Scene 1/50'
        """
        lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
        target = self._profile.scenes_per_video
        lines = lines[:target]
        total = self._profile.scenes_per_video

        scenes = [
            Scene(
                scene_id=idx + 1,
                total_scenes=total,
                prompt=line,
                duration_seconds=self._profile.seconds_per_scene,
            )
            for idx, line in enumerate(lines)
        ]
        logger.info("parse_llm_output: produced %d scenes", len(scenes))
        return scenes

    def generate_template_scenes(self, topic: str, rng: np.random.Generator) -> list[Scene]:
        """Generate deterministic template-based scenes when no LLM is available.

        Cycles through the built-in template bank with RNG-shuffled character
        names to produce varied but reproducible scene descriptions.

        Parameters
        ----------
        topic:
            Short topic string injected into prompts (e.g. "morning on the hill").
        rng:
            Seeded NumPy random generator for reproducibility.

        Returns
        -------
        list[Scene]
            Scene list of length ``profile.scenes_per_video``.

        Complexity: O(n) where n = scenes_per_video

        Examples
        --------
        >>> import numpy as np
        >>> planner = ScenePlanner(GhibliASMRProfile(), CharacterRegistry("ch1"))
        >>> scenes = planner.generate_template_scenes("forest morning", np.random.default_rng(42))
        >>> len(scenes)
        50
        >>> scenes[0].scene_id
        1
        """
        characters = self._registry.list_all()
        char_names = [c.name for c in characters] if characters else ["a villager"]

        n = self._profile.scenes_per_video
        total = n
        template_count = len(_SCENE_TEMPLATES)

        # Shuffle template indices once for deterministic variety
        indices = rng.integers(0, template_count, size=n)

        scenes: list[Scene] = []
        for i, tmpl_idx in enumerate(indices):
            char_name = char_names[int(rng.integers(0, len(char_names)))]
            template = _SCENE_TEMPLATES[int(tmpl_idx)]
            prompt = f"{topic} — {template.format(character=char_name)}"
            scenes.append(
                Scene(
                    scene_id=i + 1,
                    total_scenes=total,
                    prompt=prompt,
                    duration_seconds=self._profile.seconds_per_scene,
                )
            )

        logger.info("generate_template_scenes: topic=%r produced %d scenes", topic, len(scenes))
        return scenes

    def build_imagen_prompt(self, scene: Scene) -> str:
        """Combine style prefix, scene prompt, and character fragments.

        Parameters
        ----------
        scene:
            Scene object whose ``prompt`` and ``character_ids`` are used.

        Returns
        -------
        str
            Full Imagen prompt ready for image generation.

        Complexity: O(k) where k = number of character_ids in scene

        Examples
        --------
        >>> from ytaimbot_ml.niches.character_registry import Character
        >>> reg = CharacterRegistry("ch1")
        >>> reg.add(Character("c1", "ch1", "Hanna", "elderly woman, white hair"))
        >>> planner = ScenePlanner(GhibliASMRProfile(), reg)
        >>> s = Scene(1, 50, "Hanna pours tea", character_ids=["c1"])
        >>> prompt = planner.build_imagen_prompt(s)
        >>> "Studio Ghibli style" in prompt
        True
        >>> "Hanna: elderly woman" in prompt
        True
        """
        prefix = self._profile.scene_prompt_prefix()
        char_fragments = []
        for cid in scene.character_ids:
            char = self._registry.get(cid)
            if char is not None:
                char_fragments.append(char.imagen_prompt_fragment)

        parts = [prefix, scene.prompt]
        if char_fragments:
            parts.append("; ".join(char_fragments))

        prompt = ". ".join(parts)
        logger.debug("build_imagen_prompt: scene=%s chars=%d", scene.label, len(char_fragments))
        return prompt

    def to_timeline(self, scenes: list[Scene]) -> list[dict]:
        """Convert scenes to a sequential timeline representation.

        Each dict entry contains the start/end timestamps, full Imagen
        prompt, and human-readable label for use by video assemblers.

        Parameters
        ----------
        scenes:
            Ordered list of Scene objects.

        Returns
        -------
        list[dict]
            List of ``{start_s, end_s, prompt, label}`` dicts.

        Complexity: O(n) where n = len(scenes)

        Examples
        --------
        >>> planner = ScenePlanner(GhibliASMRProfile(), CharacterRegistry("ch1"))
        >>> scenes = [Scene(i+1, 3, f"desc {i}", duration_seconds=7) for i in range(3)]
        >>> tl = planner.to_timeline(scenes)
        >>> tl[0]["start_s"], tl[0]["end_s"]
        (0, 7)
        >>> tl[1]["start_s"]
        7
        """
        timeline: list[dict] = []
        cursor = 0
        for scene in scenes:
            entry = {
                "start_s": cursor,
                "end_s": cursor + scene.duration_seconds,
                "prompt": self.build_imagen_prompt(scene),
                "label": scene.label,
            }
            timeline.append(entry)
            cursor += scene.duration_seconds

        logger.debug("to_timeline: %d entries, total_s=%d", len(timeline), cursor)
        return timeline
