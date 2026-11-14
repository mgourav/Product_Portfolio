"""
Command-line entry point. Three subcommands, matching ARCHITECTURE.md's CLI
surface exactly:

    pqc-radar scan <path> [--baseline FILE] [--register FILE]
                           [--save-baseline] [--out report.json]
                           [--fail-on-new] [--repo-name NAME]
    pqc-radar accept <fingerprint> --ticket T --review-by YYYY-MM-DD [--reason TEXT]
                      [--register FILE]
    pqc-radar dashboard <report.json> [--out dashboard.html]

Run as `python -m pqc_radar <subcommand> ...` or via the `pqc-radar` console
script once installed.
"""

import argparse
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

    current = scan_path(scan_target)
    existing_baseline = baseline_mod.load_baseline(baseline_path)
    diff_result = baseline_mod.diff(current, existing_baseline)
    reg = register_mod.load_register(register_path)

    repo_name = args.repo_name or Path(scan_target).resolve().name
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
    register_path = Path(args.register)
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
    accept_p.add_argument("fingerprint", help="The finding's fingerprint, from a scan report.")
    accept_p.add_argument("--ticket", required=True, help="Tracking ticket/reference for this acceptance.")
    accept_p.add_argument("--review-by", required=True, help="ISO date (YYYY-MM-DD) this acceptance expires.")
    accept_p.add_argument("--reason", help="Optional free-text reason.")
    accept_p.add_argument("--register", required=True, help="Path to the register file to update.")
    accept_p.set_defaults(func=cmd_accept)

    dash_p = sub.add_parser("dashboard", help="Render a static HTML dashboard from a JSON report.")
    dash_p.add_argument("report", help="Path to a report.json produced by `scan`.")
    dash_p.add_argument("--out", default="dashboard.html", help="Output HTML path (default: dashboard.html).")
    dash_p.set_defaults(func=cmd_dashboard)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
