"""FastAPI scoring service.

Exposes the propensity model for online and batch inference. The service
loads a model version from the registry at startup and serves predictions
over HTTP. It is designed to sit behind a load balancer and to emit
scoring events to the event bus for downstream lifecycle automation.

Run locally with::

    uvicorn src.api.scoring_service:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from src.api.schemas import (
    BatchScoreRequest,
    BatchScoreResponse,
    ModelInfo,
    ScoreRequest,
    ScoreResponse,
)

app = FastAPI(
    title="User Lifecycle Scoring Service",
    description="Subscription propensity scoring for real-time and batch use.",
    version="0.1.0",
)


class ScoringService:
    """Encapsulates model loading and inference logic.

    Holds the active model and feature lookup so request handlers stay
    thin. Separated from the FastAPI app to keep the inference logic
    independently testable.
    """

    def __init__(self) -> None:
        """Initialize an empty service; call :meth:`load` before serving."""
        self._model = None
        self._model_version: str = ""

    def load(self, name: str, version: str) -> None:
        """Load a model version from the registry into memory.

        Args:
            name: Registered model name.
            version: Version identifier to serve.
        """
        raise NotImplementedError

    def score_one(self, request: ScoreRequest) -> ScoreResponse:
        """Score a single user.

        Args:
            request: The scoring request.

        Returns:
            The scoring response.
        """
        raise NotImplementedError

    def score_batch(self, request: BatchScoreRequest) -> BatchScoreResponse:
        """Score a batch of users.

        Args:
            request: The batch scoring request.

        Returns:
            The batch scoring response.
        """
        raise NotImplementedError

    def model_info(self) -> ModelInfo:
        """Return metadata about the served model."""
        raise NotImplementedError


service = ScoringService()


@app.post("/score/user/{user_id}", response_model=ScoreResponse)
def score_user(user_id: str, request: ScoreRequest) -> ScoreResponse:
    """Score a single user in real time."""
    raise NotImplementedError


@app.post("/score/batch", response_model=BatchScoreResponse)
def score_batch(request: BatchScoreRequest) -> BatchScoreResponse:
    """Score a batch of users."""
    raise NotImplementedError


@app.get("/model/info", response_model=ModelInfo)
def model_info() -> ModelInfo:
    """Return metadata about the currently served model."""
    raise NotImplementedError
