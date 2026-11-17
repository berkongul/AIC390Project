"""Offline tests for src/rescore_week2.py. Uses the committed week 2 run, no API calls.

Run:  python -m unittest discover -s tests -v
"""
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import rescore_week2 as rs  # noqa: E402

RUN = ROOT / "results" / "week2" / "20261116T152017602676Z"


class Helpers(unittest.TestCase):
    def test_failed_calls_do_not_make_cost_null(self):
        calls = [
            {"status": "ok", "input_tokens": 1000, "output_tokens": 100, "latency_s": 1.0},
            {"status": "error", "input_tokens": None, "output_tokens": None, "latency_s": 0.1},
        ]
        self.assertAlmostEqual(rs.call_cost(calls, 0.075, 0.30), (1000 * 0.075 + 100 * 0.30) / 1e6)

    def test_latency_counts_model_time_only(self):
        row = {"pipeline_calls": [{"status": "ok", "latency_s": 0.5},
                                  {"status": "error", "latency_s": 0.2},
                                  {"status": "ok", "latency_s": 0.7}], "latency_s": 31.4}
        self.assertAlmostEqual(rs.model_seconds(row), 1.2)

    def test_abstention_pattern(self):
        for text in ("I can’t confirm that.", "I cannot check orders.", "I don't have the refund policy.",
                     "I'm not able to confirm return eligibility.", "I do not have access to order data."):
            self.assertTrue(rs.abstains(text), text)
        for text in ("Your order ships in 3 days.", "Yes, TR-220 runs small, order one size up.", ""):
            self.assertFalse(rs.abstains(text), text)

    def test_price_override(self):
        with patch.dict(os.environ, {"GROQ_INPUT_USD_PER_MILLION": "1", "GROQ_OUTPUT_USD_PER_MILLION": "2"}):
            self.assertEqual(rs.prices(), (1.0, 2.0))
        with patch.dict(os.environ, {"GROQ_INPUT_USD_PER_MILLION": "", "GROQ_OUTPUT_USD_PER_MILLION": ""}):
            self.assertEqual(rs.prices(), (rs.PRICE_IN, rs.PRICE_OUT))


@unittest.skipUnless(RUN.exists(), "committed week 2 run not present")
class CommittedRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.dict(os.environ, {"GROQ_INPUT_USD_PER_MILLION": "", "GROQ_OUTPUT_USD_PER_MILLION": ""}):
            cls.board, cls.detail = rs.rescore(RUN)
        cls.own = json.loads((RUN / "scoreboard_week2.json").read_text(encoding="utf-8"))

    def test_e2e_and_selection_are_unchanged(self):
        self.assertEqual(self.detail["selected_version"], "v3")
        self.assertEqual(self.board["e2e_accuracy"]["count"], self.own["e2e_accuracy"]["count"])
        self.assertEqual(self.board["e2e_accuracy"]["n"], 40)

    def test_judge_abstained_flag_is_never_true(self):
        for version in rs.VERSIONS:
            self.assertEqual(self.detail["versions"][version]["abstention_judge_flag"]["count"], 0)
        self.assertEqual(self.board["abstention_correct"]["n"], 9)
        self.assertEqual(self.board["abstention_correct"]["count"], 9)

    def test_every_key_present_and_numbers_measured(self):
        template = {"week", "test_set_size", "e2e_accuracy", "abstention_correct", "unsupported_claims",
                    "hit_at_5", "mrr", "task_success", "pass_k", "injection_success",
                    "cost_per_task_usd", "latency_p50_s", "spend_week_usd", "spend_total_usd"}
        self.assertEqual(set(self.board), template)
        self.assertGreater(self.board["cost_per_task_usd"], 0)
        self.assertLess(self.board["latency_p50_s"], 5)
        self.assertGreater(self.detail["versions"]["v3"]["latency_p50_with_pauses_s"], 15)
        self.assertEqual(self.board["injection_success"], {"value": 0.0, "n": 3, "script": "src/rescore_week2.py"})

    def test_spend_total_adds_week1(self):
        week1 = json.loads(rs.WEEK1_SCOREBOARD.read_text(encoding="utf-8"))["spend_total_usd"]
        self.assertAlmostEqual(self.board["spend_total_usd"], round(week1 + self.board["spend_week_usd"], 6), places=6)

    def test_committed_scoreboard_matches_the_script(self):
        committed = json.loads(rs.SCOREBOARD.read_text(encoding="utf-8"))
        self.assertEqual(committed, json.loads(json.dumps(self.board)))


if __name__ == "__main__":
    unittest.main()
