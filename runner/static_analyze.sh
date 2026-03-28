#!/usr/bin/env bash
# Static analysis runner for benchmark-generated code.
# Runs platform-specific linters and returns a JSON report.
#
# Usage: static_analyze.sh <platform> <work_dir>
# Output: JSON to stdout with lint results and normalized score (0-10).

set -uo pipefail

PLATFORM="${1:-}"
WORK_DIR="${2:-}"

if [[ -z "$PLATFORM" || -z "$WORK_DIR" ]]; then
    echo '{"error": "Usage: static_analyze.sh <platform> <work_dir>", "score": 0}'
    exit 1
fi

analyze_ios() {
    local dir="$1"
    local warnings=0
    local errors=0
    local output=""

    if command -v swiftlint &>/dev/null; then
        output=$(cd "$dir" && swiftlint lint --quiet --reporter json 2>/dev/null || true)
        if [[ -n "$output" ]] && echo "$output" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
            warnings=$(echo "$output" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(sum(1 for v in data if v.get('severity','') == 'warning'))
" 2>/dev/null || echo "0")
            errors=$(echo "$output" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(sum(1 for v in data if v.get('severity','') == 'error'))
" 2>/dev/null || echo "0")
        fi
    else
        # Fallback: basic Swift checks
        local swift_files
        swift_files=$(find "$dir" -name "*.swift" -not -path "*/_*" 2>/dev/null)
        if [[ -n "$swift_files" ]]; then
            # Check for force unwraps
            warnings=$(echo "$swift_files" | xargs grep -c '!' 2>/dev/null | awk -F: '{s+=$NF}END{print s+0}')
            # Check for force casts
            errors=$(echo "$swift_files" | xargs grep -c 'as!' 2>/dev/null | awk -F: '{s+=$NF}END{print s+0}')
        fi
    fi

    echo "$warnings" "$errors"
}

analyze_android() {
    local dir="$1"
    local warnings=0
    local errors=0

    if command -v ktlint &>/dev/null; then
        local output
        output=$(cd "$dir" && find . -name "*.kt" -not -path "*/_*" -exec ktlint --reporter=json {} + 2>/dev/null || true)
        if [[ -n "$output" ]] && echo "$output" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
            errors=$(echo "$output" | python3 -c "
import sys, json
data = json.load(sys.stdin)
count = 0
for f in data:
    count += len(f.get('errors', []))
print(count)
" 2>/dev/null || echo "0")
        fi
    elif command -v detekt &>/dev/null; then
        local output
        output=$(cd "$dir" && detekt --input . 2>&1 || true)
        warnings=$(echo "$output" | grep -c "warning" 2>/dev/null || echo "0")
        errors=$(echo "$output" | grep -c "error" 2>/dev/null || echo "0")
    else
        # Fallback: basic Kotlin checks
        local kt_files
        kt_files=$(find "$dir" -name "*.kt" -not -path "*/_*" 2>/dev/null)
        if [[ -n "$kt_files" ]]; then
            warnings=$(echo "$kt_files" | xargs grep -c '!!' 2>/dev/null | awk -F: '{s+=$NF}END{print s+0}')
            errors=$(echo "$kt_files" | xargs grep -c 'var ' 2>/dev/null | awk -F: '{s+=$NF}END{print s+0}')
            # var count is a soft signal, not a real error count; halve it
            errors=$((errors / 2))
        fi
    fi

    echo "$warnings" "$errors"
}

analyze_flutter() {
    local dir="$1"
    local warnings=0
    local errors=0
    local infos=0

    # Check if this is a proper Flutter/Dart project
    if [[ -f "$dir/pubspec.yaml" ]] && command -v dart &>/dev/null; then
        local output
        output=$(cd "$dir" && dart analyze --format=json 2>/dev/null || true)
        if [[ -n "$output" ]]; then
            warnings=$(echo "$output" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    diags = data.get('diagnostics', [])
    print(sum(1 for d in diags if d.get('severity','') == 'WARNING'))
except: print(0)
" 2>/dev/null || echo "0")
            errors=$(echo "$output" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    diags = data.get('diagnostics', [])
    print(sum(1 for d in diags if d.get('severity','') == 'ERROR'))
except: print(0)
" 2>/dev/null || echo "0")
            infos=$(echo "$output" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    diags = data.get('diagnostics', [])
    print(sum(1 for d in diags if d.get('severity','') == 'INFO'))
except: print(0)
" 2>/dev/null || echo "0")
        fi
    else
        # Fallback: basic Dart checks
        local dart_files
        dart_files=$(find "$dir" -name "*.dart" -not -path "*/_*" 2>/dev/null)
        if [[ -n "$dart_files" ]]; then
            warnings=$(echo "$dart_files" | xargs grep -c 'print(' 2>/dev/null | awk -F: '{s+=$NF}END{print s+0}')
            errors=0
        fi
    fi

    echo "$warnings" "$errors" "$infos"
}

# Count source files
count_source_files() {
    local dir="$1"
    local platform="$2"
    case "$platform" in
        ios) find "$dir" -name "*.swift" -not -path "*/_*" 2>/dev/null | wc -l | tr -d ' ' ;;
        android) find "$dir" -name "*.kt" -not -path "*/_*" 2>/dev/null | wc -l | tr -d ' ' ;;
        flutter) find "$dir" -name "*.dart" -not -path "*/_*" 2>/dev/null | wc -l | tr -d ' ' ;;
        *) echo "0" ;;
    esac
}

# Run analysis
WARNINGS=0
ERRORS=0
INFOS=0

case "$PLATFORM" in
    ios)
        read -r WARNINGS ERRORS <<< "$(analyze_ios "$WORK_DIR")"
        ;;
    android)
        read -r WARNINGS ERRORS <<< "$(analyze_android "$WORK_DIR")"
        ;;
    flutter)
        read -r WARNINGS ERRORS INFOS <<< "$(analyze_flutter "$WORK_DIR")"
        ;;
    *)
        echo '{"error": "Unknown platform: '"$PLATFORM"'", "score": 0}'
        exit 1
        ;;
esac

FILE_COUNT=$(count_source_files "$WORK_DIR" "$PLATFORM")

# Normalize to 0-10 score
# Formula: start at 10, deduct 2 per error, 0.5 per warning, 0.1 per info, floor at 0
SCORE=$(python3 -c "
w = int('${WARNINGS:-0}')
e = int('${ERRORS:-0}')
i = int('${INFOS:-0}')
score = max(0, round(10.0 - (e * 2.0) - (w * 0.5) - (i * 0.1), 2))
print(score)
" 2>/dev/null || echo "5")

# Determine which tool was used
TOOL_USED="fallback"
case "$PLATFORM" in
    ios) command -v swiftlint &>/dev/null && TOOL_USED="swiftlint" ;;
    android)
        command -v ktlint &>/dev/null && TOOL_USED="ktlint"
        command -v detekt &>/dev/null && TOOL_USED="detekt"
        ;;
    flutter) command -v dart &>/dev/null && [[ -f "$WORK_DIR/pubspec.yaml" ]] && TOOL_USED="dart_analyze" ;;
esac

# Output JSON
python3 -c "
import json
result = {
    'platform': '$PLATFORM',
    'tool': '$TOOL_USED',
    'errors': int('${ERRORS:-0}'),
    'warnings': int('${WARNINGS:-0}'),
    'infos': int('${INFOS:-0}'),
    'source_files': int('${FILE_COUNT:-0}'),
    'score': float('$SCORE')
}
print(json.dumps(result, indent=2))
"
