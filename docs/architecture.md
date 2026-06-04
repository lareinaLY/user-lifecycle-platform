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
>
> The build sequence for turning these designs into working software is in
> [Roadmap](ROADMAP.md) (five planned phases; Phase 1 is next up).

## Overview

At runtime the system is **two independent pipelines that share nothing
except the model artifact**. Describing it as a single top-to-bottom "layer
stack" is inaccurate: the real-time request path and the offline training
path run on different triggers and different latencies, and they touch each
other **only** through the model **Registry**.

> The four `src/` directories (data / models / api+events / experiments)
> are a **source-tree code map**, not the runtime data flow. The runtime
> shape is the two pipelines below. See
> [Code modules](#code-modules-src) for the source map and
> [Roadmap](ROADMAP.md) for the build order.

### Real-time serving pipeline (on a user request)

1. **A/B platform first — the most upstream entry.** The request enters the
   A/B platform, which hash-buckets the user and resolves the **A/B
   parameters** for this request. These parameters are the topmost input and
   drive the entire path — in particular *which model / which version* this
   request uses. A/B parameters are merged over the system defaults, with
   **A/B parameters taking priority** on conflict. (A/B is the upstream that
   decides how the request flows — *not* a downstream consumer of scores.)
2. **Serving flow — model scoring is one step among several.** A
   parameter-driven business flow runs. Model scoring is **a single link in
   the chain**: there are pre-/post-scoring mechanisms around it such as
   filtering and forced-insertion (business rules). The model is not the
   whole serving layer. *(A POC may stub out filtering / forced-insertion,
   but the architecture treats the model as one step, not the entirety.)*
3. **Response** is returned.

### Offline training pipeline (asynchronous; NOT on the request path)

1. At prediction time, the features that fed the prediction are **dumped**
   to a feature stream → **table A**.
2. **Exposure + conversion** instrumentation is dumped to a label stream →
   **table B**.
3. **join(table A, table B) → samples → train model → push model to the
   Registry.**

### The single connection point

The only coupling between the two pipelines is the model artifact:
*offline training produces a model → **Registry** → the real-time pipeline
loads it.* Nothing else links them directly. In particular, the model's use
of **data-layer** features happens **offline, at training time** — the
real-time path scores using the features already dumped at prediction time
and does **not** reach back into the data layer mid-request (the
model↔data relationship is offline/async, not a real-time serving
dependency).

## Code modules (`src/`)

> Source-tree responsibilities. This is a code map; for the runtime data
> flow see [Overview](#overview).

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
  scoring; loads a model version (selected by the request's A/B parameters)
  from the registry. Model scoring is **one step** of the serving flow,
  which also includes pre-/post-scoring mechanisms (filtering,
  forced-insertion); the model is not the whole flow.
- **`api/schemas.py`** — pydantic request/response contracts.
- **`events/event_producer.py`** — Kafka-compatible `EventProducer`
  interface with an in-memory mock; production backs it with a real broker.
  In the offline pipeline it carries the feature dump and the
  exposure/conversion instrumentation (see
  [Event interfaces](#event-interfaces-dual-stream-design-design)).

### Experiment layer (`src/experiments/`)
- **`ab_test.py`** — deterministic, hash-based variant assignment (stateless
  and reproducible) plus significance testing. Assignment is the **upstream
  entry** of a request: it resolves the A/B parameters that route the
  request (including which model/version to use), and those parameters take
  priority over system defaults. It is *not* a downstream consumer of
  scores.

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

### Two-stage vs a single ZILN model — design trade-off
A more advanced alternative is a single **zero-inflated lognormal (ZILN)**
model that predicts conversion and value jointly, roughly halving model
complexity versus two separate stages. We still choose two stages here,
deliberately:
- The target is **discrete value tiering**, not precise revenue
  regression, so ZILN's main advantage (a calibrated continuous amount) is
  not needed — and the two-stage approach's main weakness (treating
  conversion and value as independent) has limited impact on *tier*
  assignment.
- ZILN is typically fit with a **neural network**, which conflicts with
  this project's deliberate *"tabular data → tree models"* choice.
- Two separate tree models are **more interpretable** (clean SHAP per
  stage).

Positioning: an informed trade-off — aware of the more advanced method,
choosing the one that fits the data and objective — not a capability gap.

## Churn label design — voluntary vs involuntary (design)

Churn is not a single label. Two mechanisms with opposite remedies must be
modeled separately:
- **Voluntary churn** — engagement decays and the user chooses to stop.
  The lever is experience/value improvement.
- **Involuntary churn** — the subscription lapses because a **payment
  fails**, not because the user decided to leave. The lever is payment
  recovery and proactive pre-expiry reminders.

**Identifying involuntary churn** relies on generic payment-failure
signals — renewal-payment failure, billing retries, and grace-period
states surfaced by billing webhooks (described generically; no concrete
status values or vendor terms appear here).

**Design principle.** The two churn types must carry **separate labels and
separate interventions**. Folding involuntary (payment-failed) users into a
voluntary-churn label pollutes the "why did they leave" signal and
mis-trains the model — a user whose card simply expired is not a
dissatisfied user.

*Not implemented; no churn model exists in the skeleton yet.*

## Output design — user health score (design)

A churn model's raw output is a probability, which is hard for operations
teams to act on directly. The design wraps it into a **user health score**
on a 0–100 scale that integrates multiple signals — engagement
persistence, breadth of scenarios used, and investment/usage trend — into
one interpretable number. Scores below a threshold trigger **tiered
intervention**.

This mirrors the **HubSpot Customer Health Score** pattern: a single,
operations-friendly indicator rather than a bare model probability.

*Design only; no health-score logic exists yet.*

## Feature correctness I — point-in-time correctness (design)

Scoring happens **before** conversion, so a correct training sample must
pair *features as they were known at prediction time* with a *label
observed strictly after that point*. Using features as of the conversion
moment leaks future information — the failure mode the industry calls a
violation of **point-in-time correctness** (a.k.a. *time-travel* or an
*"as-of" join*).

**Why it matters.** Feature leakage inflates offline metrics while the
model collapses in production, because the leaked signal is not available
at serving time. Published industry write-ups on point-in-time correctness
report offline-vs-online gaps on the order of **5–20 percentage points**
from this class of leakage — large enough to invalidate a launch decision.
(Figure cited from external industry sources, not from this project's data.)

**Chosen approach — log features at prediction time.** Rather than
reconstruct history after the fact, the system **dumps the exact features
that fed each prediction, at the moment of prediction**, to the feature
stream → table A. Because what is stored *is* "the features as of the
prediction instant," it is point-in-time-correct **by construction** — it
cannot contain future information. This is *prediction-time feature
logging*, the technique production ranking systems use to guarantee
correctness without a separate time-travel join.

**Bonus — this also closes training/serving skew.** Because the training
features are the *same* values dumped at serving time, the model trains on
exactly what serving produced. A single mechanism therefore solves **both**
point-in-time correctness *and* training/serving skew (see
[Feature correctness II](#feature-correctness-ii--trainingserving-consistency-design)).

**Alternative — as-of recompute (for historical backfill).** Where no
prediction-time log exists yet, features can instead be reconstructed by an
**as-of recompute** over timestamped raw events
(`event_timestamp <= sample_timestamp`) — the approach used by feature
platforms such as Airbnb's Zipline and Hopsworks, mirrored by Feast's
`get_historical_features` (training) vs `get_online_features` (serving). The
prediction-time dump is preferred when available: no recompute, and
skew-free.

The current `FeaturePipeline` exposes a `reference_date` cutoff in its
config (the leakage-safe intent), but the prediction-time dump and the
join-to-samples machinery are **not yet built**.

## Feature correctness II — training/serving consistency (design)

Point-in-time correctness prevents leakage *within* the training set; it
does not by itself guarantee that training and serving compute features
the same way. If batch training and real-time scoring build features
through **different code paths**, the two definitions drift apart — a
**training/serving skew** that shifts the serving feature distribution away
from what the model learned, degrading performance even when no single
feature leaks.

**Design principle.** Batch training and real-time scoring **share one
feature-transform definition behind a single interface** — the same
transformation code produces both the training matrix and the online
feature vector. No parallel re-implementation of "the same" feature.

Together these are the two feature-correctness guarantees the design
commits to:
- **Point-in-time correctness** — no feature observed after its label
  (prevents leakage).
- **Training/serving consistency** — one shared transform for both paths
  (prevents skew).

## Event interfaces: dual-stream design (design)

Two streams feed the offline training pipeline, separating features from
labels; both are Kafka topics that land in tables:

- **Feature stream → table A** — at prediction time, dump the exact
  features that fed the prediction (see
  [Feature correctness I](#feature-correctness-i--point-in-time-correctness-design)).
- **Label stream → table B** — labels are emitted as **two distinct
  instrumentation events**:
  - **Exposure event** — fired when the user is *shown* the paid anchor.
  - **Conversion event** — fired if the user then pays / clicks.
  - **Why two events:** the exposure event defines the **negative-sample
    boundary**. Only users who were *exposed but did not convert* count as
    negatives; users who were *never exposed* are excluded from the sample
    set. This keeps false negatives out of training — a user who never saw
    the offer is not a genuine "did not convert."
- **Join** — table A and table B are joined by **user + point in time**
  into the training samples, which feed batch (or streaming) training.

Interfaces are designed to map directly onto a real Kafka deployment. The
current code ships a **single-stream**, in-memory `MockEventProducer`
(`send` / `flush`); the dual-stream split, the exposure/conversion labels,
and the join are **design, not implemented**. Per the dependency-inversion
principle, swapping the mock for a real broker leaves callers unchanged.

## Batch-first, streaming-ready (design)

**Current main path — batch training.** Subscription conversion is a
day-scale decision, not a second-scale interest shift, so batch training is
more than sufficient on timeliness while staying cost-efficient and
maintainable. The flow is the offline pipeline from the
[Overview](#overview): prediction-time feature dump → table A,
exposure/conversion instrumentation → table B, join → samples → batch
training → model pushed to the Registry. Established users are scored in a
daily batch; brand-new users are scored in real time on the registration
event.

**Extension path — streaming training (reserved, not built).** Separating
the feature and label streams already positions the system for streaming
training: if near-real-time updates are ever required, the joined sample
stream can feed a streaming trainer **without re-architecting the data
path** — the same two streams and the same join, consumed continuously
rather than in a daily batch.

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

## Intervention optimization layer — uplift modeling (extension)

> **Status: reserved design direction — not implemented.** This layer is
> absent from the skeleton; it records where the architecture is headed.

The prediction layer (churn / LTV) answers *who* will churn or *who* is
high-value. It does **not** answer *whom to treat*: spending retention
budget on a user who would have stayed anyway is wasted, and some users
react **negatively** to intervention. That question belongs to an
**intervention optimization layer** built on **uplift modeling**, which
estimates the *incremental* effect of an intervention per user:

- **Persuadables** — stay only if treated. *The only segment worth
  spending on.*
- **Sure Things** — stay regardless; treating them wastes budget.
- **Lost Causes** — churn regardless; treating them wastes budget.
- **Sleeping Dogs** — treatment *causes* them to churn; must not be treated.

**Hard constraint — needs experimental data.** Uplift models must be
trained on **randomized controlled (A/B) data**, because an incremental
effect is only identifiable from a treated-vs-control comparison. This
closes the loop with this project's **experiment layer**: A/B tests are not
only for validating a strategy — their assignment/outcome data is the
training set for uplift.

**Tooling.** This would build on **Uber's CausalML** rather than
implementing uplift estimators from scratch.

Design philosophy: *the endpoint of prediction is a decision; decisions
should be judged on incremental effect; incremental effect comes from
causal experiments.*

## Key design decisions

1. **Interface-first, implementation-swappable.** Storage, registry, and
   event bus are abstract; local implementations support development and the
   same interfaces back production services. Concretely, the interfaces are
   aligned to production standards — the feature-store interface to the
   **Feast** API (planned `LocalFeatureStore`) and the model registry to
   **MLflow** (`LocalModelRegistry`) — so a POC-local backend can be swapped
   for the production system without changing callers.
2. **Leakage-safe features by construction.** The feature pipeline enforces a
   reference-time cutoff so training and serving see consistent, non-leaking
   features.
3. **Baseline alongside the primary model.** A logistic baseline quantifies
   the incremental value of the GBM and guards against pipeline regressions.
4. **Explainability as a first-class output.** SHAP contributions are part of
   the scoring response to support targeted lifecycle interventions.
5. **Progressive build — pipe first, fill later.** The real-time path is
   brought up end-to-end with a **fake (random-scoring) model** before any
   real model exists: *A/B parameters load → those parameters route to a
   model (fake at first) → swap in the real model last.* Each step is
   independently testable, so no milestone blocks on a downstream piece. The
   phased milestones are in [Roadmap](ROADMAP.md).

## Data privacy

This repository contains **code only**. No real datasets, credentials, user
identifiers, or analytical conclusions are included. All data directories are
git-ignored and credentials are read from environment variables.
