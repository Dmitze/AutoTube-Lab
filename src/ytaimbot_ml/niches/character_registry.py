"""Character registry for persistent Ghibli ASMR characters — Phase P11 (T-904–T-906).

Characters are defined once per channel and referenced in scene prompts by ID,
ensuring visual consistency across all 50 scenes of a video.

Complexity notes
----------------
CharacterRegistry.add():    O(1)
CharacterRegistry.get():    O(1) dict lookup
CharacterRegistry.list_all: O(k) where k = characters in channel
CharacterRegistry.remove(): O(1)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Character:
    """A persistent character used across Ghibli ASMR scenes.

    Parameters
    ----------
    char_id:
        Unique character identifier (e.g. "c1", "elderly_woman").
    channel_id:
        YouTube channel ID that owns this character definition.
    name:
        Human-readable character name (e.g. "Hanna").
    description:
        Verbatim visual description injected into image generation prompts.
    created_at:
        UTC timestamp of character creation.

    Complexity
    ----------
    O(1) — data container

    Examples
    --------
    >>> c = Character(char_id="c1", channel_id="ch1", name="Hanna",
    ...               description="elderly woman, white hair bun, warm apron, blue eyes")
    >>> c.imagen_prompt_fragment
    'Hanna: elderly woman, white hair bun, warm apron, blue eyes'
    """

    char_id: str
    channel_id: str
    name: str
    description: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def imagen_prompt_fragment(self) -> str:
        """Return the prompt fragment for image generation.

        Complexity: O(1)

        Returns
        -------
        str
            ``"<name>: <description>"`` ready for injection into an Imagen prompt.

        Examples
        --------
        >>> c = Character("c1", "ch1", "Hanna", "elderly woman, white hair bun")
        >>> c.imagen_prompt_fragment
        'Hanna: elderly woman, white hair bun'
        """
        return f"{self.name}: {self.description}"


class CharacterRegistry:
    """Stores and retrieves Character definitions for a channel.

    Characters are stored in-memory (dict) and optionally persisted
    to a storage backend for cross-run consistency.

    Parameters
    ----------
    channel_id:
        YouTube channel ID that owns the registry.
    storage:
        Optional storage backend (duck-typed: must implement ``get``/``set``).
        Pass ``None`` (default) for pure in-memory operation.

    Complexity
    ----------
    add():              O(1)
    get():              O(1) dict lookup
    list_all():         O(k) where k = characters in channel
    remove():           O(1)
    load_from_storage:  O(k)

    Examples
    --------
    >>> registry = CharacterRegistry(channel_id="my_channel")
    >>> registry.add(Character("c1", "my_channel", "Hanna", "elderly woman"))
    >>> registry.get("c1").name
    'Hanna'
    >>> len(registry.list_all())
    1
    """

    def __init__(self, channel_id: str, storage: Any | None = None) -> None:
        self._channel_id = channel_id
        self._storage = storage
        self._chars: dict[str, Character] = {}
        logger.debug("CharacterRegistry init: channel_id=%s storage=%s", channel_id, storage is not None)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(self, character: Character) -> None:
        """Add a character to the in-memory store and optionally persist it.

        Parameters
        ----------
        character:
            Character instance to register.

        Complexity: O(1)

        Examples
        --------
        >>> reg = CharacterRegistry("ch1")
        >>> reg.add(Character("c1", "ch1", "Hanna", "elderly woman"))
        >>> reg.get("c1") is not None
        True
        """
        self._chars[character.char_id] = character
        logger.debug("Added character: char_id=%s name=%s", character.char_id, character.name)
        if self._storage is not None:
            try:
                self._storage.set(f"char:{self._channel_id}:{character.char_id}", self.to_dict())
            except Exception:  # noqa: BLE001
                logger.exception("Failed to persist character %s", character.char_id)

    def get(self, char_id: str) -> Character | None:
        """Retrieve a character by its ID.

        Parameters
        ----------
        char_id:
            Unique character identifier.

        Returns
        -------
        Character | None
            The Character if found, else None.

        Complexity: O(1)

        Examples
        --------
        >>> reg = CharacterRegistry("ch1")
        >>> reg.add(Character("c1", "ch1", "Hanna", "elderly woman"))
        >>> reg.get("c1").name
        'Hanna'
        >>> reg.get("missing") is None
        True
        """
        return self._chars.get(char_id)

    def list_all(self) -> list[Character]:
        """Return all characters registered for this channel.

        Returns
        -------
        list[Character]
            List of Character objects in insertion order.

        Complexity: O(k) where k = number of characters

        Examples
        --------
        >>> reg = CharacterRegistry("ch1")
        >>> reg.add(Character("c1", "ch1", "Hanna", "elderly woman"))
        >>> reg.add(Character("c2", "ch1", "Kiri", "young girl, red dress"))
        >>> len(reg.list_all())
        2
        """
        return list(self._chars.values())

    def remove(self, char_id: str) -> bool:
        """Remove a character by ID.

        Parameters
        ----------
        char_id:
            Unique character identifier.

        Returns
        -------
        bool
            True if the character existed and was removed, False otherwise.

        Complexity: O(1)

        Examples
        --------
        >>> reg = CharacterRegistry("ch1")
        >>> reg.add(Character("c1", "ch1", "Hanna", "elderly woman"))
        >>> reg.remove("c1")
        True
        >>> reg.remove("c1")
        False
        """
        if char_id in self._chars:
            del self._chars[char_id]
            logger.debug("Removed character: char_id=%s", char_id)
            return True
        return False

    def load_from_storage(self) -> int:
        """Load characters from the storage backend into memory.

        Returns
        -------
        int
            Number of characters loaded.

        Complexity: O(k) where k = characters in storage

        Examples
        --------
        >>> reg = CharacterRegistry("ch1")
        >>> reg.load_from_storage()
        0
        """
        if self._storage is None:
            return 0
        try:
            raw = self._storage.get(f"char:{self._channel_id}:all")
            if raw is None:
                return 0
            loaded = CharacterRegistry.from_dict(raw, self._channel_id)
            self._chars = loaded._chars
            count = len(self._chars)
            logger.info("Loaded %d characters from storage", count)
            return count
        except Exception:  # noqa: BLE001
            logger.exception("Failed to load characters from storage")
            return 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize all characters to a plain dictionary.

        Returns
        -------
        dict
            ``{"channel_id": ..., "characters": [{...}, ...]}``

        Complexity: O(k)

        Examples
        --------
        >>> reg = CharacterRegistry("ch1")
        >>> reg.add(Character("c1", "ch1", "Hanna", "elderly woman"))
        >>> d = reg.to_dict()
        >>> d["channel_id"]
        'ch1'
        >>> d["characters"][0]["name"]
        'Hanna'
        """
        return {
            "channel_id": self._channel_id,
            "characters": [
                {
                    "char_id": c.char_id,
                    "channel_id": c.channel_id,
                    "name": c.name,
                    "description": c.description,
                    "created_at": c.created_at.isoformat(),
                }
                for c in self._chars.values()
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], channel_id: str) -> CharacterRegistry:
        """Deserialize a CharacterRegistry from a plain dictionary.

        Parameters
        ----------
        data:
            Dict produced by ``to_dict()``.
        channel_id:
            Channel ID to associate with the registry.

        Returns
        -------
        CharacterRegistry
            Populated registry instance.

        Complexity: O(k)

        Examples
        --------
        >>> reg = CharacterRegistry("ch1")
        >>> reg.add(Character("c1", "ch1", "Hanna", "elderly woman"))
        >>> reg2 = CharacterRegistry.from_dict(reg.to_dict(), "ch1")
        >>> reg2.get("c1").name
        'Hanna'
        """
        registry = cls(channel_id=channel_id)
        for entry in data.get("characters", []):
            char = Character(
                char_id=entry["char_id"],
                channel_id=entry["channel_id"],
                name=entry["name"],
                description=entry["description"],
            )
            registry._chars[char.char_id] = char
        return registry
