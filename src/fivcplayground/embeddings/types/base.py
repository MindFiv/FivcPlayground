from pydantic import BaseModel, Field


class EmbeddingConfig(BaseModel):
    """Configuration for an embedding function."""

    id: str = Field(..., description="Unique identifier for the embedding function")
    description: str | None = Field(
        default=None, description="Description of the embedding function"
    )
    provider: str = Field(..., description="Provider of the embedding function")
    model: str = Field(
        ...,
        description="Model name (e.g., 'text-embedding-ada-002', 'all-MiniLM-L6-v2')",
    )
    api_key: str | None = Field(
        default=None, description="API key for the embedding function (if required)"
    )
    base_url: str | None = Field(
        default=None, description="Base URL for the embedding function (if applicable)"
    )
    dimension: int = Field(
        default=1024, description="Dimension of the embedding vector"
    )
