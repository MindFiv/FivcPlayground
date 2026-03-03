from abc import ABC, abstractmethod
from typing import List

from fivcplayground.skills.types.base import SkillConfig


class SkillConfigRepository(ABC):
    """Abstract base class for skill configuration repositories."""

    @abstractmethod
    async def get_skill_config_async(self, skill_id: str) -> SkillConfig | None:
        """Retrieve a skill configuration by ID."""

    @abstractmethod
    async def list_skill_configs_async(self) -> List[SkillConfig]:
        """List all skill configurations."""

    @abstractmethod
    async def update_skill_config_async(self, skill_config: SkillConfig) -> None:
        """Create or update a skill configuration."""

    @abstractmethod
    async def delete_skill_config_async(self, skill_id: str) -> None:
        """Delete a skill configuration."""
