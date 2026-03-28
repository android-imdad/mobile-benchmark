#!/usr/bin/env python3
"""
Mobile Development Benchmark Report Generator
Generates a self-contained HTML report with interactive Chart.js graphs.
Supports deterministic scores, LLM-as-Judge dimensions, and static analysis.
"""

import json
import os
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone

JUDGE_DIMENSIONS = [
    "correctness", "code_quality", "best_practices", "completeness",
    "readability", "error_handling", "performance", "architecture",
]


def load_results(raw_dir: str) -> list[dict]:
    results = []
    for f in Path(raw_dir).glob("*.json"):
        try:
            with open(f) as fh:
                data = json.load(fh)
                results.append(data)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load {f}: {e}", file=sys.stderr)
    return results


def compute_aggregates(results: list[dict]) -> dict:
    models = sorted(set(r["model"] for r in results))
    platforms = sorted(set(r["platform"] for r in results))
    difficulties = sorted(
        set(r["difficulty"] for r in results),
        key=lambda d: ["easy", "medium", "hard"].index(d) if d in ["easy", "medium", "hard"] else 99,
    )
    categories = sorted(set(r.get("category", "generate") for r in results))

    model_platform_scores = defaultdict(lambda: defaultdict(list))
    model_difficulty_scores = defaultdict(lambda: defaultdict(list))
    model_category_scores = defaultdict(lambda: defaultdict(list))
    model_total_scores = defaultdict(list)
    model_composite_scores = defaultdict(list)
    model_times = defaultdict(list)
    model_build_pass = defaultdict(lambda: {"passed": 0, "total": 0})
    model_pattern_pass = defaultdict(lambda: {"matched": 0, "total": 0})
    model_judge_dims = defaultdict(lambda: defaultdict(list))
    model_judge_avg = defaultdict(list)
    model_static_scores = defaultdict(list)
    task_results = []

    has_judge = any(r.get("llm_judge", {}).get("success", False) for r in results)
    has_static = any("static_analysis" in r and r["static_analysis"] for r in results)
    judge_model_used = ""

    for r in results:
        model = r["model"]
        platform = r["platform"]
        difficulty = r["difficulty"]
        category = r.get("category", "generate")
        score = r["scores"]["total"]
        composite = r["scores"].get("composite", score)
        max_score = r.get("max_score", 10)
        duration = r["duration_ms"]

        model_platform_scores[model][platform].append(composite)
        model_difficulty_scores[model][difficulty].append(composite)
        model_category_scores[model][category].append(composite)
        model_total_scores[model].append(score)
        model_composite_scores[model].append(composite)
        model_times[model].append(duration)

        model_build_pass[model]["total"] += 1
        if r.get("validation", {}).get("build_success", False):
            model_build_pass[model]["passed"] += 1

        pv = r.get("validation", {}).get("patterns", {})
        if isinstance(pv, dict):
            model_pattern_pass[model]["matched"] += pv.get("matched", 0)
            model_pattern_pass[model]["total"] += pv.get("total", 0)

        # LLM Judge data
        judge = r.get("llm_judge", {})
        if judge.get("success", False):
            if not judge_model_used:
                judge_model_used = judge.get("model", "")
            judge_avg = judge.get("average_score", 0)
            model_judge_avg[model].append(judge_avg)
            dims = judge.get("dimensions", {})
            for dim in JUDGE_DIMENSIONS:
                if dim in dims:
                    s = dims[dim].get("score", 0) if isinstance(dims[dim], dict) else 0
                    model_judge_dims[model][dim].append(s)

        # Static analysis
        static = r.get("static_analysis", {})
        if static and "score" in static:
            model_static_scores[model].append(static["score"])

        # Task detail
        judge_scores_detail = {}
        if judge.get("success", False):
            for dim in JUDGE_DIMENSIONS:
                d = judge.get("dimensions", {}).get(dim, {})
                if isinstance(d, dict):
                    judge_scores_detail[dim] = {
                        "score": d.get("score", 0),
                        "reason": d.get("reason", ""),
                    }

        task_results.append({
            "model": model,
            "platform": platform,
            "difficulty": difficulty,
            "category": category,
            "task": r.get("task", ""),
            "score": score,
            "composite": composite,
            "max_score": max_score,
            "duration_ms": duration,
            "build_success": r.get("validation", {}).get("build_success", False),
            "patterns_matched": pv.get("matched", 0) if isinstance(pv, dict) else 0,
            "patterns_total": pv.get("total", 0) if isinstance(pv, dict) else 0,
            "judge_avg": judge.get("average_score", 0) if judge.get("success") else None,
            "judge_dimensions": judge_scores_detail,
            "static_score": static.get("score") if static else None,
            "static_errors": static.get("errors", 0) if static else 0,
            "static_warnings": static.get("warnings", 0) if static else 0,
        })

    def avg(lst):
        return round(sum(lst) / len(lst), 2) if lst else 0

    summary_table = []
    for model in models:
        scores = model_total_scores[model]
        composites = model_composite_scores[model]
        times = model_times[model]
        bp = model_build_pass[model]
        pp = model_pattern_pass[model]
        judge_avgs = model_judge_avg.get(model, [])
        statics = model_static_scores.get(model, [])

        summary_table.append({
            "model": model,
            "avg_score": avg(scores),
            "avg_composite": avg(composites),
            "total_score": round(sum(composites), 1),
            "max_possible": len(scores) * 10,
            "tasks_run": len(scores),
            "pass_rate": round(sum(1 for s in composites if s >= 7) / len(composites) * 100, 1) if composites else 0,
            "avg_time_s": round(avg(times) / 1000, 1),
            "build_pass_rate": round(bp["passed"] / bp["total"] * 100, 1) if bp["total"] else 0,
            "pattern_match_rate": round(pp["matched"] / pp["total"] * 100, 1) if pp["total"] else 0,
            "judge_avg": avg(judge_avgs) if judge_avgs else None,
            "static_avg": avg(statics) if statics else None,
        })

    # Radar chart: model -> platform -> avg composite
    radar_data = {}
    for model in models:
        radar_data[model] = {p: avg(model_platform_scores[model][p]) for p in platforms}

    # Difficulty bar
    grouped_bar_data = {}
    for model in models:
        grouped_bar_data[model] = {d: avg(model_difficulty_scores[model][d]) for d in difficulties}

    # Category bar
    category_data = {}
    for model in models:
        category_data[model] = {c: avg(model_category_scores[model][c]) for c in categories}

    # Time data
    time_data = {}
    for model in models:
        model_results = [r for r in results if r["model"] == model]
        time_data[model] = [(r.get("task_id", r.get("task", "")), r["duration_ms"]) for r in model_results]

    # Judge dimension radar: model -> dimension -> avg score
    judge_dimension_data = {}
    for model in models:
        judge_dimension_data[model] = {}
        for dim in JUDGE_DIMENSIONS:
            vals = model_judge_dims[model].get(dim, [])
            judge_dimension_data[model][dim] = avg(vals) if vals else 0

    return {
        "models": models,
        "platforms": platforms,
        "difficulties": difficulties,
        "categories": categories,
        "summary_table": sorted(summary_table, key=lambda x: x["avg_composite"], reverse=True),
        "radar_data": radar_data,
        "grouped_bar_data": grouped_bar_data,
        "category_data": category_data,
        "time_data": time_data,
        "task_results": task_results,
        "total_tasks": len(results),
        "has_judge": has_judge,
        "has_static": has_static,
        "judge_model": judge_model_used,
        "judge_dimension_data": judge_dimension_data,
    }


def generate_html(agg: dict, output_path: str):
    models = agg["models"]
    platforms = agg["platforms"]
    difficulties = agg["difficulties"]
    categories = agg["categories"]
    has_judge = agg["has_judge"]
    has_static = agg["has_static"]

    model_colors = [
        "rgba(99, 102, 241, {a})",
        "rgba(236, 72, 153, {a})",
        "rgba(16, 185, 129, {a})",
        "rgba(245, 158, 11, {a})",
        "rgba(59, 130, 246, {a})",
        "rgba(168, 85, 247, {a})",
        "rgba(239, 68, 68, {a})",
        "rgba(20, 184, 166, {a})",
    ]

    def color(i, alpha=1.0):
        return model_colors[i % len(model_colors)].replace("{a}", str(alpha))

    # Radar datasets (platform)
    radar_datasets = []
    for i, model in enumerate(models):
        values = [agg["radar_data"][model].get(p, 0) for p in platforms]
        radar_datasets.append({
            "label": model,
            "data": values,
            "backgroundColor": color(i, 0.2),
            "borderColor": color(i, 1),
            "pointBackgroundColor": color(i, 1),
            "borderWidth": 2,
        })

    # Difficulty bar datasets
    bar_datasets = []
    for i, model in enumerate(models):
        values = [agg["grouped_bar_data"][model].get(d, 0) for d in difficulties]
        bar_datasets.append({
            "label": model,
            "data": values,
            "backgroundColor": color(i, 0.7),
            "borderColor": color(i, 1),
            "borderWidth": 1,
        })

    # Category bar datasets
    cat_datasets = []
    for j, cat in enumerate(categories):
        cat_colors = [
            "rgba(99, 102, 241, 0.8)", "rgba(236, 72, 153, 0.8)",
            "rgba(16, 185, 129, 0.8)", "rgba(245, 158, 11, 0.8)",
            "rgba(59, 130, 246, 0.8)",
        ]
        values = [agg["category_data"][m].get(cat, 0) for m in models]
        cat_datasets.append({
            "label": cat.capitalize(),
            "data": values,
            "backgroundColor": cat_colors[j % len(cat_colors)],
        })

    # Time line chart
    time_datasets = []
    all_task_ids = []
    if models:
        first_model = models[0]
        all_task_ids = [t[0] for t in agg["time_data"].get(first_model, [])]

    for i, model in enumerate(models):
        times = agg["time_data"].get(model, [])
        time_map = {t[0]: t[1] / 1000 for t in times}
        values = [time_map.get(tid, 0) for tid in all_task_ids]
        time_datasets.append({
            "label": model,
            "data": values,
            "borderColor": color(i, 1),
            "backgroundColor": color(i, 0.1),
            "tension": 0.3,
            "fill": False,
            "pointRadius": 3,
        })

    # Judge dimension radar datasets
    judge_radar_datasets = []
    if has_judge:
        dim_labels = [d.replace("_", " ").title() for d in JUDGE_DIMENSIONS]
        for i, model in enumerate(models):
            values = [agg["judge_dimension_data"][model].get(d, 0) for d in JUDGE_DIMENSIONS]
            judge_radar_datasets.append({
                "label": model,
                "data": values,
                "backgroundColor": color(i, 0.15),
                "borderColor": color(i, 1),
                "pointBackgroundColor": color(i, 1),
                "borderWidth": 2,
            })

    # Build summary table HTML
    judge_headers = ""
    if has_judge:
        judge_headers = "<th>Judge Avg</th>"
    if has_static:
        judge_headers += "<th>Static</th>"

    table_rows = ""
    for idx, row in enumerate(agg["summary_table"]):
        rank_badge = ""
        if idx == 0:
            rank_badge = '<span class="badge gold">1st</span>'
        elif idx == 1:
            rank_badge = '<span class="badge silver">2nd</span>'
        elif idx == 2:
            rank_badge = '<span class="badge bronze">3rd</span>'
        else:
            rank_badge = f'<span class="badge">{idx+1}th</span>'

        sc = row["avg_composite"]
        score_class = "score-high" if sc >= 7 else "score-mid" if sc >= 4 else "score-low"

        extra_cols = ""
        if has_judge:
            jv = row.get("judge_avg")
            jclass = "score-high" if jv and jv >= 7 else "score-mid" if jv and jv >= 4 else "score-low"
            extra_cols += f'<td class="{jclass}">{jv if jv is not None else "N/A"}</td>'
        if has_static:
            sv = row.get("static_avg")
            sclass = "score-high" if sv and sv >= 7 else "score-mid" if sv and sv >= 4 else "score-low"
            extra_cols += f'<td class="{sclass}">{sv if sv is not None else "N/A"}</td>'

        table_rows += f"""
        <tr>
            <td>{rank_badge}</td>
            <td class="model-name">{row['model']}</td>
            <td class="{score_class}">{row['avg_composite']}</td>
            <td>{row['avg_score']}</td>
            <td>{row['total_score']}/{row['max_possible']}</td>
            <td>{row['tasks_run']}</td>
            <td>{row['pass_rate']}%</td>
            <td>{row['build_pass_rate']}%</td>
            {extra_cols}
            <td>{row['avg_time_s']}s</td>
        </tr>"""

    # Task detail rows
    task_detail_rows = ""
    for t in sorted(agg["task_results"], key=lambda x: (x["model"], x["platform"], x["difficulty"], x["task"])):
        sc = "score-high" if t["composite"] >= 7 else "score-mid" if t["composite"] >= 4 else "score-low"
        build_icon = "&#10003;" if t["build_success"] else "&#10007;"
        build_class = "pass" if t["build_success"] else "fail"
        pat_text = f"{t['patterns_matched']}/{t['patterns_total']}" if t["patterns_total"] > 0 else "N/A"

        judge_col = ""
        if has_judge:
            ja = t.get("judge_avg")
            if ja is not None and ja > 0:
                jclass = "score-high" if ja >= 7 else "score-mid" if ja >= 4 else "score-low"
                # Build tooltip with dimension scores
                dims = t.get("judge_dimensions", {})
                tooltip_parts = []
                for d in JUDGE_DIMENSIONS:
                    if d in dims:
                        tooltip_parts.append(f"{d.replace('_',' ').title()}: {dims[d]['score']}/10")
                tooltip = "&#10;".join(tooltip_parts)
                judge_col = f'<td class="{jclass}" title="{tooltip}">{ja}</td>'
            else:
                judge_col = '<td class="score-low">N/A</td>'

        static_col = ""
        if has_static:
            sv = t.get("static_score")
            if sv is not None:
                sclass = "score-high" if sv >= 7 else "score-mid" if sv >= 4 else "score-low"
                static_col = f'<td class="{sclass}">{sv} ({t["static_errors"]}E/{t["static_warnings"]}W)</td>'
            else:
                static_col = '<td>N/A</td>'

        task_detail_rows += f"""
        <tr>
            <td>{t['model']}</td>
            <td>{t['platform']}</td>
            <td><span class="diff-badge diff-{t['difficulty']}">{t['difficulty']}</span></td>
            <td>{t['task']}</td>
            <td class="{sc}">{t['composite']}/{t['max_score']}</td>
            <td>{t['score']}</td>
            <td class="{build_class}">{build_icon}</td>
            <td>{pat_text}</td>
            {judge_col}
            {static_col}
            <td>{round(t['duration_ms']/1000, 1)}s</td>
        </tr>"""

    task_detail_headers = ""
    if has_judge:
        task_detail_headers += "<th>Judge</th>"
    if has_static:
        task_detail_headers += "<th>Static</th>"

    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Judge section HTML
    judge_section_html = ""
    if has_judge:
        judge_section_html = f"""
    <div class="section">
        <h2 class="section-title">LLM-as-Judge Code Quality Analysis</h2>
        <p class="section-desc">Judge model: <strong>{agg['judge_model']}</strong> — Scores across 8 quality dimensions (1-10 scale)</p>
        <div class="charts-grid">
            <div class="chart-card" style="grid-column: span 2;">
                <h3>Code Quality Dimensions (Radar)</h3>
                <div class="chart-container" style="height: 450px;">
                    <canvas id="judgeRadarChart"></canvas>
                </div>
            </div>
        </div>
    </div>
"""

    # Scoring explanation
    scoring_html = """
    <div class="section">
        <h2 class="section-title">Scoring Methodology</h2>
        <div class="scoring-grid">
            <div class="scoring-card">
                <h4>Deterministic Score (40%)</h4>
                <ul>
                    <li><strong>Completion (3pts)</strong>: Did the model produce output?</li>
                    <li><strong>Build (3pts)</strong>: Does the code compile?</li>
                    <li><strong>Patterns (2pts)</strong>: Required code patterns present?</li>
                    <li><strong>Files (1pt)</strong>: Expected files created?</li>
                    <li><strong>Speed (1pt)</strong>: Finished under half timeout?</li>
                </ul>
            </div>"""
    if has_judge:
        scoring_html += """
            <div class="scoring-card">
                <h4>LLM Judge Score (45%)</h4>
                <ul>
                    <li><strong>Correctness</strong>: Logic and output accuracy</li>
                    <li><strong>Code Quality</strong>: Clean, idiomatic code</li>
                    <li><strong>Best Practices</strong>: Platform conventions</li>
                    <li><strong>Completeness</strong>: All requirements addressed</li>
                    <li><strong>Readability</strong>: Naming, formatting, flow</li>
                    <li><strong>Error Handling</strong>: Graceful failure handling</li>
                    <li><strong>Performance</strong>: Efficiency of solution</li>
                    <li><strong>Architecture</strong>: Separation, testability</li>
                </ul>
            </div>"""
    if has_static:
        scoring_html += """
            <div class="scoring-card">
                <h4>Static Analysis (15%)</h4>
                <ul>
                    <li>SwiftLint (iOS), ktlint (Android), dart analyze (Flutter)</li>
                    <li>-2pts per error, -0.5pts per warning</li>
                    <li>Starts at 10, floor at 0</li>
                </ul>
            </div>"""
    scoring_html += """
        </div>
    </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mobile Dev Benchmark Report</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root {{
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --bg-card: #1e293b;
    --bg-card-hover: #334155;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --border-color: #334155;
    --accent-indigo: #818cf8;
    --accent-pink: #f472b6;
    --accent-emerald: #34d399;
    --accent-amber: #fbbf24;
    --success: #34d399;
    --danger: #f87171;
    --warning: #fbbf24;
}}

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    min-height: 100vh;
}}

.container {{
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
}}

header {{
    text-align: center;
    padding: 3rem 0 2rem;
    border-bottom: 1px solid var(--border-color);
    margin-bottom: 2rem;
}}

header h1 {{
    font-size: 2.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, var(--accent-indigo), var(--accent-pink));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.5rem;
}}

header .subtitle {{ color: var(--text-secondary); font-size: 1.1rem; }}

header .meta {{
    margin-top: 1rem;
    display: flex;
    justify-content: center;
    gap: 2rem;
    color: var(--text-muted);
    font-size: 0.9rem;
    flex-wrap: wrap;
}}

header .meta span {{ display: flex; align-items: center; gap: 0.4rem; }}

.stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
}}

.stat-card {{
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    transition: transform 0.2s, border-color 0.2s;
}}

.stat-card:hover {{ transform: translateY(-2px); border-color: var(--accent-indigo); }}
.stat-card .value {{ font-size: 2rem; font-weight: 700; color: var(--accent-indigo); }}
.stat-card .label {{ color: var(--text-secondary); font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.3rem; }}

.section {{ margin-bottom: 2.5rem; }}

.section-title {{
    font-size: 1.4rem;
    font-weight: 700;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid var(--border-color);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}

.section-desc {{ color: var(--text-secondary); margin-bottom: 1rem; font-size: 0.9rem; }}

.charts-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(580px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}}

.chart-card {{
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 1.5rem;
}}

.chart-card h3 {{ font-size: 1.1rem; margin-bottom: 1rem; color: var(--text-primary); }}
.chart-container {{ position: relative; height: 350px; }}

table {{
    width: 100%;
    border-collapse: collapse;
    background: var(--bg-card);
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid var(--border-color);
}}

th, td {{ padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid var(--border-color); font-size: 0.9rem; }}

th {{
    background: var(--bg-secondary);
    color: var(--text-secondary);
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.75rem;
    letter-spacing: 0.05em;
    position: sticky;
    top: 0;
}}

tr:hover {{ background: var(--bg-card-hover); }}
.model-name {{ font-weight: 600; color: var(--accent-indigo); }}
.score-high {{ color: var(--success); font-weight: 700; }}
.score-mid {{ color: var(--warning); font-weight: 700; }}
.score-low {{ color: var(--danger); font-weight: 700; }}
.pass {{ color: var(--success); }}
.fail {{ color: var(--danger); }}

.badge {{
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 700;
    background: var(--bg-secondary);
    color: var(--text-secondary);
    border: 1px solid var(--border-color);
}}

.badge.gold {{ background: linear-gradient(135deg, #fbbf24, #f59e0b); color: #1e293b; border: none; }}
.badge.silver {{ background: linear-gradient(135deg, #94a3b8, #64748b); color: #1e293b; border: none; }}
.badge.bronze {{ background: linear-gradient(135deg, #d97706, #b45309); color: #1e293b; border: none; }}

.diff-badge {{ display: inline-block; padding: 0.15rem 0.5rem; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }}
.diff-easy {{ background: rgba(52, 211, 153, 0.2); color: var(--success); }}
.diff-medium {{ background: rgba(251, 191, 36, 0.2); color: var(--warning); }}
.diff-hard {{ background: rgba(248, 113, 113, 0.2); color: var(--danger); }}

.table-wrapper {{ border-radius: 12px; overflow-x: auto; max-height: 600px; overflow-y: auto; }}

.detail-toggle {{
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    padding: 0.6rem 1.2rem;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.9rem;
    margin-bottom: 1rem;
    transition: background 0.2s;
}}

.detail-toggle:hover {{ background: var(--bg-card-hover); }}
#taskDetailSection {{ display: none; }}

.scoring-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1rem;
}}

.scoring-card {{
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 1.5rem;
}}

.scoring-card h4 {{
    color: var(--accent-indigo);
    margin-bottom: 0.75rem;
    font-size: 1rem;
}}

.scoring-card ul {{
    list-style: none;
    padding: 0;
}}

.scoring-card li {{
    color: var(--text-secondary);
    font-size: 0.85rem;
    padding: 0.25rem 0;
    border-bottom: 1px solid rgba(51, 65, 85, 0.5);
}}

.scoring-card li:last-child {{ border-bottom: none; }}

footer {{
    text-align: center;
    padding: 2rem 0;
    color: var(--text-muted);
    font-size: 0.85rem;
    border-top: 1px solid var(--border-color);
    margin-top: 2rem;
}}
</style>
</head>
<body>

<div class="container">
    <header>
        <h1>Mobile Dev Benchmark</h1>
        <p class="subtitle">AI Model Performance Across iOS, Android &amp; Flutter</p>
        <div class="meta">
            <span>Generated: {timestamp}</span>
            <span>Tasks: {agg['total_tasks']}</span>
            <span>Models: {len(models)}</span>
            {"<span>Judge: " + agg['judge_model'] + "</span>" if has_judge else ""}
            <span>Scoring: {"Composite (Det 40% + Judge 45% + Static 15%)" if has_judge else "Deterministic"}</span>
        </div>
    </header>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="value">{len(models)}</div>
            <div class="label">Models Tested</div>
        </div>
        <div class="stat-card">
            <div class="value">{agg['total_tasks']}</div>
            <div class="label">Total Tasks Run</div>
        </div>
        <div class="stat-card">
            <div class="value">{agg['summary_table'][0]['avg_composite'] if agg['summary_table'] else 0}</div>
            <div class="label">Best Avg Score</div>
        </div>
        <div class="stat-card">
            <div class="value">{agg['summary_table'][0]['model'] if agg['summary_table'] else 'N/A'}</div>
            <div class="label">Top Model</div>
        </div>
        {"<div class='stat-card'><div class='value'>" + str(max((r.get('judge_avg') or 0) for r in agg['task_results'])) + "</div><div class='label'>Best Judge Score</div></div>" if has_judge else ""}
    </div>

    <div class="section">
        <h2 class="section-title">Leaderboard</h2>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Model</th>
                        <th>Composite</th>
                        <th>Deterministic</th>
                        <th>Total</th>
                        <th>Tasks</th>
                        <th>Pass Rate</th>
                        <th>Build Pass</th>
                        {judge_headers}
                        <th>Avg Time</th>
                    </tr>
                </thead>
                <tbody>{table_rows}</tbody>
            </table>
        </div>
    </div>

    {judge_section_html}

    <div class="charts-grid">
        <div class="chart-card">
            <h3>Platform Performance (Radar)</h3>
            <div class="chart-container">
                <canvas id="radarChart"></canvas>
            </div>
        </div>
        <div class="chart-card">
            <h3>Score by Difficulty</h3>
            <div class="chart-container">
                <canvas id="difficultyChart"></canvas>
            </div>
        </div>
        <div class="chart-card">
            <h3>Score by Category</h3>
            <div class="chart-container">
                <canvas id="categoryChart"></canvas>
            </div>
        </div>
        <div class="chart-card">
            <h3>Task Completion Time (seconds)</h3>
            <div class="chart-container">
                <canvas id="timeChart"></canvas>
            </div>
        </div>
    </div>

    {scoring_html}

    <div class="section">
        <h2 class="section-title">Task Details</h2>
        <button class="detail-toggle" onclick="toggleDetails()">Show/Hide Task Details</button>
        <div id="taskDetailSection">
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>Model</th>
                            <th>Platform</th>
                            <th>Difficulty</th>
                            <th>Task</th>
                            <th>Composite</th>
                            <th>Det.</th>
                            <th>Build</th>
                            <th>Patterns</th>
                            {task_detail_headers}
                            <th>Time</th>
                        </tr>
                    </thead>
                    <tbody>{task_detail_rows}</tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<footer>
    <p>Mobile Development Benchmark Suite &mdash; Generated by Factory Droid CLI</p>
</footer>

<script>
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = '#334155';

new Chart(document.getElementById('radarChart'), {{
    type: 'radar',
    data: {{ labels: {json.dumps(platforms)}, datasets: {json.dumps(radar_datasets)} }},
    options: {{
        responsive: true, maintainAspectRatio: false,
        scales: {{ r: {{ beginAtZero: true, max: 10, ticks: {{ stepSize: 2, color: '#64748b' }}, grid: {{ color: '#334155' }}, angleLines: {{ color: '#334155' }}, pointLabels: {{ font: {{ size: 14 }}, color: '#f1f5f9' }} }} }},
        plugins: {{ legend: {{ position: 'bottom', labels: {{ padding: 20 }} }} }}
    }}
}});

new Chart(document.getElementById('difficultyChart'), {{
    type: 'bar',
    data: {{ labels: {json.dumps([d.capitalize() for d in difficulties])}, datasets: {json.dumps(bar_datasets)} }},
    options: {{
        responsive: true, maintainAspectRatio: false,
        scales: {{ y: {{ beginAtZero: true, max: 10, grid: {{ color: '#334155' }} }}, x: {{ grid: {{ display: false }} }} }},
        plugins: {{ legend: {{ position: 'bottom', labels: {{ padding: 20 }} }} }}
    }}
}});

new Chart(document.getElementById('categoryChart'), {{
    type: 'bar',
    data: {{ labels: {json.dumps(models)}, datasets: {json.dumps(cat_datasets)} }},
    options: {{
        responsive: true, maintainAspectRatio: false,
        scales: {{ y: {{ stacked: false, beginAtZero: true, max: 10, grid: {{ color: '#334155' }} }}, x: {{ stacked: false, grid: {{ display: false }}, ticks: {{ maxRotation: 45 }} }} }},
        plugins: {{ legend: {{ position: 'bottom', labels: {{ padding: 20 }} }} }}
    }}
}});

new Chart(document.getElementById('timeChart'), {{
    type: 'line',
    data: {{ labels: {json.dumps([tid.replace('_', ' ') for tid in all_task_ids])}, datasets: {json.dumps(time_datasets)} }},
    options: {{
        responsive: true, maintainAspectRatio: false,
        scales: {{ y: {{ beginAtZero: true, title: {{ display: true, text: 'Seconds' }}, grid: {{ color: '#334155' }} }}, x: {{ grid: {{ display: false }}, ticks: {{ maxRotation: 90, font: {{ size: 9 }} }} }} }},
        plugins: {{ legend: {{ position: 'bottom', labels: {{ padding: 20 }} }} }}
    }}
}});

{"" if not has_judge else f"""
new Chart(document.getElementById('judgeRadarChart'), {{
    type: 'radar',
    data: {{
        labels: {json.dumps([d.replace('_', ' ').title() for d in JUDGE_DIMENSIONS])},
        datasets: {json.dumps(judge_radar_datasets)}
    }},
    options: {{
        responsive: true, maintainAspectRatio: false,
        scales: {{ r: {{ beginAtZero: true, max: 10, ticks: {{ stepSize: 2, color: '#64748b' }}, grid: {{ color: '#334155' }}, angleLines: {{ color: '#334155' }}, pointLabels: {{ font: {{ size: 12 }}, color: '#f1f5f9' }} }} }},
        plugins: {{ legend: {{ position: 'bottom', labels: {{ padding: 20 }} }} }}
    }}
}});
"""}

function toggleDetails() {{
    const section = document.getElementById('taskDetailSection');
    section.style.display = section.style.display === 'none' ? 'block' : 'none';
}}
</script>

</body>
</html>"""

    with open(output_path, "w") as f:
        f.write(html)
    print(f"Report generated: {output_path}")


def main():
    if len(sys.argv) < 3:
        print("Usage: generate_report.py <raw_results_dir> <output_html>")
        sys.exit(1)

    raw_dir = sys.argv[1]
    output_path = sys.argv[2]

    if not os.path.isdir(raw_dir):
        print(f"Error: {raw_dir} is not a directory")
        sys.exit(1)

    results = load_results(raw_dir)
    if not results:
        print("No results found. Creating empty report.")
        with open(output_path, "w") as f:
            f.write("<html><body><h1>No benchmark results found</h1></body></html>")
        sys.exit(0)

    agg = compute_aggregates(results)
    generate_html(agg, output_path)


if __name__ == "__main__":
    main()
