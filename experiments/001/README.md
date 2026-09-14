# Experiment 001 — Evidence-disciplined decisions

Status: **PRE-REGISTERED / NOT YET RUN**

Author and provenance: Cognigenesis and Cognigenesis Prime are Fernando Acosta's work. This experiment evaluates one bounded, observable effect of the existing Cognigenesis control plane; it does not disclose proprietary internal mechanisms.

## Frozen claim

With the same Ollama model, sampling settings, user tasks, and output schema, the current Cognigenesis control plane will improve evidence-disciplined decision performance by **at least 15 percentage points** over a minimal helpful-assistant baseline on this fixed corpus.

This is intentionally narrower than “Cognigenesis is better.” It tests whether the existing control plane improves decisions when evidence is incomplete, contradictory, or insufficient.

## Conditions

- **Baseline:** `You are a helpful assistant.`
- **Treatment:** the repository's current `cognigenesis/resources/agent.md`
- Both conditions receive the same evaluation instruction and case text.
- Same local Ollama endpoint, exact model identifier, temperature, token limit, and run seeds.
- No tools, retrieval, conversation history, or human repair during a run.
- Default: 8 cases × 3 seeded runs × 2 conditions = 48 responses.

## Primary metric

Mean deterministic score from `score.py` across all completed responses.

Each response can earn 100 points:

- 10: valid JSON object
- 25: correct decision
- 20: required evidence IDs cited
- 15: required uncertainty/contradiction flags present
- 15: confidence does not exceed the case ceiling
- 15: proposed next test contains the case's required discriminating concepts

Primary outcome:

- **WIN:** treatment minus baseline >= 15.0 points
- **TIE:** difference is between -5.0 and +15.0 points
- **LOSS:** treatment minus baseline < -5.0 points

The thresholds, corpus, and scorer must not be changed after inspecting model outputs. Any revised experiment gets a new numbered directory.

## Secondary diagnostics

Report JSON validity, decision accuracy, evidence coverage, uncertainty coverage, calibration, and test quality separately. Latency and failures are recorded but are not part of the primary score.

## Falsifiers and limitations

The claim fails if the treatment misses the win threshold. A win supports only this model/configuration/corpus/control-plane combination. It does not establish universal superiority, causation for every runtime component, or the effect of the full architecture.

Known threats: task leakage, benchmark overfitting, format sensitivity, stochastic variance, and a baseline that may already exhibit the target behavior. Replication should add a held-out corpus and blinded external cases without changing this result.

## Run

From the repository root on Windows, the launcher selects the preferred installed model and runs plus scores the full experiment:

```powershell
.\\experiments\\001\\run.ps1
```

Or select an exact model manually:

```powershell
python experiments/001/run.py --model llama3.1:8b --runs 3
```

Optional endpoint/settings:

```powershell
python experiments/001/run.py --model <exact-model> --base-url http://127.0.0.1:11434 --temperature 0.2 --runs 3
```

The runner writes a manifest containing the Git commit when available, dataset SHA-256, exact systems/prompts, model, seeds, timestamps, latency, raw responses, and errors.

## Integrity rule

Commit this directory before the first run. Preserve failed responses. Never edit raw artifacts. If a defect makes the experiment invalid, label it invalid and create `experiments/002` rather than silently repairing Experiment 001.
