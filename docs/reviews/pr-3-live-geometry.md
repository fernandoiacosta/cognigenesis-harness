# PR #3 review: live topology dashboard

Reviewed original head `2120f050b1ed0e4d96f97ba5dbbbddd3b888eecf` against base `b2efecfdc98a79f7e12c9594420802151aed79f9`. Changes belong only to `feature/live-geometry-dashboard`; no merge into main.

## Confirmed defects and fixes

- **Missing cognitive relationships:** CognitiveLedger stores membership on `Hypothesis.evidence_ids`, not on Evidence. Project those actual references with supports, contradicts or neutral polarity. Do not manufacture a supporting link from unrelated claim fields.
- **Identity and label corruption:** Removing ID truncation prevents distinct IDs sharing a 160-character prefix from collapsing. Dependency references no longer overwrite recorded task titles. Entries without runtime IDs are ignored rather than assigned invented identities.
- **Unbounded aggregate display cost:** Per-collection limits previously permitted tens of thousands of nodes and quadratic repulsion every animation frame. Cap output at 2,000 nodes and 4,000 links, report truncation visibly, and sample at most 32 pair interactions per node per frame, rotating samples deterministically. This is an approximate structural layout, not a measured physical system. Stop after 300 frames until graph content changes or the viewport resizes; pause work and polling while hidden. Identical snapshots preserve positions without restarting simulation.
- **Malformed collection handling:** Ignore invalid collection types and non-string references instead of failing the topology request or splitting strings into invented dependencies.
- **Browser defense in depth:** Replace script `unsafe-inline` with hashes of the actual static scripts, disallow framing, and reject requests marked cross-site by Fetch Metadata. Existing loopback bind and Host checks remain enforced. These harden the unauthenticated local reader; no exploit through the original text/canvas label rendering was found.

## Mapping and trust boundaries

TaskGraph dependencies and assignments reference runtime IDs; TeamManager snapshots emit agent lists with matching IDs. CognitiveLedger evidence links can refer to multiple hypotheses and retain polarity. Runtime event sources are distinct source nodes; the generic runtime source is excluded. Only graph fields are returned: descriptions, results, model endpoints, capabilities and event payloads are excluded. Labels and source names remain user-provided content and could contain sensitive text; this is not a general secret redactor. Browser labels use canvas/textContent, never HTML interpolation.

The server remains a read-only, unauthenticated loopback service. CSP, lack of CORS, Host checks and Fetch Metadata are browser defenses, not authentication against other local processes. Shared-machine or remote access requires an authenticated gateway. Arbitrarily large persisted files still impose read/JSON parsing cost before graph caps apply; future ingestion limits and snapshot caching should address this separately.

All three changed files were inspected along with snapshot producers, ledger, task graph, team fabric and store. A formal Security Diff Scan could not run because its mandatory config-preflight skill resource was unavailable; this is a manual security review.

## Validation

Baseline targeted tests: 4 passed. Updated Python suite: **100 passed, 1 skipped** (the live Ollama integration requires a running local model). Added tests use real producer snapshots, mixed evidence polarity, long IDs, malformed collections, aggregate caps, actual HTTP boundary checks, metadata omission and exact CSP hashes.

Chromium headless with software rendering: CSP permits intended scripts, hostile labels remain text, newly saved entities appear through polling, viewports resize at 375px and 1440px, Host/cross-site checks return 403, and no page JavaScript errors occur. Reproduce with `python scripts/check_geometry_browser.py` after installing Playwright and Chromium; the script requires `/usr/bin/chromium` and the original PR commit in local Git history.

A synthetic chain graph measured synchronous layout plus Canvas command submission over 30 frames after 5 warmup frames. This excludes compositor/raster/GPU completion and is not an end-to-end FPS claim.

| Nodes | Original median / p95 ms | Revised median / p95 ms |
| --- | --- | --- |
| 100 | 0.1 / 2.3 | 0.1 / 1.2 |
| 1,000 | 5.9 / 12.1 | 1.3 / 4.8 |
| 2,000 | 25.1 / 30.1 | 2.4 / 4.7 |

A repeat run with the persisted smoke script measured 27.0 → 1.8ms median at 2,000 nodes (42.6 → 4.2ms p95). Smaller-case p95 results varied under shared-runner load; benchmark results are illustrative, not a release performance guarantee. The smoke script also verifies that identical snapshots leave a stopped simulation idle and resizing restarts it.

## Proposed WebGL work

1. Separate topology ingestion, layout and drawing. Move layout to a worker using typed position arrays and Barnes–Hut or a spatial grid. WebGL drawing alone does not fix CPU layout complexity. Preserve stable ID-to-index mapping and pin old positions across deltas.
2. Add an optional WebGL2 renderer with instanced node glyphs, batched line vertices and reusable buffers; update changed ranges rather than rebuilding every frame. Keep Canvas fallback and handle context loss/restoration. Retain DOM text for counts, status and accessible selection details.
3. Cull offscreen entities, render labels only for selections/zoomed views, and introduce aggregation or explicit level of detail above the current cap. Show omitted counts before raising limits.
4. Benchmark 100/1,000/10,000-node sparse and dense graphs on desktop and mobile. Capture layout time, command submission, long tasks, dropped frames, buffer bytes and polling payload size. Set a 16.7ms p95 end-to-end frame budget for 60Hz targets. Use disjoint timer queries only when supported; report CPU and GPU timing separately.

## Proposed real-time telemetry work

1. Define versioned measured records with workspace/run/entity IDs, monotonic sequence, wall timestamp, units, sampling interval and provenance. Include observed duration, queue depth, tokens and tool failures only when runtime instrumentation emits them. Never derive agent activity from layout motion.
2. Add loopback-protected Server-Sent Events for one-way streaming, with heartbeat, bounded client queues, Last-Event-ID replay and full snapshot recovery after a sequence gap. Coalesce updates and batch UI ingestion once per animation frame. Keep polling as a fallback with timeout, backoff and visible stale age.
3. Keep metric collection off request and inference paths. Optional GPU collectors can use NVML or supported vendor interfaces with explicit device/run attribution. Expose sampled utilization, allocated/reserved memory and collector health; unavailable data stays unavailable. Browser WebGL availability is not evidence of inference GPU usage.
4. Bound retention and enforce a telemetry field allowlist. Exclude prompts, credentials, full tool arguments and private endpoints. Test disconnects, slow consumers, event floods, missing collectors and schema changes.
5. Treat any state-space projection as a separately named measured analysis: document selected signals, normalization, window, missing-data handling and uncertainty. The current graph shows recorded structural relationships only.
