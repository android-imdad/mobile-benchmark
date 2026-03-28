#!/usr/bin/env python3
"""
LLM-as-Judge evaluator for benchmark tasks.
Supports both single-task and batch mode (one judge request for all tasks).
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

DIMENSIONS = [
    ("correctness", "Does the code correctly solve the task as specified? Consider logic, output, and edge cases."),
    ("code_quality", "Is the code clean, well-structured, and idiomatic for the platform (Swift/Kotlin/Dart)?"),
    ("best_practices", "Does it follow platform best practices (SwiftUI patterns, Compose conventions, Flutter widget patterns)?"),
    ("completeness", "Does the solution fully address all requirements in the prompt, including edge cases?"),
    ("readability", "Is the code easy to read and understand? Good naming, formatting, and logical flow?"),
    ("error_handling", "Does the code handle errors, invalid inputs, and edge cases gracefully?"),
    ("performance", "Is the code efficient? No unnecessary allocations, recomputations, or O(n^2) where O(n) suffices?"),
    ("architecture", "Is the code well-architected? Separation of concerns, testability, extensibility?"),
]

JUDGE_PROMPT_TEMPLATE = """You are an expert mobile development code reviewer acting as an impartial judge.

## Task Prompt
{task_prompt}

## Platform
{platform}

## Generated Code
{generated_code}

## Instructions
Rate the generated code on EACH of the following dimensions from 1-10 (1=terrible, 5=acceptable, 10=exceptional).
Provide a brief justification (1-2 sentences max) for each score.

Respond ONLY with valid JSON in this exact format, nothing else:
{{
  "correctness": {{"score": <1-10>, "reason": "<brief justification>"}},
  "code_quality": {{"score": <1-10>, "reason": "<brief justification>"}},
  "best_practices": {{"score": <1-10>, "reason": "<brief justification>"}},
  "completeness": {{"score": <1-10>, "reason": "<brief justification>"}},
  "readability": {{"score": <1-10>, "reason": "<brief justification>"}},
  "error_handling": {{"score": <1-10>, "reason": "<brief justification>"}},
  "performance": {{"score": <1-10>, "reason": "<brief justification>"}},
  "architecture": {{"score": <1-10>, "reason": "<brief justification>"}}
}}
"""

BATCH_JUDGE_PROMPT_TEMPLATE = """You are an expert mobile development code reviewer acting as an impartial judge.
You will evaluate multiple tasks in a single pass. Each task has a unique ID, a prompt, platform, and generated code.

Rate EACH task's code on these dimensions from 1-10 (1=terrible, 5=acceptable, 10=exceptional):
correctness, code_quality, best_practices, completeness, readability, error_handling, performance, architecture.

Provide a brief justification (1-2 sentences max) for each score.

{task_sections}

## Instructions
Respond ONLY with valid JSON: an object keyed by task_id, each containing dimension scores.
Example format:
{{
  "task_id_1": {{
    "correctness": {{"score": 7, "reason": "..."}},
    "code_quality": {{"score": 8, "reason": "..."}},
    "best_practices": {{"score": 6, "reason": "..."}},
    "completeness": {{"score": 7, "reason": "..."}},
    "readability": {{"score": 8, "reason": "..."}},
    "error_handling": {{"score": 5, "reason": "..."}},
    "performance": {{"score": 7, "reason": "..."}},
    "architecture": {{"score": 6, "reason": "..."}}
  }},
  "task_id_2": {{ ... }}
}}
"""


def collect_generated_code(work_dir: str, platform: str) -> str:
    """Collect all generated source files from the work directory."""
    extensions = {
        "ios": [".swift"],
        "android": [".kt", ".java"],
        "flutter": [".dart"],
    }
    exts = extensions.get(platform, [".swift", ".kt", ".dart"])
    code_parts = []

    for root, _, files in os.walk(work_dir):
        for fname in sorted(files):
            if any(fname.endswith(ext) for ext in exts):
                fpath = os.path.join(root, fname)
                rel_path = os.path.relpath(fpath, work_dir)
                if rel_path.startswith("_"):
                    continue
                try:
                    with open(fpath) as f:
                        content = f.read()
                    if content.strip():
                        code_parts.append(f"// --- {rel_path} ---\n{content}")
                except IOError:
                    continue

    return "\n\n".join(code_parts) if code_parts else ""


def _empty_result(error: str) -> dict:
    return {
        "success": False,
        "error": error,
        "scores": {dim: {"score": 0, "reason": error} for dim, _ in DIMENSIONS},
        "average_score": 0.0,
    }


def _validate_scores(scores: dict) -> dict:
    """Validate and normalize a single task's dimension scores."""
    validated = {}
    total = 0
    count = 0
    for dim, _ in DIMENSIONS:
        if dim in scores and isinstance(scores[dim], dict):
            s = min(10, max(0, int(scores[dim].get("score", 0))))
            r = str(scores[dim].get("reason", ""))[:200]
            validated[dim] = {"score": s, "reason": r}
            total += s
            count += 1
        else:
            validated[dim] = {"score": 0, "reason": "Not evaluated"}
    avg = round(total / count, 2) if count > 0 else 0.0
    return {"success": True, "scores": validated, "average_score": avg}


def _call_droid(judge_model: str, prompt: str, timeout: int) -> str:
    """Call droid exec with a prompt and return the raw judge text response."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(prompt)
        prompt_file = f.name

    try:
        result = subprocess.run(
            ["droid", "exec", "-m", judge_model, "--output-format", "json", "-f", prompt_file],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            raise RuntimeError(f"droid exec failed with exit code {result.returncode}")

        try:
            droid_output = json.loads(result.stdout)
            judge_text = droid_output.get("result", "")
        except json.JSONDecodeError:
            judge_text = result.stdout

        return judge_text
    finally:
        os.unlink(prompt_file)


def _extract_json(text: str) -> str:
    """Extract JSON from a response that may be wrapped in markdown code fences."""
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        text = text[start:end]
    return text


def run_judge(judge_model: str, task_prompt: str, generated_code: str, platform: str, timeout: int = 120) -> dict:
    """Run the LLM judge for a single task."""
    if not generated_code.strip():
        return _empty_result("No generated code to evaluate")

    prompt = JUDGE_PROMPT_TEMPLATE.format(
        task_prompt=task_prompt.strip(),
        platform=platform,
        generated_code=generated_code.strip(),
    )

    try:
        judge_text = _call_droid(judge_model, prompt, timeout)
        scores = json.loads(_extract_json(judge_text))
        return _validate_scores(scores)
    except subprocess.TimeoutExpired:
        return _empty_result("Judge timed out")
    except (json.JSONDecodeError, ValueError, KeyError, RuntimeError) as e:
        return _empty_result(f"Failed to parse judge response: {e}")


def run_batch_judge(judge_model: str, manifest_path: str, timeout: int = 300) -> dict:
    """Evaluate all tasks in a single judge request.

    The manifest is a JSON file with a list of entries:
      [{"task_id": "...", "platform": "...", "task_prompt": "...", "generated_code": "..."}, ...]

    Returns a dict keyed by task_id, each value being the same structure as run_judge output.
    """
    with open(manifest_path) as f:
        tasks = json.load(f)

    # Build per-task results for tasks with no code
    results = {}
    valid_tasks = []
    for task in tasks:
        tid = task["task_id"]
        code = task.get("generated_code", "").strip()
        if not code:
            results[tid] = _empty_result("No generated code to evaluate")
        else:
            valid_tasks.append(task)

    if not valid_tasks:
        return results

    # Build a single prompt containing all tasks
    sections = []
    for i, task in enumerate(valid_tasks, 1):
        sections.append(
            f"---\n### Task {i}: `{task['task_id']}`\n"
            f"**Platform:** {task['platform']}\n\n"
            f"**Task Prompt:**\n{task['task_prompt'].strip()}\n\n"
            f"**Generated Code:**\n```\n{task['generated_code'].strip()}\n```\n"
        )

    prompt = BATCH_JUDGE_PROMPT_TEMPLATE.format(task_sections="\n".join(sections))

    try:
        judge_text = _call_droid(judge_model, prompt, timeout)
        all_scores = json.loads(_extract_json(judge_text))

        for task in valid_tasks:
            tid = task["task_id"]
            if tid in all_scores and isinstance(all_scores[tid], dict):
                results[tid] = _validate_scores(all_scores[tid])
            else:
                results[tid] = _empty_result("Task not found in judge response")

    except subprocess.TimeoutExpired:
        for task in valid_tasks:
            results[task["task_id"]] = _empty_result("Judge timed out")
    except (json.JSONDecodeError, ValueError, KeyError, RuntimeError) as e:
        for task in valid_tasks:
            results[task["task_id"]] = _empty_result(f"Failed to parse judge response: {e}")

    return results


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "batch":
        # Batch mode: llm_judge.py batch <judge_model> <manifest_json> <output_dir>
        if len(sys.argv) < 5:
            print("Usage: llm_judge.py batch <judge_model> <manifest_json> <output_dir>")
            sys.exit(1)
        judge_model = sys.argv[2]
        manifest_path = sys.argv[3]
        output_dir = sys.argv[4]
        os.makedirs(output_dir, exist_ok=True)

        results = run_batch_judge(judge_model, manifest_path)
        for task_id, result in results.items():
            out_file = os.path.join(output_dir, f"{task_id}.json")
            with open(out_file, "w") as f:
                json.dump(result, f, indent=2)
        print(json.dumps({"success": True, "tasks_judged": len(results)}))
    else:
        # Single mode: llm_judge.py <judge_model> <platform> <task_file> <work_dir> [output_file]
        if len(sys.argv) < 5:
            print("Usage: llm_judge.py <judge_model> <platform> <task_file> <work_dir> [output_file]")
            print("       llm_judge.py batch <judge_model> <manifest_json> <output_dir>")
            sys.exit(1)

        judge_model = sys.argv[1]
        platform = sys.argv[2]
        task_file = sys.argv[3]
        work_dir = sys.argv[4]
        output_file = sys.argv[5] if len(sys.argv) > 5 else None

        with open(task_file) as f:
            content = f.read()
        parts = content.split("---")
        task_prompt = "---".join(parts[2:]).strip() if len(parts) >= 3 else content

        generated_code = collect_generated_code(work_dir, platform)
        result = run_judge(judge_model, task_prompt, generated_code, platform)

        output = json.dumps(result, indent=2)
        if output_file:
            with open(output_file, "w") as f:
                f.write(output)
        else:
            print(output)


if __name__ == "__main__":
    main()
