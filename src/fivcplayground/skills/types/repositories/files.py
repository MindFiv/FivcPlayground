"""
File-based skill configuration repository implementation.

Storage Structure:
    /<output_dir>/configs/
    └── skills.yaml    # All skill configurations (mapping of skill_id -> SkillConfig)
"""

import yaml
from pathlib import Path
from typing import Optional, List

from fivcplayground.skills.types.base import SkillConfig
from fivcplayground.skills.types.repositories.base import SkillConfigRepository
from fivcplayground.utils import OutputDir


class FileSkillConfigRepository(SkillConfigRepository):
    """File-based repository for skill configurations stored in a single YAML file."""

    def __init__(self, output_dir: Optional[OutputDir] = None):
        self.output_dir = output_dir or OutputDir().subdir("configs")
        self.base_path = Path(str(self.output_dir))
        self.skills_file = self.base_path / "skills.yaml"
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _load_skills_data(self) -> dict:
        if not self.skills_file.exists():
            return {}
        try:
            with open(self.skills_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if data is not None else {}
        except (yaml.YAMLError, ValueError) as e:
            print(f"Error loading skills from {self.skills_file.name}: {e}")
            return {}

    def _save_skills_data(self, skills_data: dict) -> None:
        with open(self.skills_file, "w", encoding="utf-8") as f:
            yaml.dump(skills_data, f, default_flow_style=False, allow_unicode=True)

    async def update_skill_config_async(self, skill_config: SkillConfig) -> None:
        skill_id = skill_config.id
        skills_data = self._load_skills_data()
        skill_data = skill_config.model_dump(mode="json")
        skills_data[skill_id] = skill_data
        self._save_skills_data(skills_data)

    async def get_skill_config_async(self, skill_id: str) -> Optional[SkillConfig]:
        skills_data = self._load_skills_data()
        if skill_id not in skills_data:
            return None
        try:
            skill_data = skills_data[skill_id]
            skill_data["id"] = skill_id
            return SkillConfig.model_validate(skill_data)
        except ValueError as e:
            print(f"Error loading skill config {skill_id}: {e}")
            return None

    async def list_skill_configs_async(self) -> List[SkillConfig]:
        skills_data = self._load_skills_data()
        configs = []
        for skill_id in sorted(skills_data.keys()):
            try:
                skill_data = skills_data[skill_id]
                skill_data["id"] = skill_id
                config = SkillConfig.model_validate(skill_data)
                configs.append(config)
            except ValueError as e:
                print(f"Error loading skill config {skill_id}: {e}")
        return configs

    async def delete_skill_config_async(self, skill_id: str) -> None:
        skills_data = self._load_skills_data()
        if skill_id in skills_data:
            del skills_data[skill_id]
            self._save_skills_data(skills_data)
