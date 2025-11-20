from typing import List, Dict, Literal

from pydantic import BaseModel, Field


class ToolConfig(BaseModel):
    """Configuration for a tool."""

    id: str = Field(..., description="Unique identifier for the tool")
    # name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Description of the tool")
    transport: Literal["stdio", "sse", "streamable_http"] = Field(
        ...,
        description="Transport protocol for the tool",
    )
    command: str | None = Field(None, description="Command to run the tool")
    args: List[str] | None = Field(None, description="Arguments for the command")
    env: Dict[str, str] | None = Field(None, description="Environment variables")
    url: str | None = Field(None, description="URL for the tool")
