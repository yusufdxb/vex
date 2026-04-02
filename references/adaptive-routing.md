# Adaptive Routing System

## Purpose

Every routing decision is logged. Over time, the log reveals which models actually succeed on which task types in *this* repository. Routing adjusts automatically when evidence accumulates.

## Log Format

File: `references/routing_log.jsonl` — one JSON object per line, append only.

```json
{"date":"2026-03-29","class":"DEBUGGING","mode":"cloud","model":"sonnet","success":false,"tokens":3200,"escalated_to":"opus","notes":"syntax error in output"}
{"date":"2026-03-29","class":"SINGLE_FILE","mode":"hybrid","model":"ollama:medium","success":true,"tokens":0,"escalated_to":null,"notes":""}
{"date":"2026-03-29","class":"TRIVIAL","mode":"cloud","model":"haiku","success":true,"tokens":400,"escalated_to":null,"notes":""}
```

Fields:
- `date`: ISO date string
- `class`: task class from Step 1 (TRIVIAL, DEBUGGING, etc.)
- `mode`: `cloud` or `hybrid`
- `model`: the model that was tried (`haiku`, `sonnet`, `opus`, `ollama:small`, `ollama:medium`, `ollama:large`, `claude:full`)
- `success`: true if task completed without escalation or build failure
- `tokens`: approximate tokens consumed
- `escalated_to`: next model used if failed, else null
- `notes`: brief failure reason or empty string

## Reading the Log Before Routing

Run this before routing any task where lower tiers are candidates:

### Cloud Mode
```bash
grep '"class":"CLASS_NAME"' references/routing_log.jsonl | grep '"mode":"cloud"' | python3 -c "
import sys, json
rows = [json.loads(l) for l in sys.stdin]
for model in ['haiku','sonnet']:
    total = sum(1 for r in rows if r['model']==model)
    wins  = sum(1 for r in rows if r['model']==model and r['success'])
    if total >= 3:
        rate = wins/total
        flag = ' <- SKIP' if rate < 0.40 else ''
        print(f'{model}: {wins}/{total} = {rate:.0%}{flag}')
    elif total > 0:
        print(f'{model}: {total} attempts -- insufficient data')
"
```

### Hybrid Mode
```bash
grep '"class":"CLASS_NAME"' references/routing_log.jsonl | grep '"mode":"hybrid"' | python3 -c "
import sys, json
rows = [json.loads(l) for l in sys.stdin]
for model in ['ollama:small','ollama:medium','ollama:large']:
    total = sum(1 for r in rows if r['model']==model)
    wins  = sum(1 for r in rows if r['model']==model and r['success'])
    if total >= 3:
        rate = wins/total
        flag = ' <- SKIP' if rate < 0.40 else ''
        print(f'{model}: {wins}/{total} = {rate:.0%}{flag}')
    elif total > 0:
        print(f'{model}: {total} attempts -- insufficient data')
"
```

## Routing Adjustment Rule

- Minimum 3 data points required before overriding default routing
- If success rate < 40% for a model+class combo → skip that tier
- If success rate > 80% for a model+class combo → prefer that tier even for slightly higher risk

## Estimated Success Rates by Task Type (bootstrap defaults)

> **These are author estimates, not measured data.** They are reasonable guesses based on general model capability expectations, provided as starting points until your routing log accumulates real data. Treat them as provisional — your actual success rates will likely differ.

### Cloud Mode

Use these until your log has >= 3 entries per class:

| Task Class | Haiku | Sonnet | Opus |
|---|---|---|---|
| TRIVIAL | 92% | 97% | 99% |
| MECHANICAL | 82% | 94% | 98% |
| SINGLE_FILE | 55% | 90% | 97% |
| MULTI_FILE | 20% | 82% | 95% |
| REFACTOR | 10% | 72% | 93% |
| DEBUGGING | 25% | 80% | 95% |
| INFRASTRUCTURE | 15% | 75% | 92% |
| ARCHITECTURAL | 5% | 45% | 90% |

### Hybrid Mode

| Task Class | ollama:small | ollama:medium | ollama:large | claude:full |
|---|---|---|---|---|
| TRIVIAL | 85% | 90% | 92% | 98% |
| MECHANICAL | 60% | 75% | 82% | 96% |
| SINGLE_FILE | 35% | 55% | 70% | 95% |
| MULTI_FILE | 10% | 20% | 35% | 92% |
| REFACTOR | 5% | 15% | 30% | 90% |
| DEBUGGING | 12% | 24% | 38% | 91% |
| INFRASTRUCTURE | 5% | 10% | 20% | 88% |
| ARCHITECTURAL | 2% | 5% | 10% | 87% |

These bootstrap rates explain the default routing table thresholds.

## Logging After Every Task

Append immediately after task completion. Don't batch or defer.

```bash
echo '{"date":"2026-03-29","class":"SINGLE_FILE","mode":"cloud","model":"haiku","success":true,"tokens":400,"escalated_to":null,"notes":""}' \
  >> references/routing_log.jsonl
```

## Token Cost Tracking

The `tokens` field tracks all API tokens. Ollama = 0.
Use this to calculate savings:

```bash
python3 -c "
import json
rows = [json.loads(l) for l in open('references/routing_log.jsonl')]
top = 'opus' if rows[0].get('mode') == 'cloud' else 'claude:full'
lower = sum(r['tokens'] for r in rows if r['model'] != top)
total = sum(r['tokens'] for r in rows)
print(f'Total tokens used: {total:,}')
print(f'Tokens on lower tiers: {lower:,}')
if total > 0:
    print(f'Lower-tier share: {lower/total*100:.0f}%')
print('Note: true cost savings depend on per-tier pricing, not just token counts.')
"
```
