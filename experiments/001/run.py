from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import request

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
EVAL_INSTRUCTION = """Return exactly one JSON object with these keys:
decision: one of yes, no, proceed, defer, insufficient, likely, unlikely
confidence: number from 0 to 1
evidence_used: array of evidence IDs
uncertainties: array of short strings
next_test: one concrete test that would most reduce decision uncertainty
rationale: concise explanation grounded only in the supplied evidence.
Do not use outside facts. Do not wrap the JSON in markdown."""

def load_cases() -> list[dict]:
    return [json.loads(line) for line in (HERE / "cases.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]

def git_commit() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return None

def installed_models(base_url: str, timeout: float) -> list[dict]:
    req = request.Request(base_url.rstrip("/") + "/api/tags", headers={"User-Agent": "Cognigenesis-Experiment/001"})
    with request.urlopen(req, timeout=min(timeout, 10.0)) as response:
        return list(json.loads(response.read().decode("utf-8")).get("models", []))

def call_ollama(base_url: str, model: str, system: str, prompt: str, temperature: float, seed: int, timeout: float) -> tuple[str, float]:
    payload = {
        "model": model,
        "stream": False,
        "messages": [{"role": "system", "content": system + "\n\n" + EVAL_INSTRUCTION}, {"role": "user", "content": prompt}],
        "options": {"temperature": temperature, "seed": seed, "num_predict": 700},
    }
    req = request.Request(base_url.rstrip("/") + "/api/chat", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", "User-Agent": "Cognigenesis-Experiment/001"}, method="POST")
    started = time.perf_counter()
    with request.urlopen(req, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    return (body.get("message") or {}).get("content", ""), time.perf_counter() - started

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:11434")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--timeout", type=float, default=300)
    args = parser.parse_args()
    models = installed_models(args.base_url, args.timeout)
    names = {str(item.get("name")) for item in models} | {str(item.get("model")) for item in models}
    if args.model not in names:
        raise SystemExit(f"Model {args.model!r} is not installed. Available: {', '.join(sorted(x for x in names if x)) or 'none'}")
    model_info = next((item for item in models if args.model in {str(item.get("name")), str(item.get("model"))}), {})
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = HERE / "results" / stamp
    out.mkdir(parents=True, exist_ok=False)
    dataset_bytes = (HERE / "cases.jsonl").read_bytes()
    treatment = (ROOT / "cognigenesis" / "resources" / "agent.md").read_text(encoding="utf-8")
    systems = {"baseline": "You are a helpful assistant.", "cognigenesis": treatment}
    seeds = [1103 + i * 7919 for i in range(args.runs)]
    manifest = {
        "experiment": "001", "status": "running", "started_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_commit(), "dataset_sha256": hashlib.sha256(dataset_bytes).hexdigest(),
        "model": args.model, "model_digest": model_info.get("digest"), "base_url": args.base_url,
        "temperature": args.temperature, "timeout_seconds": args.timeout, "seeds": seeds,
        "evaluation_instruction": EVAL_INSTRUCTION, "systems": systems, "records": [],
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for case in load_cases():
        for run_index, seed in enumerate(seeds, 1):
            for condition, system in systems.items():
                record = {"case_id": case["id"], "run": run_index, "seed": seed, "condition": condition, "prompt": case["prompt"]}
                try:
                    raw, latency = call_ollama(args.base_url, args.model, system, case["prompt"], args.temperature, seed, args.timeout)
                    record.update({"raw_response": raw, "latency_seconds": latency, "error": None})
                except Exception as exc:
                    record.update({"raw_response": "", "latency_seconds": None, "error": f"{type(exc).__name__}: {exc}"})
                manifest["records"].append(record)
                (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest["status"] = "complete"
    manifest["completed_at"] = datetime.now(timezone.utc).isoformat()
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    subprocess.run([sys.executable, str(HERE / "score.py"), str(out)], check=True)
    print(out)

if __name__ == "__main__":
    main()
