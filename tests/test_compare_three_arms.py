import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/"experiments"/"compare"/"compare.py"
spec=importlib.util.spec_from_file_location("cg_compare",SCRIPT)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class CompareTests(unittest.TestCase):
    def test_cumulative_profiles(self):
        p=mod.PROFILES
        self.assertEqual(len(p),3)
        self.assertIn(mod.V3,p["acosta_v3"])
        self.assertIn(mod.V3,p["acosta_v3_plus_cognigenesis_v6"])
        self.assertIn(mod.V6,p["acosta_v3_plus_cognigenesis_v6"])
        self.assertNotIn(mod.V6,p["acosta_v3"])

    def test_matched_settings_and_preserved_raw_output(self):
        seen=[]
        def fake(endpoint,payload,timeout):
            seen.append(payload)
            return {"message":{"content":"No. Evidence is weak."},"eval_count":9}
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"output.json"
            result=mod.compare("Explain the options","gemma4:e2b",path,request_fn=fake)
            self.assertEqual(len(seen),3)
            self.assertEqual({p["model"] for p in seen},{"gemma4:e2b"})
            self.assertEqual({p["options"]["seed"] for p in seen},{1103})
            self.assertEqual({p["messages"][1]["content"] for p in seen},{"Explain the options"})
            self.assertTrue(all(a["raw_output"]=="No. Evidence is weak." for a in result["records"]))
            with self.assertRaises(FileExistsError):
                mod.compare("Another prompt","gemma4:e2b",path,request_fn=fake)

    def test_no_silent_model_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                mod.compare("Question","",Path(td)/"run.json")

    def test_error_is_recorded_not_hidden(self):
        def fail(*args): raise RuntimeError("runtime unavailable")
        with tempfile.TemporaryDirectory() as td:
            result=mod.compare("Test","gemma4:e2b",Path(td)/"run.json",request_fn=fail)
        self.assertTrue(all(r["error"]=="RuntimeError: runtime unavailable" for r in result["records"]))
        self.assertTrue(all(r["raw_output"]=="" for r in result["records"]))

if __name__=="__main__": unittest.main()
