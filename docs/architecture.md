# Architecture

> **Status:** Initial draft. Full architecture design to be completed
> (`待补充完整架构设计`). This document captures the high-level design that
> the current code skeleton is built around.
>
> **Implementation status:** The repository currently ships an **interface
> skeleton** — modules define typed contracts (dataclasses, abstract base
> classes, signatures, docstrings), but method bodies are not yet
> implemented. Sections below are tagged to distinguish what exists from
> what is planned:
> - **(implemented)** — code that runs today.
> - **(design)** — a decided design not yet built.
> - **(extension)** — a reserved direction, intentionally out of scope for now.

## Overview

The platform is organized into four loosely coupled layers. Each layer
depends only on the abstract interfaces of the layer below it, which keeps
components independently testable and lets backing implementations
(storage, registry, event bus) be swapped between local development and
production without touching upstream code.

```
┌─────────────────────────────────────────────────────────────┐
│  Experiment Layer   src/experiments/                          │
│  A/B assignment (hash-based) · significance testing           │
└───────────────▲─────────────────────────────────────────────┘
                │ consumes scores
┌───────────────┴─────────────────────────────────────────────┐
│  Serving Layer      src/api/  ·  src/events/                  │
│  FastAPI scoring (real-time + batch) · event production       │
└───────────────▲─────────────────────────────────────────────┘
                │ loads model versions
┌───────────────┴─────────────────────────────────────────────┐
│  Model Layer        src/models/                               │
│  LightGBM propensity · LR baseline · model registry           │
└───────────────▲─────────────────────────────────────────────┘
                │ consumes feature matrices
┌───────────────┴─────────────────────────────────────────────┐
│  Data Layer         src/data/                                 │
│  Parquet loaders (storage-agnostic) · feature pipeline        │
└─────────────────────────────────────────────────────────────┘
```

## Layers

### Data layer (`src/data/`)
- **`data_loader.py`** — `DataLoader` abstraction over the physical storage
  format. `ParquetDataLoader` reads from a configurable root and supports
  predicate pushdown and batched, out-of-core reads. Connection/location
  details come from environment variables; no data lives in the repo.
- **`feature_pipeline.py`** — composable feature groups (RFM, engagement,
  session). All transforms are leakage-safe: features use only events
  observable strictly before the prediction reference time.

### Model layer (`src/models/`)
- **`propensity_model.py`** — primary LightGBM model with SHAP-based
  per-prediction explanations and global feature importance. *(design;
  interface defined, training/scoring logic pending.)*
- **`baseline.py`** — logistic regression baseline sharing the same
  `fit` / `predict_proba` interface for apples-to-apples comparison.
  *(design; interface defined.)*
- **`registry.py`** — MLflow-compatible `ModelRegistry` interface and a
  local filesystem implementation (`LocalModelRegistry`). Production can
  swap in an MLflow tracking server transparently. *(design; interface
  defined.)*

The prediction target itself follows a two-stage design — see
[Prediction target](#prediction-target-design) below.

### Serving layer (`src/api/`, `src/events/`)
- **`api/scoring_service.py`** — FastAPI app exposing real-time and batch
  scoring; loads a model version from the registry at startup.
- **`api/schemas.py`** — pydantic request/response contracts.
- **`events/event_producer.py`** — Kafka-compatible `EventProducer`
  interface with an in-memory mock; production backs it with a real broker.

### Experiment layer (`src/experiments/`)
- **`ab_test.py`** — deterministic, hash-based variant assignment (stateless
  and reproducible) plus two-proportion significance testing.

## Prediction target (design)

The modeling target evolves in two stages. Stage 1 is the baseline that
gets the end-to-end pipeline working; stage 2 enriches it once the
pipeline is proven. **Neither stage is implemented yet — this records the
intended target definition.**

### Stage 1 — Propensity (baseline)
- **Binary classification:** will the user convert to *valid* paid usage?
- The label is deliberately simple and reliable, which makes it a clean
  signal for validating the full data → feature → model → scoring loop.

### Stage 2 — Value-aware tiering (extension)
- **Multi-class classification:** predict a user's long-term value tier.
- The value signal is **subscription duration**, not cumulative spend.
  Duration sidesteps multi-currency conversion entirely and, because
  renewals extend the subscription, it naturally encodes renewal depth.
- **Tier concept** (no thresholds specified here; thresholds are a tuning
  concern, not an architectural one): non-paying / short-term /
  mid-term / long-term high-value.
- **Primary objective:** identify long-term high-value users — the core
  user profile that lifecycle interventions should protect and grow.

### Why subscription duration — design trade-off record
Documented for rigor; contains no business figures:
- **Not order count** — the renewal mechanism updates the existing order
  rather than appending new order rows, so order count carries little
  discriminative signal for renewal depth.
- **Not a renewal-count field** — such a field is unreliable in practice
  (substantial missingness), so it is unsafe as a label driver.
- **Not cumulative amount** — multi-currency conversion introduces error,
  and precise revenue is unnecessary for a tiering objective.
- **Subscription duration** — a single field that cleanly encodes renewal
  depth, independent of currency conversion and of any (possibly missing)
  renewal counter.

## Point-in-time features & leakage avoidance (design)

Scoring happens **before** conversion. A correct training sample must
therefore pair *features as they were known at a given point in time*
with a *label observed strictly after that point*. Using features as of
the conversion moment would leak future information into the model.

**Designed approach:**
- A training sample = a **feature snapshot at a historical point in time**
  + the conversion label observed in a window *after* that timestamp.
- The feature pipeline emits **timestamped feature snapshots** so the
  feature state at any point in time can be reproduced.
- Hard rule: when constructing a training sample, the feature timestamp
  must precede the label observation window.

This adopts the feature/label point-in-time alignment practice common in
production recommendation and ad-ranking systems. The current
`FeaturePipeline` exposes a `reference_date` cutoff in its config (the
leakage-safe intent), but the snapshot machinery itself is **not yet
built**.

## Event interfaces: dual-stream design (design)

The event interface upgrades from a single producer stream to a
**two-stream** design that separates features from labels:

- **Feature stream** — at scoring-request time, persist the feature
  snapshot as of that moment.
- **Label stream** — when a conversion event (payment instrumentation)
  fires, persist the label.
- **Join** — the two streams are aligned by **user + point in time** into
  a single training-sample stream.

Interfaces are designed to map directly onto a real Kafka deployment. The
current code ships a **single-stream**, in-memory `MockEventProducer`
(`send` / `flush`); the dual-stream split and the join are **design, not
implemented**. Per the dependency-inversion principle, swapping the mock
for a real broker leaves callers unchanged.

## Batch-first, streaming-ready (design)

**Current main path — batch training.** Subscription conversion is a
day-scale decision, not a second-scale interest shift, so batch training
is more than sufficient on timeliness while staying cost-efficient and
maintainable. Established users are scored in a daily batch; brand-new
users are scored in real time on the registration event.

```
Batch main path (design)
┌────────────┐   daily   ┌──────────────┐   ┌───────────┐   ┌───────────┐
│ raw events │ ───────▶  │ feature      │ ▶ │ batch     │ ▶ │ model     │
│ (parquet)  │  refresh  │ snapshots    │   │ training  │   │ registry  │
└────────────┘           └──────────────┘   └───────────┘   └─────┬─────┘
                                                                   │
   established users → daily batch scoring  ◀──────────────────────┤
   new users (<48h)  → real-time scoring on registration event ◀───┘
```

**Extension path — streaming training (reserved, not built).** The
separation of feature and label streams already positions the system for
streaming training. If near-real-time updates are ever required, the
sample stream can feed a streaming trainer **without re-architecting the
data path**.

```
Streaming extension (reserved)
┌──────────────┐     ┌──────────────┐
│ feature      │     │ label        │
│ stream       │     │ stream       │
└──────┬───────┘     └──────┬───────┘
       └────── join (user + point in time) ──────┐
                                                  ▼
                                       ┌────────────────────┐
                                       │ streaming training  │
                                       │ / online update     │
                                       └────────────────────┘
```

## Training strategy (design)

Not implemented; records the intended training-time decisions.

- **Full-population training set** — include all users, low-activity ones
  included, to keep the training distribution complete and negatives
  fresh, avoiding covariate shift between training and serving.
- **Tiered feature refresh** — refresh features daily for high-activity
  and new users; weekly for low-activity users (their behavior changes
  slowly and the information gain is low, which lowers compute cost).
- **Trigger-based refresh** — when a significant drift in the population's
  behavioral distribution is detected, trigger feature refresh and
  retraining (event-driven, rather than a fixed timer).
- **Class imbalance** — paid users are the minority class; handle it
  explicitly via negative-sample downsampling of the majority
  (low-activity non-payers) and/or LightGBM `scale_pos_weight`.

## Key design decisions

1. **Interface-first, implementation-swappable.** Storage, registry, and
   event bus are abstract; local implementations support development and the
   same interfaces back production services.
2. **Leakage-safe features by construction.** The feature pipeline enforces a
   reference-time cutoff so training and serving see consistent, non-leaking
   features.
3. **Baseline alongside the primary model.** A logistic baseline quantifies
   the incremental value of the GBM and guards against pipeline regressions.
4. **Explainability as a first-class output.** SHAP contributions are part of
   the scoring response to support targeted lifecycle interventions.

## Data privacy

This repository contains **code only**. No real datasets, credentials, user
identifiers, or analytical conclusions are included. All data directories are
git-ignored and credentials are read from environment variables.
