# Cognigenesis Compare — MVP decision, 2026-10-30
**Owner: Fernando Acosta. Status: tested CLI prototype + product plan, NOT a deployed web application.**

## Product proposition
**Ask once. Compare three ways of thinking. See what improves, what does not, and why.**

Run the SAME approved foundation model and SAME question under:
A. regular base instruction;
B. A + ACOSTA V3 reasoning guidance;
C. B + Cognigenesis V6 reasoning guidance.
Future D: harness with CognitiveLedger, TaskGraph and Agent Fabric, explicitly a separate tool-enabled test.

The runner currently uses SHORT **operationalized excerpts** rather than verbatim historical protocol instructions. Do not claim exhaustive implementation until the complete author-reviewed profile modules and checks are added. This product does NOT retrain a model.

## MVP user experience
One prompt field, explicit model selection, Compare button, three FULL raw answer cards. Blind review mode should hide arm identities until the person votes. Show evidence/citations (verified or unverified), assumptions, uncertainty, actionability, missing requirements, latency, input/output tokens and cost; do not produce invented IQ scores. One-click export of a run and independent review. JSON is a transport only, not a replacement for reasoning. Any parse failure is disclosed without discarding the answer.

## What exists and what is missing
| Asset | Exists | Gaps/priority |
|--|--|--|
| ACOSTA 3 | Public historical source, neuromorphic software correction | Versioned modular profile, fidelity signoff, licensing (P0) |
| Cognigenesis v6 | Public research source | Verifiable mechanism-to-output map, profile fidelity and ablation tests (P0) |
| Harness | Ollama/ACP, cognitive ledger, task graph, event bus, multiple providers, output interpreter | Stable compare endpoint, auth, per-user isolation, rate limits, safety boundaries, production monitoring (P1) |
| Experiment 001 | Qwen LOSS and Gemma E2B TIE; both heavily JSON/format-sensitive | Separate format from factual reasoning; stronger adjudication and balanced tasks (P0) |
| CritPt pilot | Public one-task Gemma physics runner, draft PR #5 | Not official AA leaderboard, no correctness verifier yet; freeze/evaluate pilot (P1) |
| JajaLabs | Live marketing site, product links | Landing still sells prompt optimization, many competing CTAs and Stan checkout; converge to Compare, verify payments (P0) |
| Custom GPTs / Gemini Gems | Historical user-facing assistants | Migrate instructions, attachments, actions, access; test equivalent plugin/skill before retirements (P0) |
| Google Drive + social posts + Stax | Historical evidence/provenance | Organized evidence registry with timestamps, dataset versions, source URLs (P1) |
| Customer proof | No reliable cohort/retention/pricing data reviewed | 10 invited people, 30 blinded comparisons, repeat-use and payment intent (P0) |
| IP/privacy | Protected repositories and reserved licensing | Evaluation terms, data handling, consent, access controls, API terms (P0) |

## Local web preview (implemented on this branch)
```bash
ollama pull gemma4:e2b
python experiments/compare/server.py
# Visit http://127.0.0.1:8787
```
One page, three visible answer cards, matched model configuration, and unique local JSON records. No cloud hosting or public access. This is a runnable *local* prototype, not a hardened internet service. Do not port-forward it or tunnel it onto the public internet without adding authentication and access controls. The UI currently displays latency and output tokens; independent accuracy scoring and blinded voting are not yet implemented.

## Engineering rules
- NO silent model switching, no assumption custom GPTs/Gems have an authorized callable API.
- Version, pin and hash prompts, profiles, model digest, configs, model output, timestamps and costs.
- Match task, model, temperature, seed, token limit, source retrieval, structured response contract, and tool budget across A/B/C. Track prompt overhead as a cost.
- Keep the complete raw answer. A postprocessor may extract structured facts, but missing fields stay unknown. No text-derived tool authority.
- Compare task accuracy and user preference independently. Blind ratings must be collected before revealing A/B/C.
- A failed model arm stays a failed arm. No synthetic success, no substituting models.
- Historical Qwen results remain archived; new public product runs can default to author-approved Gemma, never force previously excluded models.

## Technical CLI prototype
```bash
python experiments/compare/compare.py --model gemma4:e2b --prompt "How should I validate my new bilingual marketing product?" --output comparisons/first.json
python -m unittest tests.test_compare_three_arms -v
```
No remote model is implicitly installed; install Ollama and an APPROVED model first. The command creates a new immutable comparison JSON record. The output itself is not an evaluation of reasoning correctness.

## Initial target customers and go/no-go thresholds (hypotheses)
Initial use case: bilingual freelancers, founders, marketing teams and AI builders. This is a customer hypothesis, not demonstrated demand.
- 10 invited test users, 30 held-out real prompts across marketing, research, and coding.
- >80% complete an A/B/C run unaided; proposed onboarding threshold.
- >=3/10 request a second run within 7 days; proposed retention signal.
- Do not charge for undefined “intelligence”; charge for credible time saved, reusable comparison/history and controlled workflow only after pilots.
- Do not market superiority unless blind quality and factual checks outperform baseline across several tasks and seeds.

## Shipping order
1. Ship one public landing page with one CTA: Try Compare. Hide obsolete/competing GPT/Gem/Stan purchase links after safe migration.
2. Build a one-page comparison UI over the existing CLI/API, with author-approved profiles, cost caps, raw-output export and reviewer vote.
3. Run independent user pilots and controlled evaluations.
4. Add login, data retention, privacy, licensing, billing only after end-to-end usage is verified.
5. Bonus fourth harness condition only after runtime permission/isolation fixes and fair tool-budget testing.

## Outreach / San Francisco
Not yet confirmed travel or any emails sent as of the decision. Do not block product release on an investor visit. A working 3-card demo with honest raw results is the asset to show evaluators and buyers.

## Sources
- https://github.com/fernandoiacosta/ACOSTA-Protocol-v3.0
- https://github.com/fernandoiacosta/Cognigenesis-protocol-v6
- https://github.com/fernandoiacosta/cognigenesis-harness
- https://jajalabs.com/
- https://docs.google.com/document/d/1-4gglNEhrvkEXlCcSiA2pBz7SJupCBucWSBLsQ5HQoM/edit
- https://help.openai.com/en/articles/20001519-custom-gpt-retirement-and-migration-faq
- https://support.google.com/gemini/answer/18560919?hl=en
