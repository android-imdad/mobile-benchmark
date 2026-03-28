#!/usr/bin/env bash
set -euo pipefail

# Standalone validation script for build + text validation
# Usage: validate.sh <platform> <work_dir> <build_command> <patterns_json> <expected_files_json>

PLATFORM="${1:-}"
WORK_DIR="${2:-}"
BUILD_COMMAND="${3:-}"
PATTERNS_JSON="${4:-[]}"
EXPECTED_FILES_JSON="${5:-[]}"

if [[ -z "$PLATFORM" || -z "$WORK_DIR" ]]; then
    echo "Usage: validate.sh <platform> <work_dir> [build_command] [patterns_json] [expected_files_json]"
    exit 1
fi

RESULT_BUILD=0
RESULT_PATTERNS=0
RESULT_FILES=0
BUILD_OUTPUT=""
PATTERNS_MATCHED=0
PATTERNS_TOTAL=0
FILES_FOUND=0
FILES_TOTAL=0

# File validation
if [[ "$EXPECTED_FILES_JSON" != "[]" ]]; then
    while IFS= read -r file_pattern; do
        FILES_TOTAL=$((FILES_TOTAL + 1))
        if compgen -G "$WORK_DIR/$file_pattern" > /dev/null 2>&1; then
            FILES_FOUND=$((FILES_FOUND + 1))
        fi
    done < <(echo "$EXPECTED_FILES_JSON" | python3 -c "import sys, json; [print(f) for f in json.loads(sys.stdin.read())]" 2>/dev/null)

    if [[ $FILES_TOTAL -gt 0 && $FILES_FOUND -eq $FILES_TOTAL ]]; then
        RESULT_FILES=1
    fi
fi

# Build validation
if [[ -n "$BUILD_COMMAND" ]]; then
    BUILD_OUTPUT=$(cd "$WORK_DIR" && eval "$BUILD_COMMAND" 2>&1) && RESULT_BUILD=1 || RESULT_BUILD=0
fi

# Pattern/text validation
if [[ "$PATTERNS_JSON" != "[]" ]]; then
    EXTENSIONS=""
    case "$PLATFORM" in
        ios) EXTENSIONS="--include=*.swift" ;;
        android) EXTENSIONS="--include=*.kt" ;;
        flutter) EXTENSIONS="--include=*.dart" ;;
    esac

    while IFS= read -r pattern; do
        PATTERNS_TOTAL=$((PATTERNS_TOTAL + 1))
        if grep -rq "$pattern" "$WORK_DIR/" $EXTENSIONS 2>/dev/null; then
            PATTERNS_MATCHED=$((PATTERNS_MATCHED + 1))
        fi
    done < <(echo "$PATTERNS_JSON" | python3 -c "import sys, json; [print(p) for p in json.loads(sys.stdin.read())]" 2>/dev/null)

    if [[ $PATTERNS_TOTAL -gt 0 ]]; then
        RESULT_PATTERNS=$(python3 -c "print(1 if $PATTERNS_MATCHED == $PATTERNS_TOTAL else 0)")
    fi
fi

# Output JSON result
python3 -c "
import json
result = {
    'build': {
        'success': bool($RESULT_BUILD),
        'output_excerpt': '''${BUILD_OUTPUT:0:500}'''[:500]
    },
    'patterns': {
        'matched': $PATTERNS_MATCHED,
        'total': $PATTERNS_TOTAL,
        'all_matched': bool($RESULT_PATTERNS)
    },
    'files': {
        'found': $FILES_FOUND,
        'total': $FILES_TOTAL,
        'all_found': bool($RESULT_FILES)
    }
}
print(json.dumps(result, indent=2))
"
