# API Specification

Scoring service HTTP API. All request and response bodies are JSON. Schemas
are defined in `src/api/schemas.py` and surfaced automatically via the
FastAPI OpenAPI docs at `/docs` when the service is running.

Base URL (local): `http://localhost:8000`

---

## POST `/score/user/{user_id}`

Real-time scoring for a single user.

**Path parameters**

| Name      | Type   | Description              |
|-----------|--------|--------------------------|
| `user_id` | string | Opaque user identifier.  |

**Request body** (`ScoreRequest`)

```json
{
  "user_id": "u_123",
  "features": { "recency_days": 3.0, "sessions_30d": 12.0 }
}
```

`features` is optional. When omitted, the service looks features up from the
online feature store.

**Response** (`ScoreResponse`)

```json
{
  "user_id": "u_123",
  "propensity": 0.78,
  "segment": "high_intent",
  "model_version": "v3_2024-01-15_scheduled",
  "top_factors": [
    { "sessions_30d": 0.21 },
    { "recency_days": -0.14 }
  ]
}
```

| Status | Meaning                          |
|--------|----------------------------------|
| 200    | Score returned.                  |
| 404    | User not found in feature store. |
| 422    | Invalid request body.            |

---

## POST `/score/batch`

Batch scoring for multiple users in one call.

**Request body** (`BatchScoreRequest`)

```json
{
  "users": [
    { "user_id": "u_123" },
    { "user_id": "u_456", "features": { "recency_days": 30.0 } }
  ]
}
```

**Response** (`BatchScoreResponse`)

```json
{
  "results": [
    { "user_id": "u_123", "propensity": 0.78, "model_version": "v3_2024-01-15_scheduled" },
    { "user_id": "u_456", "propensity": 0.12, "model_version": "v3_2024-01-15_scheduled" }
  ],
  "model_version": "v3_2024-01-15_scheduled"
}
```

| Status | Meaning               |
|--------|-----------------------|
| 200    | Batch scored.         |
| 422    | Invalid request body. |

---

## GET `/model/info`

Metadata about the currently served model.

**Response** (`ModelInfo`)

```json
{
  "name": "subscription_propensity",
  "version": "v3_2024-01-15_scheduled",
  "trained_at": "2024-01-15T02:00:00Z",
  "metrics": { "auc": 0.86, "logloss": 0.31 },
  "feature_count": 47
}
```

| Status | Meaning                 |
|--------|-------------------------|
| 200    | Model metadata returned.|
| 503    | No model loaded.        |

---

> **Note:** The values above are illustrative examples only and do not
> reflect any real model, dataset, or production system.
