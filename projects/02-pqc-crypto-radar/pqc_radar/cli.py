"""
Command-line entry point. Three subcommands, matching ARCHITECTURE.md's CLI
surface exactly:

    pqc-radar scan <path> [--baseline FILE] [--register FILE]
                           [--save-baseline] [--out report.json]
                           [--fail-on-new] [--repo-name NAME]
    pqc-radar accept <path> <fingerprint> --ticket T --review-by YYYY-MM-DD [--reason TEXT]
                      [--register FILE]
    pqc-radar dashboard <report.json> [--out dashboard.html]

Run as `python -m pqc_radar <subcommand> ...` or via the `pqc-radar` console
script once installed.
"""

import argparse
import json
import sys
from pathlib import Path

from . import baseline as baseline_mod
from . import register as register_mod
from . import report as report_mod
from .scanner import scan_path, risk_summary


def _default_pqc_radar_dir(scan_target: str) -> Path:
    return Path(scan_target) / ".pqc-radar"


def cmd_scan(args: argparse.Namespace) -> int:
    scan_target = args.path
    pqc_dir = _default_pqc_radar_dir(scan_target)
    baseline_path = Path(args.baseline) if args.baseline else pqc_dir / "baseline.json"
    register_path = Path(args.register) if args.register else pqc_dir / "register.json"
    out_path = Path(args.out) if args.out else Path("report.json")

    repo_name = args.repo_name or Path(scan_target).resolve().name

    # Guard against the default --out (report.json in the current directory)
    # silently clobbering a different repo's report — easy to hit by running
    # `scan repoA` then `scan repoB` from the same terminal without
    # remembering --out each time.
    if out_path.exists():
        try:
            previous = report_mod.load_report(out_path)
            if previous.get("repo_name") not in (None, repo_name):
                print(
                    f"Warning: {out_path} already contains a report for "
                    f"{previous['repo_name']!r}, overwriting it with {repo_name!r}. "
                    "Pass --out to keep separate reports per repo.",
                    file=sys.stderr,
                )
        except Exception:
            pass  # not a report we can introspect — fine, just overwrite as before

    current = scan_path(scan_target)
    existing_baseline = baseline_mod.load_baseline(baseline_path)
    diff_result = baseline_mod.diff(current, existing_baseline)
    reg = register_mod.load_register(register_path)

    rep = report_mod.build_report(current, diff_result, reg, repo_name=repo_name)
    report_mod.save_report(out_path, rep)

    summary = rep["summary"]
    print(f"Scanned {scan_target}")
    print(f"  Total findings:        {summary['total_findings']}")
    print(f"  New since baseline:    {summary['new_count']}")
    print(f"  Existing:              {summary['existing_count']}")
    print(f"  Resolved:              {summary['resolved_count']}")
    print(f"  Unreviewed:            {summary['unreviewed_count']}")
    print(f"  Expired acceptances:   {summary['expired_acceptance_count']}")
    print(f"Report written to {out_path}")

    if args.save_baseline:
        baseline_mod.save_baseline(baseline_path, current)
        print(f"Baseline saved to {baseline_path} ({len(current)} findings).")
    else:
        print(
            "Baseline NOT updated (pass --save-baseline to accept these findings "
            "into the tracked baseline)."
        )

    if args.fail_on_new and summary["unreviewed_count"] > 0:
        print(
            f"\nFAIL: {summary['unreviewed_count']} unreviewed finding(s). "
            "(--fail-on-new is unused by any CI pipeline yet — this is Phase 1; "
            "wiring it into CI is a documented fast-follow, not built here.)",
            file=sys.stderr,
        )
        return 1

    return 0


def cmd_accept(args: argparse.Namespace) -> int:
    # Same pattern as `scan`: a repo path, with the register location
    # defaulted from it unless --register overrides. Previously this
    # command required typing out the full --register file path by hand
    # while `scan` figured it out from the repo path — same tool, two
    # different mental models. Fixed to match.
    register_path = Path(args.register) if args.register else _default_pqc_radar_dir(args.path) / "register.json"

    # Soft check, not a hard failure: if a baseline exists for this repo and
    # the fingerprint isn't in it, the user likely mistyped it (or it's a
    # genuinely brand-new finding not yet baselined, which is legitimate —
    # hence a warning, not a rejection).
    baseline_path = _default_pqc_radar_dir(args.path) / "baseline.json"
    known_fps = {f.fingerprint for f in (baseline_mod.load_baseline(baseline_path) or [])}
    if known_fps and args.fingerprint not in known_fps:
        print(
            f"Warning: fingerprint {args.fingerprint!r} isn't in the baseline at {baseline_path}. "
            "Double-check you copied it correctly from a scan report "
            "(this is fine if it's a brand-new finding not yet baselined).",
            file=sys.stderr,
        )

    try:
        entry = register_mod.accept(
            register_path,
            fingerprint=args.fingerprint,
            ticket=args.ticket,
            review_by=args.review_by,
            reason=args.reason or "",
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Accepted {entry.fingerprint} — ticket {entry.ticket}, review by {entry.review_by}")
    print(f"Register saved to {register_path}")
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    rep = report_mod.load_report(args.report)
    html = report_mod.render_dashboard(rep)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"Dashboard written to {out_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pqc-radar")
    sub = parser.add_subparsers(dest="command", required=True)

    scan_p = sub.add_parser("scan", help="Scan a codebase for cryptographic algorithm usage.")
    scan_p.add_argument("path", help="Path to the repository/codebase to scan.")
    scan_p.add_argument("--baseline", help="Path to baseline file (default: <path>/.pqc-radar/baseline.json).")
    scan_p.add_argument("--register", help="Path to register file (default: <path>/.pqc-radar/register.json).")
    scan_p.add_argument("--out", help="Where to write the JSON report (default: report.json).")
    scan_p.add_argument("--repo-name", help="Display name for the report/dashboard (default: directory name).")
    scan_p.add_argument("--save-baseline", action="store_true",
                         help="Write current findings into the baseline. Never implicit — see ARCHITECTURE.md.")
    scan_p.add_argument("--fail-on-new", action="store_true",
                         help="Exit non-zero if any unreviewed finding exists. Unused by CI in Phase 1; "
                              "present for the documented fast-follow (R8).")
    scan_p.set_defaults(func=cmd_scan)

    accept_p = sub.add_parser("accept", help="Mark a finding as a known, sanctioned, time-boxed risk.")
    accept_p.add_argument("path", help="Path to the repository (same path you ran `scan` against) — "
                                        "used to default the register location.")
    accept_p.add_argument("fingerprint", help="The finding's fingerprint, from a scan report.")
    accept_p.add_argument("--ticket", required=True, help="Tracking ticket/reference for this acceptance.")
    accept_p.add_argument("--review-by", required=True, help="ISO date (YYYY-MM-DD) this acceptance expires.")
    accept_p.add_argument("--reason", help="Optional free-text reason.")
    accept_p.add_argument("--register", help="Path to register file (default: <path>/.pqc-radar/register.json).")
    accept_p.set_defaults(func=cmd_accept)

    dash_p = sub.add_parser("dashboard", help="Render a static HTML dashboard from a JSON report.")
    dash_p.add_argument("report", help="Path to a report.json produced by `scan`.")
    dash_p.add_argument("--out", default="dashboard.html", help="Output HTML path (default: dashboard.html).")
    dash_p.set_defaults(func=cmd_dashboard)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, NotADirectoryError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: couldn't parse JSON — {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
