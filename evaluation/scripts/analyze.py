#!/usr/bin/env python3
"""Analyze Vex evaluation log and print summary statistics.

Usage: python3 analyze.py evaluation/data/eval_log.jsonl
"""

import json
import sys
from collections import defaultdict

# Per-1M-token pricing (update when prices change)
PRICING = {
    "haiku":  {"input": 0.80, "output": 4.00},
    "sonnet": {"input": 3.00, "output": 15.00},
    "opus":   {"input": 15.00, "output": 75.00},
}

OPUS_PRICING = PRICING["opus"]


def load_log(path):
    entries = []
    with open(path) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"Warning: skipping malformed line {line_num}", file=sys.stderr)
    return entries


def estimate_cost(entry):
    """Estimate cost in USD for a single task."""
    model = entry.get("routed_model", "opus")
    # Normalize model name
    model_key = model.split(":")[0] if ":" in model else model
    if model_key.startswith("ollama"):
        return 0.0  # Local models are free

    prices = PRICING.get(model_key, OPUS_PRICING)
    tokens_in = entry.get("tokens_in", 0)
    tokens_out = entry.get("tokens_out", 0)

    # If only total is available, assume 60/40 split
    if tokens_in == 0 and tokens_out == 0:
        total = entry.get("tokens_total", 0)
        tokens_in = int(total * 0.6)
        tokens_out = int(total * 0.4)

    cost = (tokens_in / 1_000_000 * prices["input"] +
            tokens_out / 1_000_000 * prices["output"])
    return cost


def estimate_opus_baseline_cost(entry):
    """What this task would have cost on Opus."""
    tokens_in = entry.get("tokens_in", 0)
    tokens_out = entry.get("tokens_out", 0)

    if tokens_in == 0 and tokens_out == 0:
        total = entry.get("tokens_total", 0)
        tokens_in = int(total * 0.6)
        tokens_out = int(total * 0.4)

    return (tokens_in / 1_000_000 * OPUS_PRICING["input"] +
            tokens_out / 1_000_000 * OPUS_PRICING["output"])


def print_section(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 analyze.py <eval_log.jsonl>")
        sys.exit(1)

    entries = load_log(sys.argv[1])
    if not entries:
        print("No entries found.")
        sys.exit(0)

    # --- Overview ---
    print_section("OVERVIEW")
    dates = sorted(set(e["date"] for e in entries))
    print(f"Tasks logged:     {len(entries)}")
    print(f"Date range:       {dates[0]} to {dates[-1]}")
    print(f"Days with data:   {len(dates)}")

    classes = defaultdict(int)
    for e in entries:
        classes[e.get("task_class", "UNKNOWN")] += 1
    print(f"\nTask distribution:")
    for cls, count in sorted(classes.items(), key=lambda x: -x[1]):
        print(f"  {cls:20s} {count:4d}  ({count/len(entries)*100:.0f}%)")

    # --- Cost ---
    print_section("COST ANALYSIS")
    total_actual = sum(estimate_cost(e) for e in entries)
    total_baseline = sum(estimate_opus_baseline_cost(e) for e in entries)
    total_tokens = sum(e.get("tokens_total", 0) for e in entries)

    print(f"Total tokens:          {total_tokens:,}")
    print(f"Estimated actual cost: ${total_actual:.4f}")
    print(f"Opus baseline cost:    ${total_baseline:.4f}")
    if total_baseline > 0:
        savings = (total_baseline - total_actual) / total_baseline * 100
        print(f"Savings vs baseline:   {savings:.1f}%")
    else:
        print("Savings vs baseline:   N/A (no token data)")

    # Cost by tier
    tier_stats = defaultdict(lambda: {"count": 0, "tokens": 0, "cost": 0.0})
    for e in entries:
        model = e.get("routed_model", "unknown")
        tier_stats[model]["count"] += 1
        tier_stats[model]["tokens"] += e.get("tokens_total", 0)
        tier_stats[model]["cost"] += estimate_cost(e)

    print(f"\nCost by tier:")
    print(f"  {'Tier':15s} {'Tasks':>6s} {'Tokens':>10s} {'Cost':>10s}")
    print(f"  {'-'*15} {'-'*6} {'-'*10} {'-'*10}")
    for tier in sorted(tier_stats.keys()):
        s = tier_stats[tier]
        print(f"  {tier:15s} {s['count']:6d} {s['tokens']:10,} ${s['cost']:9.4f}")

    # --- Quality ---
    print_section("QUALITY")
    scores = [e["quality_score"] for e in entries if "quality_score" in e]
    if scores:
        avg_score = sum(scores) / len(scores)
        pass_count = sum(1 for s in scores if s >= 3)
        rework = sum(1 for e in entries if e.get("rework_needed", False))
        print(f"Mean quality score: {avg_score:.2f}/5")
        print(f"Median score:       {sorted(scores)[len(scores)//2]}/5")
        print(f"Pass rate (>=3):    {pass_count}/{len(scores)} ({pass_count/len(scores)*100:.0f}%)")
        print(f"Rework needed:      {rework}/{len(entries)} ({rework/len(entries)*100:.0f}%)")

        # Quality by tier
        print(f"\nQuality by tier:")
        print(f"  {'Tier':15s} {'N':>4s} {'Mean':>6s} {'Pass%':>6s}")
        print(f"  {'-'*15} {'-'*4} {'-'*6} {'-'*6}")
        tier_scores = defaultdict(list)
        for e in entries:
            if "quality_score" in e:
                tier_scores[e.get("routed_model", "unknown")].append(e["quality_score"])
        for tier in sorted(tier_scores.keys()):
            sc = tier_scores[tier]
            avg = sum(sc) / len(sc)
            pct = sum(1 for s in sc if s >= 3) / len(sc) * 100
            print(f"  {tier:15s} {len(sc):4d} {avg:6.2f} {pct:5.0f}%")

    # --- Routing ---
    print_section("ROUTING ACCURACY")
    classified = [e for e in entries if "task_class_correct" in e]
    if classified:
        correct = sum(1 for e in classified if e["task_class_correct"])
        print(f"Classification accuracy: {correct}/{len(classified)} ({correct/len(classified)*100:.0f}%)")

    escalated = [e for e in entries if e.get("escalation_chain")]
    print(f"Tasks with escalation:  {len(escalated)}/{len(entries)} ({len(escalated)/len(entries)*100:.0f}%)")
    if escalated:
        esc_success = sum(1 for e in escalated if e.get("task_success", False))
        print(f"Escalation success:     {esc_success}/{len(escalated)} ({esc_success/len(escalated)*100:.0f}%)")

    # Manual pick comparison
    manual_match = sum(1 for e in entries
                       if e.get("manual_pick") and e.get("routed_model") == e.get("manual_pick"))
    manual_total = sum(1 for e in entries if e.get("manual_pick"))
    if manual_total:
        print(f"Matched manual pick:    {manual_match}/{manual_total} ({manual_match/manual_total*100:.0f}%)")

    # --- Per-class breakdown ---
    print_section("PER-CLASS BREAKDOWN")
    print(f"  {'Class':18s} {'N':>4s} {'Pass%':>6s} {'Mean':>6s} {'Esc%':>6s} {'AvgTok':>8s}")
    print(f"  {'-'*18} {'-'*4} {'-'*6} {'-'*6} {'-'*6} {'-'*8}")
    for cls in sorted(classes.keys()):
        cls_entries = [e for e in entries if e.get("task_class") == cls]
        n = len(cls_entries)
        sc = [e["quality_score"] for e in cls_entries if "quality_score" in e]
        avg = sum(sc) / len(sc) if sc else 0
        passes = sum(1 for s in sc if s >= 3) / len(sc) * 100 if sc else 0
        esc = sum(1 for e in cls_entries if e.get("escalation_chain")) / n * 100
        avg_tok = sum(e.get("tokens_total", 0) for e in cls_entries) / n
        print(f"  {cls:18s} {n:4d} {passes:5.0f}% {avg:6.2f} {esc:5.0f}% {avg_tok:8.0f}")

    # --- Warnings ---
    print_section("DATA QUALITY WARNINGS")
    low_n = [cls for cls, count in classes.items() if count < 5]
    if low_n:
        print(f"Insufficient data (<5 tasks): {', '.join(low_n)}")
        print("Do not report success rates for these classes.")
    estimated = sum(1 for e in entries if e.get("token_source") == "estimated")
    if estimated:
        print(f"Estimated token counts: {estimated}/{len(entries)} entries")
        print("Cost calculations for these entries are approximate.")
    if len(entries) < 50:
        print(f"\nOnly {len(entries)} tasks logged. Minimum 50 recommended for credible reporting.")


if __name__ == "__main__":
    main()
