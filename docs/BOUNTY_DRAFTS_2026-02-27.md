# Bounty Drafts (Reduced by 25%)

## 1) [BOUNTY] Epoch Determinism Simulator + Cross-Node Replay (113 RTC)

**Reward:** 113 RTC (reduced 25%)  
**Category:** Consensus hardening / settlement reliability

### Objective
Build a deterministic replay harness that proves epoch settlement outputs are identical across nodes for identical inputs.

### Why this matters
If two nodes process the same epoch input and produce different reward allocations, we can get settlement drift, trust loss, and payout disputes.

### Scope
- Build a replay tool that accepts an epoch fixture input (attestations/enrollments/multipliers/config).
- Run replay against at least 2 node environments (or 2 deterministic code-path runs).
- Compare outputs and produce a human-readable + machine-readable diff report.
- Include a CI-friendly mode for regression checking.

### Deliverables
1. Replay CLI/tooling with documented usage.
2. Fixture format spec + at least 3 fixtures:
   - normal epoch
   - sparse epoch
   - edge-case epoch (boundary timing / missing fallback data)
3. Determinism report output (JSON + markdown summary).
4. Tests for mismatch detection and deterministic pass.
5. README with reproduction steps.

### Acceptance Criteria
- Same fixture replayed across both targets yields byte-equivalent normalized payout output.
- Tool exits non-zero on mismatch and prints per-miner diff.
- Handles `epoch_enroll` primary path and `miner_attest_recent` fallback path.
- Includes at least one intentionally-divergent fixture test proving mismatch detection works.
- Works in a clean checkout with documented one-command run.

### Anti-Farming Guardrails
- No docs-only submission accepted.
- Must include executable replay code + passing tests.
- Must include real diff artifact examples.

### Submission Format
- PR link
- Sample replay command(s)
- Determinism output snippet
- Wallet/miner ID for payout

### Payout
- 40% on accepted deterministic replay framework
- 60% on full fixture/test suite + CI-ready validation

---

## 2) [BOUNTY] Attestation Fuzz Harness + Crash Regression Corpus (98 RTC)

**Reward:** 98 RTC (reduced 25%)  
**Category:** API hardening / red-team

### Objective
Create a fuzz/property-based test harness for attestation ingestion and validation, with a reusable regression corpus for known and newly discovered crash classes.

### Why this matters
Attestation parsing is externally exposed and high-risk. We need to prevent unhandled exceptions, parser edge-case bypasses, and DoS-class malformed payloads.

### Scope
- Target attestation-related request parsing/validation paths.
- Generate malformed and adversarial payloads (type confusion, missing fields, nested structures, oversized values, boundary timestamps, boolean/dict shape mismatch, etc.).
- Capture and persist crashing/minimizing inputs into a regression corpus.
- Add CI-mode test gate for "no unhandled exceptions".

### Deliverables
1. Fuzz harness (property-based and/or mutation-based).
2. Regression corpus directory with repro inputs.
3. Reproducer script for each corpus entry.
4. Test suite integrated with existing test runner.
5. Report summarizing findings and fixed/known behavior.

### Acceptance Criteria
- Harness executes at least 10,000 generated cases in one run mode.
- No unhandled server exceptions in target paths.
- At least 5 distinct malformed input classes are covered by explicit tests.
- Regression corpus entries are replayable and deterministic.
- CI command documented and returns non-zero on regression.

### Anti-Farming Guardrails
- Must include runnable code, not only issue commentary.
- Synthetic "found nothing" without harness artifacts is not accepted.
- Duplicate previously-reported payloads without added coverage are partial credit only.

### Submission Format
- PR link
- Fuzz command and run stats
- Corpus summary (count + classes)
- Wallet/miner ID for payout

### Payout
- 30% after harness + first passing run
- 70% after corpus + CI integration + maintainer verification

---

## 3) [BOUNTY] Sybil/Farming Risk Scorer for Bounty Claims (83 RTC)

**Reward:** 83 RTC (reduced 25%)  
**Category:** Program integrity / anti-abuse automation

### Objective
Implement an explainable risk-scoring module that flags likely bounty farming/Sybil behavior in claim triage.

### Why this matters
Bounty farming reduces real signal and wastes reviewer time. We need automated ranking to prioritize suspicious claim patterns for manual review.

### Scope
- Extend existing claim triage flow with risk scoring.
- Compute a per-claim score and reason codes based on measurable features.
- Produce a sortable report with `low/medium/high` risk buckets.

### Minimum Feature Set
- Account age heuristic.
- Claim velocity heuristic (burst behavior).
- Text similarity/template reuse heuristic.
- Wallet/repo cross-pattern heuristic.
- Duplicate proof-link heuristic.
- Optional: timezone/posting cadence anomaly signal.

### Deliverables
1. Scoring module integrated into claim triage script/workflow.
2. Configurable thresholds via constants/config file.
3. Triage report output with reason codes per flagged claim.
4. Unit tests with synthetic samples.
5. README section describing scoring logic and limitations.

### Acceptance Criteria
- Score output includes numeric score + reason list per claim.
- Generates top-N suspicious claims sorted descending.
- Includes at least 8 test fixtures across benign + suspicious patterns.
- No hard-fail when a feature is unavailable (graceful degradation).
- Backward compatible with existing claim triage workflow.

### Anti-Farming Guardrails
- Black-box "AI says suspicious" is not accepted.
- Must be explainable and reproducible from claim metadata.
- Must avoid auto-ban behavior; this is triage assist only.

### Submission Format
- PR link
- Sample triage output
- List of reason codes implemented
- Wallet/miner ID for payout

### Payout
- 40% on scoring engine + tests
- 60% on workflow integration + usable report output
