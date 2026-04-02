#!/usr/bin/env bash
# Interactive helper to log an evaluation task entry.
# Usage: ./evaluation/scripts/log_task.sh [log_file]
#
# Appends one JSONL entry to the evaluation log.

set -euo pipefail

LOG_FILE="${1:-evaluation/data/eval_log.jsonl}"

# Auto-increment ID
if [ -f "$LOG_FILE" ]; then
    LAST_ID=$(tail -1 "$LOG_FILE" 2>/dev/null | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('id','000'))" 2>/dev/null || echo "000")
    NEXT_ID=$(printf "%03d" $((10#$LAST_ID + 1)))
else
    NEXT_ID="001"
    mkdir -p "$(dirname "$LOG_FILE")"
fi

DATE=$(date +%Y-%m-%d)

echo "=== Vex Evaluation Log Entry ==="
echo "ID: $NEXT_ID | Date: $DATE"
echo ""

read -rp "Task summary: " SUMMARY
read -rp "Task class (TRIVIAL/MECHANICAL/SINGLE_FILE/MULTI_FILE/REFACTOR/ARCHITECTURAL/DEBUGGING/RESEARCH/INFRASTRUCTURE): " CLASS
read -rp "Was classification correct? (y/n): " CLASS_CORRECT
read -rp "Confidence (0.0-1.0): " CONFIDENCE
read -rp "Risk (LOW/MEDIUM/HIGH/CRITICAL): " RISK
read -rp "Impact (LOW/MEDIUM/HIGH/CRITICAL): " IMPACT
read -rp "Routed model (haiku/sonnet/opus/ollama:*): " MODEL
read -rp "What model would YOU have picked? " MANUAL
read -rp "Escalation chain (comma-separated models, or empty): " ESC_RAW
read -rp "Total tokens (approx): " TOKENS
read -rp "Token count source (exact/estimated): " TOKEN_SRC
read -rp "Quality score (1-5): " SCORE
read -rp "Task successful? (y/n): " SUCCESS
read -rp "Rework needed? (y/n): " REWORK
REWORK_SEV=0
if [[ "$REWORK" == "y" ]]; then
    read -rp "Rework severity (1=cosmetic, 2=functional, 3=redo): " REWORK_SEV
fi
read -rp "Wall clock seconds (approx): " WALL
read -rp "Codebase name: " CODEBASE
read -rp "Languages (comma-separated): " LANGS
read -rp "Notes: " NOTES

# Convert y/n to true/false
[[ "$CLASS_CORRECT" == "y" ]] && CC="true" || CC="false"
[[ "$SUCCESS" == "y" ]] && SUCC="true" || SUCC="false"
[[ "$REWORK" == "y" ]] && RW="true" || RW="false"

# Build escalation chain JSON array
if [ -z "$ESC_RAW" ]; then
    ESC_JSON="[]"
else
    ESC_JSON=$(echo "$ESC_RAW" | python3 -c "import sys,json; print(json.dumps([s.strip() for s in sys.stdin.read().strip().split(',')]))")
fi

# Build languages JSON array
LANGS_JSON=$(echo "$LANGS" | python3 -c "import sys,json; print(json.dumps([s.strip() for s in sys.stdin.read().strip().split(',') if s.strip()]))")

# Estimate input/output split (60/40)
TOKENS_IN=$(python3 -c "print(int(${TOKENS:-0} * 0.6))")
TOKENS_OUT=$(python3 -c "print(int(${TOKENS:-0} * 0.4))")

# Write entry
python3 -c "
import json
entry = {
    'id': '$NEXT_ID',
    'date': '$DATE',
    'task_summary': $(python3 -c "import json; print(json.dumps('$SUMMARY'))"),
    'task_class': '$CLASS',
    'task_class_correct': $CC,
    'confidence': ${CONFIDENCE:-0.5},
    'risk': '$RISK',
    'impact': '$IMPACT',
    'routed_model': '$MODEL',
    'manual_pick': '$MANUAL',
    'escalation_chain': $ESC_JSON,
    'tokens_in': $TOKENS_IN,
    'tokens_out': $TOKENS_OUT,
    'tokens_total': ${TOKENS:-0},
    'token_source': '$TOKEN_SRC',
    'quality_score': ${SCORE:-3},
    'task_success': $SUCC,
    'rework_needed': $RW,
    'rework_severity': ${REWORK_SEV:-0},
    'wall_clock_seconds': ${WALL:-0},
    'codebase': '$CODEBASE',
    'languages': $LANGS_JSON,
    'notes': $(python3 -c "import json; print(json.dumps('$NOTES'))")
}
print(json.dumps(entry, ensure_ascii=False))
" >> "$LOG_FILE"

echo ""
echo "Logged entry $NEXT_ID to $LOG_FILE"
