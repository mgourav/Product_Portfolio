"""
Report + dashboard generation (PRD requirement R5).

build_report() merges scanner output, baseline diff, and register status
into one JSON-serializable structure. render_dashboard() turns that into a
single self-contained HTML file: inline CSS, hand-rolled SVG bar charts, no
external assets, no charting library, no build step (see ARCHITECTURE.md —
this is a deliberate cost to keep the dashboard genuinely standalone and
openable offline).
"""

import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from .baseline import DiffResult, TOOL_VERSION
from .register import RegisterEntry, RegisterStatus, status_for
from .scanner import Finding

# Colors are deliberately plain/accessible rather than brand-matched — this
# is a standalone tool, not styled after any one company's design system.
RISK_COLORS = {
    "quantum-vulnerable": "#c0392b",
    "monitor": "#d68910",
    "quantum-safe-today": "#1e8449",
    "pqc-ready": "#2874a6",
}
REGISTER_COLORS = {
    RegisterStatus.UNREVIEWED: "#c0392b",
    RegisterStatus.EXPIRED_ACCEPTANCE: "#d68910",
    RegisterStatus.ACCEPTED: "#1e8449",
}
# Diff status (new/existing) is a separate axis from register status and
# needs its own colors — reusing REGISTER_COLORS here was a bug: it made
# "existing" look red, green, or orange depending on register state, which
# conflates "is this new code" with "is this risk reviewed."
DIFF_COLORS = {
    "new": "#8e44ad",
    "existing": "#607d8b",
}


def build_report(
    current: list[Finding],
    diff_result: DiffResult,
    register: dict[str, RegisterEntry],
    repo_name: str = "unnamed-repo",
) -> dict:
    """
    Produces the JSON-serializable report that both the CLI prints a
    summary of and the dashboard renders from.

    Every current finding gets two independent classifications attached:
    - diff_status: new / existing (resolved findings aren't in `current`,
      so they're listed separately — there's nothing to attach a register
      status to for code that no longer exists)
    - register_status: accepted / expired-acceptance / unreviewed

    These are independent on purpose. A finding can be "existing" (we've
    known about it for months) and "expired-acceptance" (the review date
    everyone agreed to has passed) at the same time — that combination is
    exactly the kind of drift this tool exists to surface.
    """
    new_fps = {f.fingerprint for f in diff_result.new}

    findings_out = []
    for f in current:
        diff_status = "new" if f.fingerprint in new_fps else "existing"
        reg_status = status_for(f.fingerprint, register)
        entry = register.get(f.fingerprint)
        findings_out.append({
            **f.to_dict(),
            "diff_status": diff_status,
            "register_status": reg_status,
            "register_entry": entry.to_dict() if entry else None,
        })

    risk_counts: dict[str, int] = {}
    register_counts: dict[str, int] = {}
    for f in findings_out:
        risk_counts[f["risk"]] = risk_counts.get(f["risk"], 0) + 1
        register_counts[f["register_status"]] = register_counts.get(f["register_status"], 0) + 1

    # The single most important number for the primary persona: how much
    # is genuinely unreviewed risk, new or old, right now.
    unreviewed_count = register_counts.get(RegisterStatus.UNREVIEWED, 0)
    expired_count = register_counts.get(RegisterStatus.EXPIRED_ACCEPTANCE, 0)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tool_version": TOOL_VERSION,
        "repo_name": repo_name,
        "summary": {
            "total_findings": len(findings_out),
            "new_count": len(diff_result.new),
            "existing_count": len(diff_result.existing),
            "resolved_count": len(diff_result.resolved),
            "by_risk": risk_counts,
            "by_register_status": register_counts,
            "unreviewed_count": unreviewed_count,
            "expired_acceptance_count": expired_count,
        },
        "findings": findings_out,
        "resolved": [f.to_dict() for f in diff_result.resolved],
    }


def save_report(path: str | Path, report: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def load_report(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


# --------------------------------------------------------------------- #
# Dashboard rendering
# --------------------------------------------------------------------- #

def _svg_bar_chart(counts: dict[str, int], colors: dict[str, str], width: int = 420, bar_height: int = 28) -> str:
    """A minimal horizontal bar chart, hand-rolled as inline SVG. No library,
    no axes library — just enough to make the summary counts scannable."""
    labels = [k for k in counts if counts[k] > 0] or list(counts.keys())
    max_count = max(counts.values(), default=0) or 1
    row_gap = 12
    height = len(labels) * (bar_height + row_gap) + row_gap
    label_col_width = 170
    chart_width = width - label_col_width - 50

    rows = []
    for i, label in enumerate(labels):
        count = counts.get(label, 0)
        bar_w = int((count / max_count) * chart_width) if max_count else 0
        y = row_gap + i * (bar_height + row_gap)
        color = colors.get(label, "#777")
        rows.append(f'''
            <text x="0" y="{y + bar_height / 2 + 5}" font-size="13" fill="#333">{escape(label)}</text>
            <rect x="{label_col_width}" y="{y}" width="{max(bar_w, 2)}" height="{bar_height}" fill="{color}" rx="3"/>
            <text x="{label_col_width + bar_w + 8}" y="{y + bar_height / 2 + 5}" font-size="13" fill="#333">{count}</text>
        ''')

    return f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">{"".join(rows)}</svg>'


def _finding_row(f: dict) -> str:
    register_color = REGISTER_COLORS.get(f["register_status"], "#777")
    diff_color = DIFF_COLORS.get(f["diff_status"], "#777")
    risk_color = RISK_COLORS.get(f["risk"], "#777")
    register_note = ""
    if f.get("register_entry"):
        e = f["register_entry"]
        register_note = (
            f'<div class="register-note">Ticket {escape(e["ticket"])} '
            f'&middot; review by {escape(e["review_by"])}'
            + (f' &middot; {escape(e["reason"])}' if e.get("reason") else "")
            + "</div>"
        )
    return f'''
    <tr>
        <td><code>{escape(f["file"])}:{f["line"]}</code></td>
        <td>{escape(f["algorithm"])}</td>
        <td><span class="pill" style="background:{risk_color}">{escape(f["risk"])}</span></td>
        <td><span class="pill" style="background:{diff_color}">{escape(f["diff_status"])}</span></td>
        <td><span class="pill" style="background:{register_color}">{escape(f["register_status"])}</span>{register_note}</td>
        <td><code class="snippet">{escape(f["snippet"])}</code></td>
    </tr>
    '''


def render_dashboard(report: dict) -> str:
    """Produces one self-contained HTML string — no external CSS/JS/fonts."""
    summary = report["summary"]
    risk_chart = _svg_bar_chart(summary["by_risk"], RISK_COLORS)
    register_chart = _svg_bar_chart(summary["by_register_status"], REGISTER_COLORS)

    # Sort findings so the things a compliance officer most needs to see
    # land at the top: unreviewed and expired-acceptance first.
    status_priority = {RegisterStatus.UNREVIEWED: 0, RegisterStatus.EXPIRED_ACCEPTANCE: 1, RegisterStatus.ACCEPTED: 2}
    findings_sorted = sorted(
        report["findings"],
        key=lambda f: (status_priority.get(f["register_status"], 9), f["file"], f["line"]),
    )
    rows = "".join(_finding_row(f) for f in findings_sorted)

    headline = summary["unreviewed_count"]
    headline_note = "No unreviewed quantum-vulnerable or monitor-risk findings." if headline == 0 else \
        f"{headline} finding(s) are unreviewed — not yet fixed, not yet accepted."

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Crypto Radar — {escape(report["repo_name"])}</title>
<style>
  :root {{ color-scheme: light; }}
  body {{ font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
          margin: 0; padding: 32px; background: #fafafa; color: #1a1a1a; }}
  h1 {{ font-size: 22px; margin-bottom: 4px; }}
  .meta {{ color: #666; font-size: 13px; margin-bottom: 28px; }}
  .headline {{ padding: 16px 20px; border-radius: 8px; margin-bottom: 28px; font-size: 15px;
               background: {"#eafaf1" if headline == 0 else "#fdecea"};
               border: 1px solid {"#1e8449" if headline == 0 else "#c0392b"}; }}
  .grid {{ display: flex; gap: 32px; flex-wrap: wrap; margin-bottom: 32px; }}
  .card {{ background: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px 20px; }}
  .card h2 {{ font-size: 14px; text-transform: uppercase; letter-spacing: 0.04em; color: #666; margin: 0 0 12px; }}
  table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; }}
  th, td {{ text-align: left; padding: 10px 12px; border-bottom: 1px solid #eee; font-size: 13px; vertical-align: top; }}
  th {{ background: #f3f3f3; font-size: 12px; text-transform: uppercase; letter-spacing: 0.03em; color: #666; }}
  code {{ font-family: "SF Mono", Consolas, monospace; font-size: 12px; }}
  .snippet {{ color: #444; }}
  .pill {{ display: inline-block; padding: 2px 8px; border-radius: 10px; color: white; font-size: 11px; white-space: nowrap; }}
  .register-note {{ font-size: 11px; color: #888; margin-top: 2px; }}
  footer {{ margin-top: 32px; font-size: 12px; color: #999; }}
</style>
</head>
<body>
  <h1>Crypto Radar — {escape(report["repo_name"])}</h1>
  <div class="meta">Generated {escape(report["generated_at"])} &middot; tool v{escape(report["tool_version"])}</div>

  <div class="headline">{escape(headline_note)}
    {f' &middot; {summary["expired_acceptance_count"]} accepted finding(s) have passed their review date.' if summary["expired_acceptance_count"] else ""}
  </div>

  <div class="grid">
    <div class="card"><h2>Findings by risk category</h2>{risk_chart}</div>
    <div class="card"><h2>Findings by register status</h2>{register_chart}</div>
    <div class="card">
      <h2>Scan summary</h2>
      <table>
        <tr><td>Total findings</td><td><strong>{summary["total_findings"]}</strong></td></tr>
        <tr><td>New since baseline</td><td><strong>{summary["new_count"]}</strong></td></tr>
        <tr><td>Existing (in baseline)</td><td><strong>{summary["existing_count"]}</strong></td></tr>
        <tr><td>Resolved since baseline</td><td><strong>{summary["resolved_count"]}</strong></td></tr>
      </table>
    </div>
  </div>

  <h2>Findings</h2>
  <table>
    <thead><tr><th>Location</th><th>Algorithm</th><th>Risk</th><th>Diff</th><th>Register</th><th>Snippet</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>

  <footer>
    Crypto Radar is a portfolio project demonstrating continuous PQC-readiness scanning.
    Detection is regex-based and not a substitute for a full cryptographic risk assessment
    — see the project README for documented limitations.
  </footer>
</body>
</html>
'''
