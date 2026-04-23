#!/usr/bin/env python3
"""Measure per-tier success rates and escalation effectiveness.

Sends coding prompts to each cloud tier (Haiku, Sonnet, Opus) and
optionally to Ollama models, checks outputs for correctness markers,
and reports success rates per tier per task class.

Usage:
  python3 evaluation/scripts/measure_routing.py --runs 1
  python3 evaluation/scripts/measure_routing.py --runs 3 --include-ollama
  python3 evaluation/scripts/measure_routing.py --tiers haiku,sonnet
"""

import argparse
import json
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

CLOUD_TIERS = {
    "haiku":  "claude-haiku-4-5",
    "sonnet": "claude-sonnet-4-6",
    "opus":   "claude-opus-4-7",
}

OLLAMA_TIERS = {
    "ollama:small":  "qwen2.5-coder:latest",
    "ollama:medium": "qwen2.5-coder:14b",
    "ollama:large":  "deepseek-coder-v2:16b",
}

PRICING = {
    "haiku":  {"input": 0.80, "output": 4.00},
    "sonnet": {"input": 3.00, "output": 15.00},
    "opus":   {"input": 15.00, "output": 75.00},
}


def load_prompts(path):
    prompts = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    prompts.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return prompts


def call_claude(model_id, prompt, timeout=120):
    args = [
        "claude", "-p",
        "--output-format", "json",
        "--tools", "",
        "--no-session-persistence",
        "--model", model_id,
        prompt,
    ]
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        return None, 0, 0
    raw = json.loads(r.stdout)
    usage = raw.get("usage", {})
    text = raw.get("result", "")
    return text, usage.get("input_tokens", 0), usage.get("output_tokens", 0)


def call_ollama(model_name, prompt, timeout=120):
    try:
        args = [
            "ollama", "run", model_name,
            "--nowordwrap",
            prompt,
        ]
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0:
            return None, 0, 0
        return r.stdout.strip(), 0, 0
    except Exception:
        return None, 0, 0


def check_success(response, prompt_entry):
    if not response or not response.strip():
        return False, "empty response"
    check = prompt_entry.get("check", "")
    if check and check.lower() not in response.lower():
        return False, f"missing '{check}'"
    fail_signals = ["I cannot", "I'm not sure", "I don't have enough", "I apologize"]
    for sig in fail_signals:
        if sig.lower() in response.lower():
            return False, f"refusal: '{sig}'"
    return True, "pass"


def run_measurement(prompts, tiers, runs, out_path):
    results = []
    total = len(prompts) * len(tiers) * runs
    idx = 0

    for run_i in range(runs):
        for prompt in prompts:
            for tier_name, model_id in tiers.items():
                idx += 1
                is_ollama = tier_name.startswith("ollama:")

                try:
                    if is_ollama:
                        text, tin, tout = call_ollama(model_id, prompt["prompt"])
                    else:
                        text, tin, tout = call_claude(model_id, prompt["prompt"])
                except subprocess.TimeoutExpired:
                    text, tin, tout = None, 0, 0
                except Exception as e:
                    print(f"  [{idx}/{total}] ERR {tier_name} {prompt['id']}: {e}", file=sys.stderr)
                    text, tin, tout = None, 0, 0

                success, reason = check_success(text, prompt)

                entry = {
                    "run": run_i,
                    "prompt_id": prompt["id"],
                    "class": prompt.get("class", "UNKNOWN"),
                    "tier": tier_name,
                    "model": model_id,
                    "success": success,
                    "reason": reason,
                    "input_tokens": tin,
                    "output_tokens": tout,
                    "response_len": len(text) if text else 0,
                    "response_preview": (text or "")[:100].replace("\n", " "),
                }
                results.append(entry)

                status = "OK" if success else f"FAIL ({reason})"
                print(f"  [{idx}/{total}] run{run_i} {prompt['id']:<24s} {tier_name:<15s} {status}")
                time.sleep(0.3)

    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            for r in results:
                f.write(json.dumps(r) + "\n")
        print(f"\nWrote {len(results)} entries to {out_path}")

    return results


def summarize(results):
    if not results:
        print("\nNo results.")
        return

    tier_order = ["haiku", "sonnet", "opus",
                  "ollama:small", "ollama:medium", "ollama:large"]
    tiers_present = [t for t in tier_order
                     if any(r["tier"] == t for r in results)]

    # Overall success rates
    print("\n" + "=" * 70)
    print("  PER-TIER SUCCESS RATES")
    print("=" * 70)
    print(f"{'Tier':<16s} {'N':>4s} {'Pass':>5s} {'Fail':>5s} {'Rate':>7s}")
    print("-" * 70)
    for tier in tiers_present:
        rs = [r for r in results if r["tier"] == tier]
        n = len(rs)
        wins = sum(1 for r in rs if r["success"])
        print(f"{tier:<16s} {n:4d} {wins:5d} {n-wins:5d} {wins/n*100:6.0f}%")

    # Per class x tier
    classes = sorted(set(r["class"] for r in results))
    print("\n" + "=" * 70)
    print("  SUCCESS RATE BY CLASS x TIER")
    print("=" * 70)
    header = f"{'Class':<18s}" + "".join(f"{t:<14s}" for t in tiers_present)
    print(header)
    print("-" * 70)
    for cls in classes:
        row = f"{cls:<18s}"
        for tier in tiers_present:
            rs = [r for r in results if r["class"] == cls and r["tier"] == tier]
            if rs:
                wins = sum(1 for r in rs if r["success"])
                row += f"{wins}/{len(rs)} ({wins/len(rs)*100:.0f}%)   "
            else:
                row += f"{'—':<14s}"
        print(row)

    # Simulated escalation
    print("\n" + "=" * 70)
    print("  SIMULATED ESCALATION (cloud tiers)")
    print("=" * 70)
    cloud_tiers = [t for t in tiers_present if not t.startswith("ollama")]
    if len(cloud_tiers) >= 2:
        by_prompt_run = defaultdict(dict)
        for r in results:
            if not r["tier"].startswith("ollama"):
                by_prompt_run[(r["prompt_id"], r["run"])][r["tier"]] = r["success"]

        escalation_stats = {"direct": 0, "escalated": 0, "failed": 0}
        escalation_chains = defaultdict(int)
        for key, tier_results in by_prompt_run.items():
            chain = []
            resolved = False
            for tier in cloud_tiers:
                if tier in tier_results:
                    if tier_results[tier]:
                        if not chain:
                            escalation_stats["direct"] += 1
                        else:
                            escalation_stats["escalated"] += 1
                            escalation_chains["→".join(chain + [tier])] += 1
                        resolved = True
                        break
                    else:
                        chain.append(tier)
            if not resolved:
                escalation_stats["failed"] += 1
                escalation_chains["→".join(chain) + "→FAIL"] += 1

        total = sum(escalation_stats.values())
        print(f"Direct success (first tier):  {escalation_stats['direct']:3d}/{total} ({escalation_stats['direct']/total*100:.0f}%)")
        print(f"Succeeded after escalation:   {escalation_stats['escalated']:3d}/{total} ({escalation_stats['escalated']/total*100:.0f}%)")
        print(f"Failed all tiers:             {escalation_stats['failed']:3d}/{total} ({escalation_stats['failed']/total*100:.0f}%)")
        if escalation_chains:
            print("\nEscalation chains:")
            for chain, count in sorted(escalation_chains.items(), key=lambda x: -x[1]):
                print(f"  {chain}: {count}")

    # Cost comparison
    print("\n" + "=" * 70)
    print("  ESTIMATED COST (cloud tiers only)")
    print("=" * 70)
    for tier in cloud_tiers:
        rs = [r for r in results if r["tier"] == tier]
        if rs and tier in PRICING:
            total_in = sum(r["input_tokens"] for r in rs)
            total_out = sum(r["output_tokens"] for r in rs)
            cost = (total_in * PRICING[tier]["input"] + total_out * PRICING[tier]["output"]) / 1e6
            print(f"{tier:<10s}: ${cost:.4f} ({len(rs)} calls, {total_in+total_out:,} tokens)")

    # Failure details
    failures = [r for r in results if not r["success"]]
    if failures:
        print("\n" + "=" * 70)
        print("  FAILURE DETAILS")
        print("=" * 70)
        for f in failures:
            preview = f["response_preview"][:60] if f["response_preview"] else "(empty)"
            print(f"  {f['tier']:<15s} {f['prompt_id']:<24s} {f['reason']:<20s} | {preview}")


def main():
    parser = argparse.ArgumentParser(description="Measure per-tier routing success rates.")
    parser.add_argument("--prompts", default="evaluation/routing_prompts.jsonl")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--tiers", default="haiku,sonnet,opus",
                        help="Comma-separated tiers (default: haiku,sonnet,opus)")
    parser.add_argument("--include-ollama", action="store_true",
                        help="Also test Ollama local models")
    parser.add_argument("--out", default="evaluation/data/routing_results.jsonl")
    args = parser.parse_args()

    prompts = load_prompts(args.prompts)
    if not prompts:
        print("No prompts found.", file=sys.stderr)
        sys.exit(1)

    tiers = {}
    for t in args.tiers.split(","):
        t = t.strip()
        if t in CLOUD_TIERS:
            tiers[t] = CLOUD_TIERS[t]
        elif t in OLLAMA_TIERS:
            tiers[t] = OLLAMA_TIERS[t]

    if args.include_ollama:
        tiers.update(OLLAMA_TIERS)

    total_calls = len(prompts) * len(tiers) * args.runs
    print(f"Prompts:     {len(prompts)}")
    print(f"Tiers:       {', '.join(tiers.keys())}")
    print(f"Runs:        {args.runs}")
    print(f"Total calls: {total_calls}")
    print()

    results = run_measurement(prompts, tiers, args.runs, args.out)
    summarize(results)


if __name__ == "__main__":
    main()
