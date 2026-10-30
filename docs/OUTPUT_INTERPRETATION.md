# Cognigenesis: native-output interpretation (alpha)

The harness now **observes** model answers instead of requiring one schema for every task. `cognigenesis.runtime.output_interpreter.interpret_output` accepts:

- JSON dictionaries and fenced or embedded JSON answers;
- direct text decisions such as `No, ...` or explicit `Decision: defer`;
- explicit evidence IDs, confidence labels, stated uncertainties, and next-test lines.

The original answer is returned and persisted *unchanged*. A separate `output.interpreted` event records a redacted metadata summary with a SHA-256 fingerprint. No raw answer prose is inserted into this extra event. The engine exposes `last_interpretation` for authorized callers.

**Safety constraints**

- Missing confidence remains unknown, never invented or clamped to a fabricated score.
- Conflicting explicit decisions are marked ambiguous.
- Detection is a best-effort parsing aid, **not an independent assessment of reasoning correctness**.
- Model prose cannot become a tool call, execute code, override policy, or approve actions through this layer.
- The context compiler, tool schemas, model control-plane instructions, and frozen Experiment 001 runner/scorer are not changed.
- Neither a parser nor a bigger model demonstrates a causal cognition improvement on its own.

**Tests**

`python -m pytest tests/test_output_interpreter.py -q`

**Evaluation**

To inspect saved raw responses without editing Experiment 001:

`python experiments/001/inspect_outputs.py experiments/001/results/<run-directory>`

This produces `output_interpretation.json` beside the unchanged `report.json`. Diagnostic decision matching uses the original case labels, which may be overly restrictive or ambiguous; it must not be described as reasoning accuracy.

**Model choice**

The separate Gemma 4 E2B CI run uses only the explicit model `gemma4:e2b` and preserves its model digest, seeds, prompt versions, raw responses and frozen grades. Do not silently select other providers or substitute another model for a failed download.
