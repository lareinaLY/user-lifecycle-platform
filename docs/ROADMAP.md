# Roadmap

> **Status:** All five phases below are **planned** — none are implemented
> yet. Phase 1 is *next up*. The repository today is an interface skeleton
> (see [`architecture.md`](architecture.md)). This document records the
> intended sequence of milestones, not delivered work.

## Guiding principle — pipe first, fill later

Build the system as a sequence of **independently shippable milestones**.
Get the end-to-end plumbing working with a **fake model** first, then
progressively replace the fakes with real components. Each phase is
verifiable on its own, so progress never blocks on a downstream piece being
ready.

The progressive order inside the serving path is deliberate:
**A/B parameters can load → those parameters route the request to a model
(initially a fake, random-scoring model) → finally swap in the real
model.** Every step is testable in isolation.

## Phase 1 — Skeleton: prove the real-time path with a fake model

**Scope.** A/B platform (hash bucketing, parameter delivery), Kafka message
queue, client-side instrumentation, Kafka → table sink, the serving-flow
framework, and a call to a **fake** model-score endpoint.

**Acceptance.** A single request completes the full loop — *A/B bucket →
fetch parameters → serving flow → call fake model (random score) →
instrumentation → Kafka → table* — and the data is visible in the table.

**Essence.** Validate that the **plumbing connects**, not that scores are
correct (the model is intentionally fake).

**Dependencies.** None on analytics conclusions; can start immediately.

## Phase 2 — Closed training / prediction loop

**Scope.** Prediction-stream dump (dump the features used at prediction
time) + instrumentation-stream dump (exposure + conversion), join into
samples, and online model serving that **replaces the fake** model.

**Acceptance.** Prediction-time features land in **table A**;
instrumentation lands in **table B**; the two are joined into samples; a
real model is trained on those samples; model serving replaces the fake.

**Essence.** Stand up the offline training pipeline and connect it to the
real-time path (a closed loop). The training data is produced by this
pipeline itself.

**Dependencies.**
- **Feature design** ← analytics side: **persistence-type signals**
  (continuity / return behavior) as the primary signal.
- **Label definition** ← **behavioral churn = continuous silence** (already
  decided).

## Phase 3 — End-to-end shakeout + A/A and A/B

**Scope.** End-to-end integration, then an **A/A test**, then an A/B test.

**A/A test.** Two arms run the *exact same* configuration, so in theory the
metrics should show **no difference**. It validates that the experiment
system itself is bug-free — buckets are uniform and metrics are computed
correctly. Only once A/A shows **no significant difference** can A/B results
be trusted.

**Acceptance.** A/A shows no significant difference between arms → A/B then
correctly detects a real difference.

**Essence.** Prove the experiment system is trustworthy *before* using it to
run experiments.

## Phase 4 — A more complex model: value prediction

**Scope.** Upgrade from "predict whether the user pays" (**propensity**) to
"predict renewal duration / value" (**value-aware**) — i.e. the second
stage of the two-stage model.

**Mapping.** This is the existing **LTV design** (subscription-duration
tiers, two-stage) documented in [`architecture.md`](architecture.md). The
evolution is **propensity → value-aware**.

## Phase 5 — Gap-filling and finishing

**Scope.** Fill in tests, documentation, and boundary cases.

**Optional.** A feature-demo visualization that shows the system's actual
output state using **simulated data shaped to resemble a realistic
distribution** — a demo facade for the system, *not* an architecture
diagram and *not* a production operations tool.

## How this connects to existing design and the analytics side

- **Phase 2 features** ← analytics conclusions: persistence / return are
  effective signals; scenario-mix and interaction-quality features were
  tested and found to lack discriminative power.
- **Phase 2 label** ← the behavioral-churn definition (continuous silence).
- **Phase 4** ← the LTV two-stage design.
- **Phase 1 "A/B → choose model"** ← the model **Registry**.
