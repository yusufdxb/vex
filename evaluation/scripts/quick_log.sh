#!/usr/bin/env bash
# Quick task logger — 5 prompts instead of 17.
# Auto-fills date, ID, token estimates, codebase, languages.
#
# Usage: ./evaluation/scripts/quick_log.sh [log_file]
#
# Fields prompted:  summary, class, routed model, manual pick, quality (1-5)
# Fields defaulted: confidence=0.8, risk=LOW, impact=LOW, success=y,
#                   rework=n, tokens=class estimate, codebase=pwd basename,
#                   languages=auto-detect from repo
#
# Override defaults inline:  RISK=HIGH REWORK=y ./evaluation/scripts/quick_log.sh

set -euo pipefail

LOG_FILE="${1:-evaluation/data/eval_log.jsonl}"

# Auto-increment ID
if [ -f "$LOG_FILE" ] && [ -s "$LOG_FILE" ]; then
    LAST_ID=$(tail -1 "$LOG_FILE" | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('id','000'))" 2>/dev/null || echo "000")
    NEXT_ID=$(printf "%03d" $((10#$LAST_ID + 1)))
else
    NEXT_ID="001"
    mkdir -p "$(dirname "$LOG_FILE")"
fi

DATE=$(date +%Y-%m-%d)

echo "=== Quick Log (#$NEXT_ID) ==="

read -rp "Summary: " SUMMARY
read -rp "Class (T/M/S/MF/R/A/D/RE/I): " CLASS_SHORT
read -rp "Routed model (h/s/o): " MODEL_SHORT
read -rp "Your pick (h/s/o): " MANUAL_SHORT
read -rp "Quality (1-5): " SCORE

# Expand class shorthand
declare -A CLASS_MAP=( [T]=TRIVIAL [M]=MECHANICAL [S]=SINGLE_FILE [MF]=MULTI_FILE
    [R]=REFACTOR [A]=ARCHITECTURAL [D]=DEBUGGING [RE]=RESEARCH [I]=INFRASTRUCTURE )
CLASS="${CLASS_MAP[${CLASS_SHORT^^}]:-$CLASS_SHORT}"

# Expand model shorthand
expand_model() {
    case "${1,,}" in
        h|haiku)  echo "haiku" ;;
        s|sonnet) echo "sonnet" ;;
        o|opus)   echo "opus" ;;
        *)        echo "$1" ;;
    esac
}
MODEL=$(expand_model "$MODEL_SHORT")
MANUAL=$(expand_model "$MANUAL_SHORT")

# Token estimates by class (median from typical usage)
declare -A TOKEN_EST=( [TRIVIAL]=400 [MECHANICAL]=800 [SINGLE_FILE]=2000
    [MULTI_FILE]=5000 [REFACTOR]=8000 [ARCHITECTURAL]=15000
    [DEBUGGING]=3000 [RESEARCH]=4000 [INFRASTRUCTURE]=3000 )
TOKENS="${TOKEN_EST[$CLASS]:-2000}"

# Defaults (overridable via env)
CONFIDENCE="${CONFIDENCE:-0.80}"
RISK="${RISK:-LOW}"
IMPACT="${IMPACT:-LOW}"
SUCCESS="${SUCCESS:-y}"
REWORK="${REWORK:-n}"
REWORK_SEV="${REWORK_SEV:-0}"
WALL="${WALL:-0}"
CODEBASE="${CODEBASE:-$(basename "$(pwd)")}"
NOTES="${NOTES:-}"

# Auto-detect languages from repo
if command -v git &>/dev/null && git rev-parse --is-inside-work-tree &>/dev/null 2>&1; then
    LANGS_JSON=$(git ls-files | sed 's/.*\.//' | sort -u | python3 -c "
import sys
EXT_MAP = {'py':'python','ts':'typescript','js':'javascript','cpp':'c++',
           'rs':'rust','go':'go','java':'java','rb':'ruby','sh':'bash',
           'md':'markdown','yml':'yaml','yaml':'yaml'}
exts = [l.strip() for l in sys.stdin]
langs = sorted(set(EXT_MAP[e] for e in exts if e in EXT_MAP))
import json; print(json.dumps(langs[:5]))
" 2>/dev/null || echo '[]')
else
    LANGS_JSON='[]'
fi

# Convert y/n
[[ "${SUCCESS,,}" == "y" ]] && SUCC="true" || SUCC="false"
[[ "${REWORK,,}" == "y" ]] && RW="true" || RW="false"

TOKENS_IN=$(( TOKENS * 6 / 10 ))
TOKENS_OUT=$(( TOKENS * 4 / 10 ))

python3 -c "
import json, sys
entry = {
    'id': '$NEXT_ID',
    'date': '$DATE',
    'task_summary': sys.argv[1],
    'task_class': '$CLASS',
    'task_class_correct': True,
    'confidence': $CONFIDENCE,
    'risk': '$RISK',
    'impact': '$IMPACT',
    'routed_model': '$MODEL',
    'manual_pick': '$MANUAL',
    'escalation_chain': [],
    'tokens_in': $TOKENS_IN,
    'tokens_out': $TOKENS_OUT,
    'tokens_total': $TOKENS,
    'token_source': 'estimated',
    'quality_score': ${SCORE:-3},
    'task_success': $SUCC,
    'rework_needed': $RW,
    'rework_severity': ${REWORK_SEV:-0},
    'wall_clock_seconds': ${WALL:-0},
    'codebase': '$CODEBASE',
    'languages': $LANGS_JSON,
    'notes': sys.argv[2]
}
print(json.dumps(entry, ensure_ascii=False))
" "$SUMMARY" "$NOTES" >> "$LOG_FILE"

echo "Logged #$NEXT_ID → $LOG_FILE  [$CLASS | $MODEL | quality=$SCORE]"
