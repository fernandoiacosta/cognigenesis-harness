"""Three cumulative reasoning profiles, one explicitly chosen Ollama model.

Experimental preview: no claim of improved intelligence, no model fallback,
no automatic tools, no alteration of the historical protocols.
"""
from __future__ import annotations
import argparse, hashlib, json, time
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import Request, urlopen

BASE = "You are a helpful assistant. Answer the user's question."
V3 = ("Analyze strategic, tactical, and operational possibilities. State objectives, "
      "constraints, alternative explanations, counterarguments, and concrete tests. "
      "Separate evidence from inference and revise unsupported assumptions.")
V6 = ("For complex problems, compare useful competing hypotheses. Track uncertainty, "
      "verification, contradictions, and missing information. Run a bounded error "
      "check, then finish with a falsifiable and actionable result.")
PROFILES = {
    "regular": BASE,
    "acosta_v3": BASE + "\n" + V3,
    "acosta_v3_plus_cognigenesis_v6": BASE + "\n" + V3 + "\n" + V6,
}
def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def ollama(endpoint, payload, timeout):
    req = Request(endpoint.rstrip("/") + "/api/chat",
                  data=json.dumps(payload).encode(),
                  headers={"Content-Type":"application/json"}, method="POST")
    with urlopen(req,timeout=timeout) as res:
        return json.loads(res.read().decode())

def compare(prompt, model, path, *, endpoint="http://127.0.0.1:11434",
            seed=1103, temperature=0.2, timeout=300, request_fn=None):
    if not prompt.strip() or not model.strip():
        raise ValueError("Prompt and explicit model ID required")
    path = Path(path)
    if path.exists():
        raise FileExistsError("Never overwrite previous experimental records")
    call = request_fn or ollama
    report = {"schema":"cognigenesis-compare-0.1", "at":datetime.now(timezone.utc).isoformat(),
              "model":model, "prompt":prompt, "prompt_sha256":digest(prompt),
              "seed":seed, "temperature":temperature, "arm_definition":"operationalized, not full historical source",
              "records":[], "claim":"No superiority or factual correctness inferred"}
    for name,system in PROFILES.items():
        payload={"model":model,"stream":False,"messages":[{"role":"system","content":system},
                 {"role":"user","content":prompt}],
                 "options":{"temperature":temperature,"seed":seed,"num_predict":1200}}
        start=time.perf_counter()
        try:
            response=call(endpoint,payload,timeout)
            raw=(response.get("message") or {}).get("content","")
            if not isinstance(raw,str): raise TypeError("Non-text model result")
            record={"condition":name,"profile_sha256":digest(system),"raw_output":raw,
                    "latency_seconds":round(time.perf_counter()-start,3),
                    "prompt_tokens":response.get("prompt_eval_count"),
                    "completion_tokens":response.get("eval_count"),"error":None}
        except Exception as exc:
            record={"condition":name,"profile_sha256":digest(system),"raw_output":"",
                    "latency_seconds":round(time.perf_counter()-start,3),
                    "prompt_tokens":None,"completion_tokens":None,
                    "error":type(exc).__name__+": "+str(exc)}
        report["records"].append(record)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:
        json.dump(report,f,indent=2,ensure_ascii=False)
        f.write("\n")
    return report

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--prompt",required=True)
    parser.add_argument("--model",required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--endpoint",default="http://127.0.0.1:11434")
    args=parser.parse_args()
    out=compare(args.prompt,args.model,args.output,endpoint=args.endpoint)
    print(json.dumps({"file":str(args.output),"conditions":[
        {"name":r["condition"],"error":r["error"],"latency":r["latency_seconds"]}
        for r in out["records"]]},indent=2))
