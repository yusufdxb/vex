#!/usr/bin/env python3
"""Measure output token savings from Vex compression modes.

Runs each prompt from a JSONL file through the Anthropic Messages API
in three modes — normal, terse, caveman — logs per-call output tokens,
and prints a summary table with estimated cost savings.

Methodology:
  This script SIMULATES each compression mode by injecting a system
  prompt that encodes the rule. It measures whether the rule reduces
  output tokens when the model is instructed to follow it. It does NOT
  measure whether the `/vex terse` or `/vex caveman` slash commands are
  correctly honored by Claude Code in a real session — that requires
  separate in-session testing.

Requirements:
  - Python 3.9+
  - ANTHROPIC_API_KEY environment variable
  - stdlib only (no third-party packages)

Usage:
  python3 evaluation/scripts/measure_compression.py
  python3 evaluation/scripts/measure_compression.py --model claude-sonnet-4-5 --runs 3
  python3 evaluation/scripts/measure_compression.py --prompts my_prompts.jsonl --out my_results.jsonl
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

SYSTEM_PROMPTS = {
    "normal": "",
    "terse": (
        "Output constraint: every reply must be at most 15 words, full "
        "sentences, no preamble, no markdown headers, no bullet lists, "
        "no trailing summary. State only the result, next action, or blocker."
    ),
    "caveman": (
        "Output constraint: every reply must be 1 to 5 words total. "
        "Broken grammar. No articles. No punctuation. Drop pronouns and "
        "auxiliary verbs. Never exceed 5 words."
    ),
    "tight": (
        "Output constraint: no opening sentence about what you are about to "
        "do ('I'll...', 'Let me...', 'Sure...'). No closing sentence summarizing "
        "what you did. No 'Here is...' preambles. Full sentences and normal "
        "length are fine — just cut preamble and trailing summary. If the "
        "answer is a code block, output only the code block with no prose "
        "wrapping it unless the user asked for explanation."
    ),
    "ghost": (
        "Output constraint: reply with at most 10 words total, in the form "
        "'done: <what>' or 'blocked: <why>' or a direct minimal answer. "
        "Never narrate what you did or will do. Never echo code that was "
        "written to a file. If the reply would be a code block, output "
        "only the code block with zero prose around it. Anything beyond 10 "
        "words of prose violates the constraint."
    ),
}

# Per-1M-token pricing. Author estimate — verify against
# https://www.anthropic.com/pricing before trusting reported cost.
PRICING = {
    "claude-haiku-4-5":  {"input": 0.80, "output": 4.00},
    "claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
    "claude-opus-4-6":   {"input": 15.00, "output": 75.00},
}


def load_prompts(path):
    prompts = []
    with open(path) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                prompts.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Warning: skipping malformed prompt line {line_num}: {e}", file=sys.stderr)
    return prompts


def call_claude_cli(model, system, user_prompt, timeout=180):
    """Invoke `claude -p` and return a response dict matching the Anthropic
    Messages API shape (usage.input_tokens, usage.output_tokens, content).

    Uses the user's Claude Code subscription auth — no API key needed.
    Loads the user's installed skills by default, which can contaminate
    replies (e.g., meta-skill preambles). Pass `--bare` upstream if you need
    an isolated baseline, but note that `--bare` disables subscription auth
    and requires ANTHROPIC_API_KEY.
    """
    args = [
        "claude", "-p",
        "--output-format", "json",
        "--tools", "",
        "--no-session-persistence",
        "--model", model,
    ]
    if system:
        args += ["--append-system-prompt", system]
    args += [user_prompt]
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"claude -p exited {r.returncode}: {(r.stderr or r.stdout)[:200]}")
    raw = json.loads(r.stdout)
    # Normalize to the shape the rest of the script expects.
    usage = raw.get("usage", {})
    text = raw.get("result", "")
    return {
        "usage": {
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
        },
        "content": [{"type": "text", "text": text}],
    }


def call_anthropic(api_key, model, system, user_prompt, max_tokens=512):
    body = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    if system:
        body["system"] = system
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def estimate_cost(model, input_tokens, output_tokens):
    if model not in PRICING:
        return None
    p = PRICING[model]
    return (input_tokens * p["input"] + output_tokens * p["output"]) / 1_000_000


def extract_text(resp):
    for block in resp.get("content", []):
        if block.get("type") == "text":
            return block.get("text", "")
    return ""


def run_measurements(prompts, modes, model, api_key, runs, out_path, backend="api"):
    results = []
    total_calls = len(prompts) * len(modes) * runs
    call_idx = 0
    for run_i in range(runs):
        for prompt in prompts:
            for mode in modes:
                call_idx += 1
                system = SYSTEM_PROMPTS[mode]
                try:
                    if backend == "claude-cli":
                        resp = call_claude_cli(model, system, prompt["prompt"])
                    else:
                        resp = call_anthropic(api_key, model, system, prompt["prompt"])
                except urllib.error.HTTPError as e:
                    body = e.read().decode(errors="replace")[:200]
                    print(f"  [{call_idx}/{total_calls}] HTTPError {e.code} on {prompt['id']}/{mode}: {body}", file=sys.stderr)
                    continue
                except Exception as e:
                    print(f"  [{call_idx}/{total_calls}] ERR on {prompt['id']}/{mode}: {e}", file=sys.stderr)
                    continue
                usage = resp.get("usage", {})
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)
                text = extract_text(resp)
                cost = estimate_cost(model, input_tokens, output_tokens)
                entry = {
                    "run": run_i,
                    "prompt_id": prompt["id"],
                    "class": prompt.get("class", "UNKNOWN"),
                    "mode": mode,
                    "model": model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_usd": cost,
                    "reply_chars": len(text),
                    "reply_preview": text[:120].replace("\n", " "),
                }
                results.append(entry)
                cost_str = f"${cost:.5f}" if cost is not None else "cost=?"
                print(
                    f"  [{call_idx}/{total_calls}] run{run_i} "
                    f"{prompt['id']:<24} {mode:<8} "
                    f"out={output_tokens:<4} {cost_str}"
                )
                time.sleep(0.3)  # be polite to the API

    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            for r in results:
                f.write(json.dumps(r) + "\n")
        print(f"\nWrote {len(results)} entries to {out_path}")
    return results


def summarize(results):
    if not results:
        print("\nNo results to summarize.")
        return

    by_mode = defaultdict(list)
    for r in results:
        by_mode[r["mode"]].append(r)

    normal_total_out = sum(r["output_tokens"] for r in by_mode.get("normal", []))

    print("\nPer-mode summary")
    print("=" * 78)
    print(f"{'Mode':<10} {'N':<4} {'Avg out':<9} {'Total out':<11} {'Total cost':<12} {'vs normal':<10}")
    print("-" * 78)
    for mode in ["normal", "terse", "caveman", "tight", "ghost"]:
        rs = by_mode.get(mode, [])
        if not rs:
            continue
        n = len(rs)
        total_out = sum(r["output_tokens"] for r in rs)
        avg_out = total_out / n
        total_cost = sum(r["cost_usd"] or 0 for r in rs)
        if mode == "normal" or normal_total_out == 0:
            savings = "—"
        else:
            pct = (1 - total_out / normal_total_out) * 100
            sign = "-" if pct >= 0 else "+"
            savings = f"{sign}{abs(pct):.1f}%"
        cost_str = f"${total_cost:.4f}" if total_cost else "?"
        print(f"{mode:<10} {n:<4} {avg_out:<9.1f} {total_out:<11} {cost_str:<12} {savings:<10}")
    print("=" * 78)

    by_class = defaultdict(lambda: defaultdict(list))
    for r in results:
        by_class[r["class"]][r["mode"]].append(r["output_tokens"])

    print("\nAvg output tokens by class x mode")
    print("-" * 78)
    header = f"{'Class':<18}" + "".join(f"{m:<12}" for m in ["normal", "terse", "caveman", "tight", "ghost"])
    print(header)
    for cls in sorted(by_class):
        row_vals = []
        for mode in ["normal", "terse", "caveman", "tight", "ghost"]:
            xs = by_class[cls].get(mode, [])
            row_vals.append(f"{sum(xs)/len(xs):.0f}" if xs else "—")
        print(f"{cls:<18}" + "".join(f"{v:<12}" for v in row_vals))

    print("\nNote: output-token savings only. Input tokens and file-writes via")
    print("tool calls are unaffected by compression modes.")


def main():
    parser = argparse.ArgumentParser(
        description="Measure output-token savings from Vex compression modes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--prompts", default="evaluation/compression_prompts.jsonl",
                        help="JSONL file of prompts (default: %(default)s)")
    parser.add_argument("--model", default="claude-sonnet-4-5",
                        help="Anthropic model ID (default: %(default)s)")
    parser.add_argument("--runs", type=int, default=1,
                        help="Repetitions per (prompt, mode) combo (default: %(default)s)")
    parser.add_argument("--modes", default="normal,terse,caveman,tight,ghost",
                        help="Comma-separated modes to run (default: %(default)s)")
    parser.add_argument("--out", default="evaluation/data/compression_results.jsonl",
                        help="Output JSONL path (default: %(default)s, gitignored)")
    parser.add_argument("--backend", default="api", choices=["api", "claude-cli"],
                        help="Where to send requests: 'api' uses ANTHROPIC_API_KEY via the Messages API, "
                             "'claude-cli' shells out to `claude -p` and uses your Claude Code subscription. "
                             "claude-cli loads your installed skills, which can contaminate replies. "
                             "(default: %(default)s)")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if args.backend == "api" and not api_key:
        print("ERROR: ANTHROPIC_API_KEY env var is not set (required for --backend api).", file=sys.stderr)
        sys.exit(1)
    if args.backend == "claude-cli":
        try:
            subprocess.run(["claude", "--version"], capture_output=True, check=True, timeout=10)
        except Exception as e:
            print(f"ERROR: `claude --version` failed (required for --backend claude-cli): {e}", file=sys.stderr)
            sys.exit(1)

    prompts_path = Path(args.prompts)
    if not prompts_path.exists():
        print(f"ERROR: prompts file not found: {prompts_path}", file=sys.stderr)
        sys.exit(1)
    prompts = load_prompts(prompts_path)
    if not prompts:
        print(f"ERROR: no valid prompts in {prompts_path}", file=sys.stderr)
        sys.exit(1)

    modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    for m in modes:
        if m not in SYSTEM_PROMPTS:
            print(f"ERROR: unknown mode '{m}'. Valid: {list(SYSTEM_PROMPTS)}", file=sys.stderr)
            sys.exit(1)

    if args.model not in PRICING:
        print(f"Warning: no pricing data for model '{args.model}' — cost columns will be empty.", file=sys.stderr)

    print(f"Backend:          {args.backend}")
    print(f"Model:            {args.model}")
    print(f"Prompts:          {len(prompts)} from {prompts_path}")
    print(f"Modes:            {', '.join(modes)}")
    print(f"Runs per combo:   {args.runs}")
    print(f"Total calls:      {len(prompts) * len(modes) * args.runs}")
    print()

    results = run_measurements(prompts, modes, args.model, api_key, args.runs, args.out, backend=args.backend)
    summarize(results)


if __name__ == "__main__":
    main()
