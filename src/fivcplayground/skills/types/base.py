from pydantic import BaseModel, Field


class SkillConfig(BaseModel):
    """Skill configuration."""

    id: str = Field(..., description="Unique identifier for the skill")
    description: str = Field(..., description="Description for semantic discovery")
    path: str | None = Field(
        default=None,
        description="Path/URL to the skill, ignore attributes below if path is set",
    )
    instructions: str | None = Field(
        default=None,
        description="Instructions injected into agent context when skill is applied",
    )
    tool_ids: list[str] | None = Field(
        default=None, description="Tool IDs to merge into agent tool set"
    )
    resources: dict[str, str] | None = Field(
        default=None, description="Reference materials (name -> markdown content)"
    )
