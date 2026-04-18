"""Unit tests for evaluation/scripts/measure_compression.py.

Stdlib-only (uses unittest). Tests the pure functions — loading prompts,
cost estimation, response text extraction, summarization. Does not hit
the Anthropic API or shell out to `claude`.

Run from repo root:
    python3 -m unittest discover tests -v
"""

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "evaluation" / "scripts" / "measure_compression.py"

spec = importlib.util.spec_from_file_location("measure_compression", SCRIPT_PATH)
mc = importlib.util.module_from_spec(spec)
sys.modules["measure_compression"] = mc
spec.loader.exec_module(mc)


class TestLoadPrompts(unittest.TestCase):
    def test_loads_valid_jsonl(self):
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            f.write(json.dumps({"id": "a", "class": "TRIVIAL", "prompt": "p1"}) + "\n")
            f.write(json.dumps({"id": "b", "class": "RESEARCH", "prompt": "p2"}) + "\n")
            path = f.name
        prompts = mc.load_prompts(path)
        self.assertEqual(len(prompts), 2)
        self.assertEqual(prompts[0]["id"], "a")
        self.assertEqual(prompts[1]["class"], "RESEARCH")

    def test_skips_blank_lines(self):
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            f.write(json.dumps({"id": "a", "prompt": "p"}) + "\n")
            f.write("\n")
            f.write("   \n")
            f.write(json.dumps({"id": "b", "prompt": "p"}) + "\n")
            path = f.name
        prompts = mc.load_prompts(path)
        self.assertEqual(len(prompts), 2)

    def test_skips_malformed_lines(self):
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            f.write(json.dumps({"id": "a", "prompt": "p"}) + "\n")
            f.write("{not valid json\n")
            f.write(json.dumps({"id": "b", "prompt": "p"}) + "\n")
            path = f.name
        stderr_capture = io.StringIO()
        real_stderr = sys.stderr
        sys.stderr = stderr_capture
        try:
            prompts = mc.load_prompts(path)
        finally:
            sys.stderr = real_stderr
        self.assertEqual(len(prompts), 2)
        self.assertIn("malformed", stderr_capture.getvalue())

    def test_real_repo_prompt_file_parses(self):
        repo_prompts = REPO_ROOT / "evaluation" / "compression_prompts.jsonl"
        prompts = mc.load_prompts(repo_prompts)
        self.assertGreaterEqual(len(prompts), 6)
        for p in prompts:
            self.assertIn("id", p)
            self.assertIn("class", p)
            self.assertIn("prompt", p)


class TestEstimateCost(unittest.TestCase):
    def test_known_model_returns_positive_cost(self):
        cost = mc.estimate_cost("claude-sonnet-4-5", 1_000_000, 1_000_000)
        self.assertAlmostEqual(cost, 18.0, places=4)

    def test_haiku_cheaper_than_opus(self):
        h = mc.estimate_cost("claude-haiku-4-5", 1_000, 1_000)
        o = mc.estimate_cost("claude-opus-4-6", 1_000, 1_000)
        self.assertLess(h, o)

    def test_unknown_model_returns_none(self):
        self.assertIsNone(mc.estimate_cost("not-a-real-model", 100, 100))

    def test_zero_tokens_zero_cost(self):
        self.assertEqual(mc.estimate_cost("claude-sonnet-4-5", 0, 0), 0.0)


class TestExtractText(unittest.TestCase):
    def test_extracts_first_text_block(self):
        resp = {"content": [{"type": "text", "text": "hello"}]}
        self.assertEqual(mc.extract_text(resp), "hello")

    def test_skips_non_text_blocks(self):
        resp = {
            "content": [
                {"type": "tool_use", "name": "x"},
                {"type": "text", "text": "found me"},
            ]
        }
        self.assertEqual(mc.extract_text(resp), "found me")

    def test_empty_content_returns_empty_string(self):
        self.assertEqual(mc.extract_text({"content": []}), "")

    def test_missing_content_returns_empty_string(self):
        self.assertEqual(mc.extract_text({}), "")


class TestSystemPrompts(unittest.TestCase):
    def test_all_three_modes_defined(self):
        self.assertIn("normal", mc.SYSTEM_PROMPTS)
        self.assertIn("terse", mc.SYSTEM_PROMPTS)
        self.assertIn("caveman", mc.SYSTEM_PROMPTS)

    def test_normal_is_empty(self):
        self.assertEqual(mc.SYSTEM_PROMPTS["normal"], "")

    def test_terse_and_caveman_are_nonempty(self):
        self.assertTrue(mc.SYSTEM_PROMPTS["terse"])
        self.assertTrue(mc.SYSTEM_PROMPTS["caveman"])

    def test_caveman_mentions_word_limit(self):
        self.assertIn("5 words", mc.SYSTEM_PROMPTS["caveman"])


class TestSummarize(unittest.TestCase):
    def test_handles_empty_results_without_crashing(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            mc.summarize([])
        self.assertIn("No results", buf.getvalue())

    def test_computes_per_mode_savings(self):
        results = [
            {"mode": "normal",  "class": "RESEARCH", "output_tokens": 1000, "cost_usd": 0.015},
            {"mode": "terse",   "class": "RESEARCH", "output_tokens": 500,  "cost_usd": 0.0075},
            {"mode": "caveman", "class": "RESEARCH", "output_tokens": 200,  "cost_usd": 0.003},
        ]
        buf = io.StringIO()
        with redirect_stdout(buf):
            mc.summarize(results)
        out = buf.getvalue()
        self.assertIn("normal", out)
        self.assertIn("terse", out)
        self.assertIn("caveman", out)
        self.assertIn("-50.0%", out)
        self.assertIn("-80.0%", out)


class TestPricing(unittest.TestCase):
    def test_all_three_tiers_priced(self):
        self.assertIn("claude-haiku-4-5", mc.PRICING)
        self.assertIn("claude-sonnet-4-5", mc.PRICING)
        self.assertIn("claude-opus-4-6", mc.PRICING)

    def test_pricing_ordering_haiku_sonnet_opus(self):
        h = mc.PRICING["claude-haiku-4-5"]
        s = mc.PRICING["claude-sonnet-4-5"]
        o = mc.PRICING["claude-opus-4-6"]
        self.assertLess(h["input"], s["input"])
        self.assertLess(s["input"], o["input"])
        self.assertLess(h["output"], s["output"])
        self.assertLess(s["output"], o["output"])

    def test_output_more_expensive_than_input(self):
        for model, prices in mc.PRICING.items():
            with self.subTest(model=model):
                self.assertGreater(prices["output"], prices["input"])


if __name__ == "__main__":
    unittest.main()
