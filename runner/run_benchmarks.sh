#!/usr/bin/env bash
set -euo pipefail

# macOS compatibility: use gtimeout if timeout is not available
if ! command -v timeout &>/dev/null; then
    if command -v gtimeout &>/dev/null; then
        timeout() { gtimeout "$@"; }
    else
        echo "Error: 'timeout' (or 'gtimeout' from coreutils) is required."
        echo "Install with: brew install coreutils"
        exit 1
    fi
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BENCHMARKS_DIR="$PROJECT_ROOT/benchmarks"
TEMPLATES_DIR="$PROJECT_ROOT/templates"
VALIDATE_SCRIPT="$SCRIPT_DIR/validate.sh"
REPORT_SCRIPT="$SCRIPT_DIR/generate_report.py"
MODEL_SELECTOR="$SCRIPT_DIR/model_selector.sh"

# Defaults
MODELS=""
PLATFORMS="ios,android,flutter"
DIFFICULTIES="easy,medium,hard"
TIMEOUT=300
PARALLEL=1
OUTPUT_DIR=""
INTERACTIVE=false
JUDGE_MODEL=""
SKIP_JUDGE=false
LLM_JUDGE_SCRIPT="$SCRIPT_DIR/llm_judge.py"
STATIC_ANALYZE_SCRIPT="$SCRIPT_DIR/static_analyze.sh"

usage() {
    cat <<EOF
Mobile Development Benchmark Suite
===================================

Usage: $0 [OPTIONS]

Options:
  --models       Comma-separated list of model IDs (REQUIRED unless --interactive)
                   e.g. "claude-sonnet-4-5-20250929,gpt-5.1-codex"
  --interactive  Launch interactive model selector
  --platforms    Comma-separated platforms (default: ios,android,flutter)
  --difficulty   Comma-separated difficulty levels (default: easy,medium,hard)
  --timeout      Max seconds per task (default: 300)
  --parallel     Number of parallel tasks (default: 1)
  --output       Custom output directory (default: results/<timestamp>)
  --judge-model  Model ID for LLM-as-Judge evaluation (default: same as invoking droid session)
  --skip-judge   Skip LLM judge evaluation (faster, deterministic scoring only)
  --help         Show this help

Examples:
  $0 --models "claude-sonnet-4-5-20250929"
  $0 --models "claude-sonnet-4-5-20250929,gpt-5.1-codex" --platforms "ios" --difficulty "easy"
  $0 --models "claude-sonnet-4-5-20250929,gpt-5.1-codex,gemini-3-pro-preview" --parallel 2
  $0 --interactive

EOF
    exit 0
}

log() { echo "[$(date '+%H:%M:%S')] $*"; }
log_success() { echo "[$(date '+%H:%M:%S')] ✓ $*"; }
log_error() { echo "[$(date '+%H:%M:%S')] ✗ $*"; }
log_info() { echo "[$(date '+%H:%M:%S')] → $*"; }

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --models) MODELS="$2"; shift 2 ;;
        --interactive) INTERACTIVE=true; shift ;;
        --platforms) PLATFORMS="$2"; shift 2 ;;
        --difficulty) DIFFICULTIES="$2"; shift 2 ;;
        --timeout) TIMEOUT="$2"; shift 2 ;;
        --parallel) PARALLEL="$2"; shift 2 ;;
        --output) OUTPUT_DIR="$2"; shift 2 ;;
        --judge-model) JUDGE_MODEL="$2"; shift 2 ;;
        --skip-judge) SKIP_JUDGE=true; shift ;;
        --help) usage ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

if [[ -z "$MODELS" ]] && [[ "$INTERACTIVE" == "true" ]]; then
    echo "Launching interactive model selector..."
    echo ""
    if [[ -x "$MODEL_SELECTOR" ]]; then
        SELECTED_MODELS=$("$MODEL_SELECTOR")
        if [[ -z "$SELECTED_MODELS" ]]; then
            echo "Error: No models selected"
            exit 1
        fi
        MODELS="$SELECTED_MODELS"
    else
        echo "Error: Model selector script not found or not executable: $MODEL_SELECTOR"
        exit 1
    fi
fi

if [[ -z "$MODELS" ]]; then
    echo "Error: --models is required (or use --interactive to select models)"
    echo ""
    usage
fi

# Setup output directory
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
if [[ -z "$OUTPUT_DIR" ]]; then
    OUTPUT_DIR="$PROJECT_ROOT/results/$TIMESTAMP"
fi
RAW_DIR="$OUTPUT_DIR/raw"
JUDGE_MANIFEST_DIR="$OUTPUT_DIR/judge_manifest"
JUDGE_RESULTS_DIR="$OUTPUT_DIR/judge_results"
mkdir -p "$RAW_DIR" "$JUDGE_MANIFEST_DIR" "$JUDGE_RESULTS_DIR"

# Create latest symlink
ln -sfn "$OUTPUT_DIR" "$PROJECT_ROOT/results/latest"

IFS=',' read -ra MODEL_LIST <<< "$MODELS"
IFS=',' read -ra PLATFORM_LIST <<< "$PLATFORMS"
IFS=',' read -ra DIFFICULTY_LIST <<< "$DIFFICULTIES"

# Count total tasks
TOTAL_TASKS=0
for platform in "${PLATFORM_LIST[@]}"; do
    for difficulty in "${DIFFICULTY_LIST[@]}"; do
        task_dir="$BENCHMARKS_DIR/$platform/$difficulty"
        if [[ -d "$task_dir" ]]; then
            task_count=$(find "$task_dir" -name "*.md" | wc -l | tr -d ' ')
            TOTAL_TASKS=$((TOTAL_TASKS + task_count * ${#MODEL_LIST[@]}))
        fi
    done
done

log "=== Mobile Development Benchmark Suite ==="
log "Models:       ${MODEL_LIST[*]}"
log "Platforms:    ${PLATFORM_LIST[*]}"
log "Difficulties: ${DIFFICULTY_LIST[*]}"
log "Total tasks:  $TOTAL_TASKS"
log "Output:       $OUTPUT_DIR"
if [[ "$SKIP_JUDGE" == "false" ]]; then
    if [[ -z "$JUDGE_MODEL" ]]; then
        JUDGE_MODEL="custom:claude-opus-4-6-thinking-10000"
        log "Judge model:  $JUDGE_MODEL (default)"
    else
        log "Judge model:  $JUDGE_MODEL"
    fi
    log "Evaluation:   Deterministic + LLM Judge + Static Analysis"
else
    log "Evaluation:   Deterministic only (judge skipped)"
fi
log "=========================================="
echo ""

COMPLETED=0
PASSED=0
FAILED=0

run_single_task() {
    set +e  # Disable errexit inside task to prevent script exit on individual failures
    local model="$1"
    local task_file="$2"
    local platform="$3"
    local difficulty="$4"
    local task_name
    task_name="$(basename "$task_file" .md)"

    local task_id="${platform}_${difficulty}_${task_name}"
    local model_safe
    model_safe="$(echo "$model" | tr '/' '_' | tr ' ' '_')"
    local result_file="$RAW_DIR/${model_safe}__${task_id}.json"
    local work_dir
    work_dir="$(mktemp -d "/tmp/benchmark_${task_id}_XXXXXX")"

    log_info "[$model] $platform/$difficulty/$task_name"

    # Copy template project
    local template_dir=""
    case "$platform" in
        ios) template_dir="$TEMPLATES_DIR/ios_project" ;;
        android) template_dir="$TEMPLATES_DIR/android_project" ;;
        flutter) template_dir="$TEMPLATES_DIR/flutter_project" ;;
    esac

    if [[ -d "$template_dir" ]]; then
        cp -R "$template_dir/." "$work_dir/"
    fi

    # Extract task metadata from frontmatter
    local max_score timeout_val patterns_json expected_files_json build_command validation_type category
    max_score=$(awk '/^---$/{n++; next} n==1 && /^max_score:/{print $2}' "$task_file")
    timeout_val=$(awk '/^---$/{n++; next} n==1 && /^timeout:/{print $2}' "$task_file")
    category=$(awk '/^---$/{n++; next} n==1 && /^category:/{print $2}' "$task_file")
    validation_type=$(awk '/^---$/{n++; next} n==1 && /^  type:/{print $2}' "$task_file")

    max_score=${max_score:-10}
    timeout_val=${timeout_val:-$TIMEOUT}
    category=${category:-generate}
    validation_type=${validation_type:-both}

    # Extract patterns as JSON array
    patterns_json=$(awk '
        /^---$/ { n++; next }
        n==1 && /^  patterns:/ { in_patterns=1; next }
        n==1 && in_patterns && /^    - / { gsub(/^    - "?/, ""); gsub(/"$/, ""); printf "%s\n", $0; next }
        n==1 && in_patterns && !/^    / { in_patterns=0 }
    ' "$task_file" | python3 -c "
import sys, json
lines = [l.strip() for l in sys.stdin if l.strip()]
print(json.dumps(lines))
" 2>/dev/null || echo "[]")

    # Extract expected files
    expected_files_json=$(awk '
        /^---$/ { n++; next }
        n==1 && /^  expected_files:/ { in_files=1; next }
        n==1 && in_files && /^    - / { gsub(/^    - "?/, ""); gsub(/"$/, ""); printf "%s\n", $0; next }
        n==1 && in_files && !/^    / { in_files=0 }
    ' "$task_file" | python3 -c "
import sys, json
lines = [l.strip() for l in sys.stdin if l.strip()]
print(json.dumps(lines))
" 2>/dev/null || echo "[]")

    # Extract build command
    build_command=$(awk '
        /^---$/ { n++; next }
        n==1 && /^  build_command:/ { gsub(/^  build_command: "?/, ""); gsub(/"$/, ""); print; exit }
    ' "$task_file")

    # Extract the prompt (everything after second ---)
    local prompt
    prompt=$(awk '/^---$/{n++; next} n>=2{print}' "$task_file")

    # Run droid exec
    local start_time end_time duration_ms droid_exit_code=0
    local droid_output_file="$work_dir/_droid_output.json"
    start_time=$(python3 -c "import time; print(int(time.time()*1000))")

    # Create a prompt file for droid exec
    local prompt_file="$work_dir/_prompt.md"
    echo "$prompt" > "$prompt_file"

    timeout "${timeout_val}" droid exec \
        -m "$model" \
        --auto medium \
        --output-format json \
        --cwd "$work_dir" \
        -f "$prompt_file" \
        > "$droid_output_file" 2>/dev/null || droid_exit_code=$?

    end_time=$(python3 -c "import time; print(int(time.time()*1000))")
    duration_ms=$((end_time - start_time))

    # Parse droid output
    local droid_success="false"
    local droid_result=""
    if [[ -f "$droid_output_file" ]] && [[ -s "$droid_output_file" ]]; then
        droid_success=$(python3 -c "
import json, sys
try:
    data = json.load(open('$droid_output_file'))
    print('true' if not data.get('is_error', True) else 'false')
except: print('false')
" 2>/dev/null || echo "false")
        droid_result=$(python3 -c "
import json, sys
try:
    data = json.load(open('$droid_output_file'))
    r = data.get('result', '')
    print(r[:500] if r else '')
except: print('')
" 2>/dev/null || echo "")
    fi

    # Run validation
    local build_score=0 pattern_score=0 file_score=0 completion_score=0 speed_score=0
    local build_output="" pattern_results="" total_score=0

    # Check if droid produced any output at all
    if [[ "$droid_success" == "true" ]] || [[ "$droid_exit_code" -eq 0 ]]; then
        completion_score=3
    fi

    # Check expected files exist
    if [[ "$expected_files_json" != "[]" ]]; then
        local files_found=0 files_total=0
        while IFS= read -r file_pattern; do
            files_total=$((files_total + 1))
            # Handle glob patterns
            if compgen -G "$work_dir/$file_pattern" > /dev/null 2>&1; then
                files_found=$((files_found + 1))
            fi
        done < <(echo "$expected_files_json" | python3 -c "import sys, json; [print(f) for f in json.loads(sys.stdin.read())]" 2>/dev/null)

        if [[ $files_total -gt 0 ]]; then
            file_score=$(python3 -c "print(round(1.0 * $files_found / $files_total, 2))")
        fi
    else
        file_score=1
    fi

    # Build validation
    if [[ -n "$build_command" ]] && [[ "$validation_type" == "build" || "$validation_type" == "both" ]]; then
        build_output=$(cd "$work_dir" && eval "$build_command" 2>&1) && build_score=3 || build_score=0
    fi

    # Pattern/text validation
    if [[ "$patterns_json" != "[]" ]] && [[ "$validation_type" == "pattern" || "$validation_type" == "both" ]]; then
        local patterns_matched=0 patterns_total=0
        while IFS= read -r pattern; do
            patterns_total=$((patterns_total + 1))
            if grep -rq "$pattern" "$work_dir/" --include="*.swift" --include="*.kt" --include="*.dart" 2>/dev/null; then
                patterns_matched=$((patterns_matched + 1))
            fi
        done < <(echo "$patterns_json" | python3 -c "import sys, json; [print(p) for p in json.loads(sys.stdin.read())]" 2>/dev/null)

        if [[ $patterns_total -gt 0 ]]; then
            pattern_score=$(python3 -c "print(round(2.0 * $patterns_matched / $patterns_total, 2))")
        fi
        pattern_results="{\"matched\": $patterns_matched, \"total\": $patterns_total}"
    else
        pattern_score=2
        pattern_results="{\"matched\": 0, \"total\": 0}"
    fi

    # Speed bonus: under half timeout
    local half_timeout=$((timeout_val * 1000 / 2))
    if [[ $duration_ms -lt $half_timeout ]] && [[ "$completion_score" -gt 0 ]]; then
        speed_score=1
    fi

    # Total score (max 10): completion(3) + build(3) + patterns(2) + files(1 mapped from 0-1) + speed(1)
    total_score=$(python3 -c "print(round($completion_score + $build_score + $pattern_score + $file_score + $speed_score, 2))")

    # --- Save task data for batch LLM-as-Judge (deferred to end) ---
    local judge_avg=0
    local judge_success="false"

    if [[ "$SKIP_JUDGE" == "false" ]] && [[ -n "$JUDGE_MODEL" ]]; then
        local manifest_entry_file="$JUDGE_MANIFEST_DIR/${model_safe}__${task_id}.json"
        python3 -c "
import json, os, sys
sys.path.insert(0, '$SCRIPT_DIR')
from llm_judge import collect_generated_code

with open('$task_file') as f:
    content = f.read()
parts = content.split('---')
task_prompt = '---'.join(parts[2:]).strip() if len(parts) >= 3 else content

generated_code = collect_generated_code('$work_dir', '$platform')

entry = {
    'task_id': '${model_safe}__${task_id}',
    'platform': '$platform',
    'task_prompt': task_prompt,
    'generated_code': generated_code
}
with open('$manifest_entry_file', 'w') as f:
    json.dump(entry, f)
" 2>/dev/null || true
    fi

    # --- Static analysis ---
    local static_result_file="$work_dir/_static_result.json"
    local static_score=0

    if [[ -x "$STATIC_ANALYZE_SCRIPT" ]]; then
        bash "$STATIC_ANALYZE_SCRIPT" "$platform" "$work_dir" > "$static_result_file" 2>/dev/null || echo '{"score": 0}' > "$static_result_file"
        static_score=$(python3 -c "
import json
try:
    data = json.load(open('$static_result_file'))
    print(data.get('score', 0))
except: print(0)
" 2>/dev/null || echo "0")
    fi

    # --- Composite score (preliminary, without judge - will be updated after batch judge) ---
    local composite_score
    # No judge: deterministic(75%) + static(25%) — batch judge merges final scores later
    composite_score=$(python3 -c "
det = $total_score
static = $static_score
composite = round(det * 0.75 + static * 0.25, 2)
print(composite)
" 2>/dev/null || echo "$total_score")

    # Write result JSON using file-based merging (avoids shell escaping issues)
    python3 -c "
import json, os

static_data = {}
static_file = '$static_result_file'
if os.path.isfile(static_file):
    try:
        static_data = json.load(open(static_file))
    except: pass

result = {
    'model': '$model',
    'platform': '$platform',
    'difficulty': '$difficulty',
    'task': '$task_name',
    'category': '$category',
    'task_id': '$task_id',
    'duration_ms': $duration_ms,
    'timeout': $timeout_val,
    'max_score': $max_score,
    'scores': {
        'total': $total_score,
        'composite': $composite_score,
        'completion': $completion_score,
        'build': $build_score,
        'patterns': $pattern_score,
        'files': $file_score,
        'speed': $speed_score
    },
    'llm_judge': {
        'model': '$JUDGE_MODEL' if '$SKIP_JUDGE' == 'false' else None,
        'success': False,
        'average_score': 0,
        'dimensions': {}
    },
    'static_analysis': static_data,
    'validation': {
        'build_success': $build_score > 0,
        'patterns': $pattern_results,
        'droid_success': '$droid_success' == 'true',
        'droid_exit_code': $droid_exit_code
    },
    'timestamp': '$(date -u '+%Y-%m-%dT%H:%M:%SZ')'
}
with open('$result_file', 'w') as f:
    json.dump(result, f, indent=2, default=str)
" 2>/dev/null

    # Log result (preliminary — judge scores merged after batch)
    local display_score="$total_score"
    local score_label="deterministic"

    if (( $(echo "$display_score >= 7" | bc -l 2>/dev/null || echo 0) )); then
        log_success "[$model] $task_id: $display_score/$max_score $score_label (${duration_ms}ms)"
        PASSED=$((PASSED + 1))
    else
        log_error "[$model] $task_id: $display_score/$max_score $score_label (${duration_ms}ms)"
        FAILED=$((FAILED + 1))
    fi
    COMPLETED=$((COMPLETED + 1))

    # Cleanup
    rm -rf "$work_dir"
    set -e  # Re-enable errexit
}

# Main execution loop
for model in "${MODEL_LIST[@]}"; do
    model=$(echo "$model" | xargs) # trim whitespace
    log "--- Running benchmarks with model: $model ---"
    echo ""

    for platform in "${PLATFORM_LIST[@]}"; do
        platform=$(echo "$platform" | xargs)
        for difficulty in "${DIFFICULTY_LIST[@]}"; do
            difficulty=$(echo "$difficulty" | xargs)
            task_dir="$BENCHMARKS_DIR/$platform/$difficulty"

            if [[ ! -d "$task_dir" ]]; then
                log "Skipping $platform/$difficulty (no tasks found)"
                continue
            fi

            for task_file in "$task_dir"/*.md; do
                [[ -f "$task_file" ]] || continue
                run_single_task "$model" "$task_file" "$platform" "$difficulty"
            done
        done
    done
    echo ""
done

# --- Batch LLM-as-Judge: single request for all tasks ---
if [[ "$SKIP_JUDGE" == "false" ]] && [[ -n "$JUDGE_MODEL" ]]; then
    MANIFEST_FILES=("$JUDGE_MANIFEST_DIR"/*.json)
    if [[ -f "${MANIFEST_FILES[0]:-}" ]]; then
        log "=== Running Batch LLM Judge (single request for all tasks) ==="

        # Combine manifest entries into a single JSON array
        MANIFEST_FILE="$OUTPUT_DIR/judge_manifest.json"
        python3 -c "
import json, glob, os
entries = []
for f in sorted(glob.glob('$JUDGE_MANIFEST_DIR/*.json')):
    try:
        entries.append(json.load(open(f)))
    except: pass
with open('$MANIFEST_FILE', 'w') as out:
    json.dump(entries, out)
print(f'Manifest: {len(entries)} tasks')
"
        # Run batch judge (single droid exec call)
        python3 "$LLM_JUDGE_SCRIPT" batch "$JUDGE_MODEL" "$MANIFEST_FILE" "$JUDGE_RESULTS_DIR" 2>/dev/null || true

        # Merge judge results back into raw result files
        log "Merging judge scores into results..."
        python3 -c "
import json, glob, os

judge_dir = '$JUDGE_RESULTS_DIR'
raw_dir = '$RAW_DIR'

for raw_file in glob.glob(os.path.join(raw_dir, '*.json')):
    try:
        with open(raw_file) as f:
            result = json.load(f)

        basename = os.path.basename(raw_file).replace('.json', '')
        judge_file = os.path.join(judge_dir, basename + '.json')

        if not os.path.isfile(judge_file):
            continue

        with open(judge_file) as f:
            judge_data = json.load(f)

        if not judge_data.get('success', False):
            continue

        judge_avg = judge_data.get('average_score', 0)
        det_score = result['scores']['total']
        static_score = result.get('static_analysis', {}).get('score', 0)
        composite = round(det_score * 0.40 + judge_avg * 0.45 + static_score * 0.15, 2)

        result['scores']['composite'] = composite
        result['llm_judge'] = {
            'model': '$JUDGE_MODEL',
            'success': True,
            'average_score': judge_avg,
            'dimensions': judge_data.get('scores', {})
        }

        with open(raw_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)

    except Exception as e:
        print(f'Warning: failed to merge {raw_file}: {e}')

print('Judge scores merged.')
" 2>/dev/null || true
        log_success "Batch judge complete"
    fi
fi

# Generate report
log "=== Generating HTML Report ==="
python3 "$REPORT_SCRIPT" "$RAW_DIR" "$OUTPUT_DIR/report.html"

echo ""
log "=== Benchmark Complete ==="
log "Completed: $COMPLETED | Passed (>=7): $PASSED | Below threshold: $FAILED"
log "Report: $OUTPUT_DIR/report.html"
log "Raw results: $RAW_DIR/"
echo ""
log "Open report: open $OUTPUT_DIR/report.html"
