"""The committed week 3 scoreboard must match what src/scoreboard_week3.py computes."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import scoreboard_week3 as sb  # noqa: E402


class Week3Scoreboard(unittest.TestCase):
    def test_committed_file_matches_the_script(self):
        committed = json.loads(sb.OUT.read_text(encoding="utf-8"))
        with patch.object(sb, "OUT", ROOT / "results" / "_tmp_scoreboard_week3.json"):
            with patch("builtins.print"):
                sb.main()
            fresh = json.loads(sb.OUT.read_text(encoding="utf-8"))
            sb.OUT.unlink()
        self.assertEqual(committed, fresh)

    def test_every_key_present(self):
        board = json.loads(sb.OUT.read_text(encoding="utf-8"))
        self.assertEqual(len(board), 14)
        self.assertIsNotNone(board["hit_at_5"]["value"])


if __name__ == "__main__":
    unittest.main()
