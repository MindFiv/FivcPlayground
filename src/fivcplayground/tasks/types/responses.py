from typing import List

from pydantic import BaseModel, Field


class TaskAssessment(BaseModel):
    """Assessment result for task complexity."""

    model_config = {"populate_by_name": True}

    require_planning: bool = Field(
        description="Whether a planning agent is required to break down the task",
        alias="requires_planning_agent",
    )
    reasoning: str = Field(default="", description="Reasoning for the assessment")


class TaskRequirement(BaseModel):
    """Tool requirements for a task."""

    tools: List[str] = Field(description="List of tools needed for the task")
