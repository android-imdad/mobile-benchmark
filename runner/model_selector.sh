#!/usr/bin/env bash

# Interactive Model Selector for Benchmark Suite
# Dynamically fetches available models from droid CLI and custom models from settings
# Compatible with bash 3.2+

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Temp file for custom model descriptions (bash 3.2 compatible - no associative arrays)
CUSTOM_MODEL_DESCS_FILE="$(mktemp /tmp/custom_model_descs_XXXXXX)"
trap "rm -f '$CUSTOM_MODEL_DESCS_FILE'" EXIT

# Fetch built-in models from droid CLI
fetch_builtin_models() {
    droid exec --help 2>&1 | grep -E "^\s+(claude-|gpt-|gemini-|glm-|kimi-|minimax-|custom:)" | awk '{print $1}' | sort
}

# Fetch custom models from ~/.factory/settings.json
# Writes to temp file: model_id|description
# Uses 'model' field as key since droid exec --help shows that
fetch_custom_models() {
    local settings_file="$HOME/.factory/settings.json"
    if [[ ! -f "$settings_file" ]]; then
        echo ""
        return
    fi

    # Extract custom models using python3 (handles JSON robustly)
    python3 -c "
import json, os, sys, re

settings_path = os.path.expanduser('~/.factory/settings.json')
try:
    with open(settings_path) as f:
        settings = json.load(f)

    seen = set()
    custom_models = settings.get('customModels', [])
    for model in custom_models:
        model_field = model.get('model', '')
        model_id = model.get('id', '')
        display_name = model.get('displayName', model_id)
        base_url = model.get('baseUrl', '')
        # Skip entries without a valid model
        if not model_field:
            continue
        # Shorten localhost URLs for display
        if 'localhost' in base_url:
            base_url = 'localhost'
        else:
            match = re.search(r'https?://([^/]+)', base_url)
            if match:
                base_url = match.group(1)
            else:
                base_url = ''
        desc = f'{display_name} ({base_url})'
        # Use model field as key since droid exec --help shows that
        key = f'custom:{model_field}'
        # Skip duplicates (keep first)
        if key in seen:
            continue
        seen.add(key)
        print(f'{key}|{desc}')
except Exception as e:
    sys.exit(0)
" 2>/dev/null || true
}

# Load custom model descriptions into temp file
load_custom_model_descs() {
    local custom_output
    custom_output=$(fetch_custom_models)
    echo "$custom_output" > "$CUSTOM_MODEL_DESCS_FILE"
}

# Model descriptions for built-in models (model_id|description format)
MODEL_DESCS=(
    "claude-opus-4-5-20251101|Claude Opus 4.5"
    "claude-opus-4-6|Claude Opus 4.6 - Best depth and safety"
    "claude-opus-4-6-fast|Claude Opus 4.6 Fast - Fast mode"
    "claude-sonnet-4-5-20250929|Claude Sonnet 4.5"
    "claude-sonnet-4-6|Claude Sonnet 4.6 - Strong daily driver"
    "claude-haiku-4-5-20251001|Claude Haiku 4.5 - Fast, cost-efficient"
    "gpt-5.2|GPT-5.2 - Latest OpenAI"
    "gpt-5.2-codex|GPT-5.2-Codex - OpenAI coding model"
    "gpt-5.4|GPT-5.4 - Latest with 922K context"
    "gpt-5.4-mini|GPT-5.4 Mini"
    "gpt-5.3-codex|GPT-5.3-Codex - Coding model"
    "gemini-3.1-pro-preview|Gemini 3.1 Pro - Strong structured outputs"
    "gemini-3-flash-preview|Gemini 3 Flash - Fast, cheap"
    "glm-4.7|Droid Core (GLM-4.7) - Open-source"
    "glm-5|Droid Core (GLM-5) - Open-source"
    "kimi-k2.5|Droid Core (Kimi K2.5) - With image support"
    "minimax-m2.5|Droid Core (MiniMax M2.5) - Cheapest 0.12x"
)

get_model_desc() {
    local model_id="$1"
    # Restore pipe escapes
    model_id="${model_id//_PIPE_/|}"
    # Check built-in models first
    for entry in "${MODEL_DESCS[@]}"; do
        if [[ "$entry" == "$model_id|"* ]]; then
            echo "${entry#*|}"
            return
        fi
    done
    # Check custom models from temp file
    if [[ -f "$CUSTOM_MODEL_DESCS_FILE" ]]; then
        local desc
        desc=$(grep "^${model_id}|" "$CUSTOM_MODEL_DESCS_FILE" 2>/dev/null | head -1 | cut -d'|' -f2-)
        if [[ -n "$desc" ]]; then
            echo "$desc"
            return
        fi
    fi
    echo "$model_id"
}

interactive_select() {
    local title="$1"
    shift
    local -a options=("$@")
    local num_options=${#options[@]}
    
    echo ""
    echo "=========================================="
    echo " $title"
    echo "=========================================="
    echo ""
    
    # Display options with numbers
    local i=0
    for opt in "${options[@]}"; do
        local desc=$(get_model_desc "$opt")
        echo "  [$((i+1))] $desc"
        i=$((i+1))
    done
    echo "  [0] Done selecting"
    echo ""
    
    # Initialize selected array
    selected=""
    local selection_count=0
    local choice=""
    
    while true; do
        echo -n "Enter number to toggle (0 when done): "
        read -r choice
        
        if [[ "$choice" == "0" ]]; then
            break
        elif [[ "$choice" =~ ^[0-9]+$ ]] && [[ "$choice" -ge 1 ]] && [[ "$choice" -le "$num_options" ]]; then
            local idx=$((choice - 1))
            local model_id="${options[$idx]}"
            
            # Toggle selection - use sed-like replacement in string
            if [[ "$selected" == *"$model_id"* ]]; then
                # Deselect - remove from string
                selected=$(echo "$selected" | tr ' ' '\n' | grep -v "^$model_id$" | tr '\n' ' ' | sed 's/ $//')
                selection_count=$((selection_count - 1))
                echo "  - Deselected: $model_id"
            else
                # Select - add to string
                if [[ -z "$selected" ]]; then
                    selected="$model_id"
                else
                    selected="$selected $model_id"
                fi
                selection_count=$((selection_count + 1))
                echo "  + Selected: $model_id"
            fi
        else
            echo "  Invalid choice. Enter a number between 0 and $num_options"
        fi
    done
    
    # Return selected models
    if [[ -z "$selected" ]]; then
        echo ""
        echo "No models selected."
        exit 0
    fi
    
    echo ""
    echo "Selected models: $selected"
    # Convert spaces to comma
    echo "$selected" | tr ' ' ','
}

# Main
echo ""
echo "=========================================="
echo "   Model Selector - Benchmark Suite"
echo "=========================================="
echo ""

# Fetch built-in models
echo "Fetching built-in models from droid CLI..."
builtin_models_output=$(fetch_builtin_models)
if [[ -z "$builtin_models_output" ]]; then
    echo "Error: Could not fetch models from droid CLI"
    exit 1
fi

# Fetch and load custom models
echo "Loading custom models from ~/.factory/settings.json..."
load_custom_model_descs

custom_count=0
if [[ -f "$CUSTOM_MODEL_DESCS_FILE" ]]; then
    custom_count=$(wc -l < "$CUSTOM_MODEL_DESCS_FILE" 2>/dev/null | tr -d ' ' || echo 0)
fi
if [[ $custom_count -gt 0 ]]; then
    echo "  Found $custom_count custom model(s)"
fi
echo ""

# Combine built-in and custom models
all_models_output="$builtin_models_output"
if [[ -n "$custom_models_output" ]]; then
    all_models_output="$all_models_output"$'\n'"$custom_models_output"
fi

# Deduplicate and sort (compatible with bash 3.2)
IFS=$'\n'
sorted_models=($(echo "$all_models_output" | sort | uniq))
unset IFS

# Run interactive selection
selected=$(interactive_select "Select Models for Benchmark" "${sorted_models[@]}")

echo ""
echo "Final selection: $selected"
echo ""

# Output the selection (this is what run_benchmarks.sh captures)
echo "$selected"
