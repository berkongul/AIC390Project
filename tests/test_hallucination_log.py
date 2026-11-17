"""Every claim in docs/hallucination_log_week2.json must be quoted exactly from the run's answers.

Run:  python -m unittest discover -s tests -v
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "docs" / "hallucination_log_week2.json"
TYPES = {"fabricated fact", "unfaithful", "reasoning error"}


@unittest.skipUnless(LOG.exists(), "no week 2 hallucination log")
class HallucinationLog(unittest.TestCase):
    def test_claims_are_exact_quotes_with_a_type(self):
        log = json.loads(LOG.read_text(encoding="utf-8"))
        raw = ROOT / log["run"] / "raw.jsonl"
        answers = {(r["version"], r["id"]): r for r in map(json.loads, raw.read_text(encoding="utf-8").splitlines())}
        self.assertGreaterEqual(len(log["entries"]), 10)
        for entry in log["entries"]:
            row = answers[(entry["version"], entry["test_id"])]
            self.assertIn(entry["claim"], row["answer"], entry["id"])
            self.assertIn(entry["type"], TYPES, entry["id"])
            self.assertEqual(entry["judge_pass"], row["judge"]["pass"], entry["id"])


if __name__ == "__main__":
    unittest.main()
