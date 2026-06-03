"""Pydantic schemas for the scoring API.

Defines the request and response contracts shared between the FastAPI
service and its clients. Keeping schemas in one module gives a single
source of truth for the API surface and enables automatic OpenAPI docs.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class UserFeatures(BaseModel):
    """Feature payload for a single user in real-time scoring requests."""

    features: Dict[str, float] = Field(
        ..., description="Mapping of feature name to value."
    )


class ScoreRequest(BaseModel):
    """Real-time scoring request for one user."""

    user_id: str = Field(..., description="Opaque user identifier.")
    features: Optional[Dict[str, float]] = Field(
        None,
        description="Optional inline features; if omitted, features are "
        "looked up from the online feature store.",
    )


class ScoreResponse(BaseModel):
    """Scoring response for one user."""

    user_id: str
    propensity: float = Field(..., description="Subscription probability in [0, 1].")
    segment: Optional[str] = Field(None, description="Behavioral segment label.")
    model_version: str
    top_factors: Optional[List[Dict[str, float]]] = Field(
        None, description="Top SHAP contributions: feature -> contribution."
    )


class BatchScoreRequest(BaseModel):
    """Batch scoring request for multiple users."""

    users: List[ScoreRequest]


class BatchScoreResponse(BaseModel):
    """Batch scoring response."""

    results: List[ScoreResponse]
    model_version: str


class ModelInfo(BaseModel):
    """Metadata about the currently served model."""

    name: str
    version: str
    trained_at: Optional[str] = None
    metrics: Optional[Dict[str, float]] = None
    feature_count: Optional[int] = None
