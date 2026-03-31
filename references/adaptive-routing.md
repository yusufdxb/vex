# Adaptive Routing System

## Purpose

Every routing decision is logged. Over time, the log reveals which models actually succeed on which task types in *this* repository. Routing adjusts automatically when evidence accumulates.

## Log Format

File: `references/routing_log.jsonl` — one JSON object per line, append only.

```json
{"date":"2026-03-29","class":"DEBUGGING","model":"ollama:large","success":false,"tokens":3200,"escalated_to":"claude:full","notes":"syntax error in output"}
{"date":"2026-03-29","class":"SINGLE_FILE","model":"ollama:medium","success":true,"tokens":1100,"escalated_to":null,"notes":""}
```

Fields:
- `date`: ISO date string
- `class`: task class from Step 1 (TRIVIAL, DEBUGGING, etc.)
- `model`: the model that was tried (`ollama:small`, `ollama:medium`, `ollama:large`, `claude:full`)
- `success`: true if task completed without escalation or build failure
- `tokens`: approximate Claude tokens consumed (0 for pure Ollama runs)
- `escalated_to`: next model used if failed, else null
- `notes`: brief failure reason or empty string

## Reading the Log Before Routing

Run this before routing any task where local models are candidates:

```bash
grep '"class":"CLASS_NAME"' references/routing_log.jsonl | python3 -c "
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

Use these until your log has >= 3 entries per class:

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
echo '{"date":"2026-03-29","class":"SINGLE_FILE","model":"ollama:medium","success":true,"tokens":0,"escalated_to":null,"notes":""}' \
  >> references/routing_log.jsonl
```

## Token Cost Tracking

The `tokens` field tracks Claude API tokens only (Ollama = 0).
Use this to calculate monthly savings:

```bash
python3 -c "
import json
rows = [json.loads(l) for l in open('references/routing_log.jsonl')]
saved = sum(r['tokens'] for r in rows if r['model'] != 'claude:full')
total = sum(r['tokens'] for r in rows)
print(f'Claude tokens used: {total:,}')
print(f'Tokens saved by routing: {saved:,} ({saved/(total+saved)*100:.0f}%)')
"
```
