# Repository Impact Analysis

## Purpose

Before routing, estimate blast radius: how many files break if this change goes wrong?
Use grep + git — no AST or call graph tooling required.

## Impact Analysis Commands

### 1. Symbol reference count (most important)

```bash
# How many files reference the symbol being changed?
SYMBOL="MyFunction"
grep -r "$SYMBOL" . \
  --include="*.py" --include="*.cpp" --include="*.hpp" \
  --include="*.h" --include="*.ts" --include="*.js" \
  --include="*.go" --include="*.rs" --include="*.java" \
  -l 2>/dev/null | grep -v "^./build\|^./node_modules\|^./target\|^./dist" | wc -l
```

### 2. Public API surface check

```bash
# Is this symbol exported from a header/interface file?
grep -r "$SYMBOL" --include="*.h" --include="*.hpp" --include="*.d.ts" --include="*.pyi" -l 2>/dev/null | wc -l
# >0 means it's part of the public API — downstream impact is likely
```

### 3. Dependency graph check

```bash
# Adapt to your build system:
# npm/yarn:  grep -r "\"$SYMBOL\"" package.json */package.json
# pip:       grep -r "$SYMBOL" requirements*.txt setup.py pyproject.toml
# cargo:     grep -r "$SYMBOL" Cargo.toml */Cargo.toml
# go:        grep -r "$SYMBOL" go.mod */go.mod
# gradle:    grep -r "$SYMBOL" build.gradle* settings.gradle*
```

### 4. Cross-package import depth

```bash
# How many packages/modules import from the module being changed?
grep -r "from pkg_name import\|import pkg_name\|require.*pkg_name\|#include.*pkg_name" \
  . -l --include="*.py" --include="*.ts" --include="*.js" --include="*.go" --include="*.rs" | wc -l
```

### 5. Git blame scope (recent changes to touched area)

```bash
# Have others recently touched these lines? More churn = more risk
git log --oneline -10 -- path/to/file
```

## Impact Score Thresholds

| Downstream files | Impact Level | Routing effect |
|---|---|---|
| 0–1 | LOW | No change to default route |
| 2–5 | MEDIUM | Escalate one tier |
| 6–15 | HIGH | Route like MULTI_FILE HIGH |
| 16+ | CRITICAL | Force `claude:full` |

## Practical Impact Check (one-liner)

Run this when you know the symbol name and want a quick score:

```bash
SYM="my_function"
N=$(grep -r "$SYM" . -l --include="*.py" --include="*.ts" --include="*.js" --include="*.go" --include="*.rs" --include="*.cpp" --include="*.java" 2>/dev/null | grep -v "node_modules\|build\|dist\|target" | wc -l)
echo "Impact: $N files reference $SYM"
if   [ "$N" -ge 16 ]; then echo "CRITICAL -- force claude:full"
elif [ "$N" -ge  6 ]; then echo "HIGH -- route as MULTI_FILE HIGH"
elif [ "$N" -ge  2 ]; then echo "MEDIUM -- escalate one tier"
else                        echo "LOW -- proceed with default route"
fi
```

## When to Skip Impact Analysis

Skip if any of these are already true:
- RISK = CRITICAL (already going to `claude:full`)
- Task class = ARCHITECTURAL or RESEARCH
- confidence < 0.65 (already forced to `claude:plan`)
- Task is TRIVIAL (0–1 files, impact analysis would be overkill)

## Notes

- Impact analysis adds ~2–5 seconds of grep time. Always worth it for SINGLE_FILE+ tasks.
- False negatives are common (grep won't find dynamic dispatch, templates, macros). When in doubt, assume MEDIUM.
- If your project has interface/schema files that generate code (protobuf, GraphQL, OpenAPI), any change to those files has CRITICAL impact by definition.
