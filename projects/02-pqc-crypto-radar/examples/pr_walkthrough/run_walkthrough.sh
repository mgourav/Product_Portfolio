#!/usr/bin/env bash
# PR walkthrough: four realistic scenarios for Crypto Radar, run against a
# single evolving file (src/payments_service.py) so the story reads like
# an actual repo's history, not four unrelated snippets.
#
# Run from the project root (projects/02-pqc-crypto-radar):
#   bash examples/pr_walkthrough/run_walkthrough.sh
#
# It's safe to re-run — .work/ is scratch and gets wiped at the start.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$ROOT/../.." && pwd)"
WORK="$ROOT/.work"
SNAP="$ROOT/snapshots"
FINAL="$ROOT/final"

cd "$PROJECT_ROOT"
rm -rf "$WORK"
mkdir -p "$WORK/src"

banner() { echo; echo "=================================================================="; echo "$1"; echo "=================================================================="; }

run_scan() {
    # run_scan <label> <report-file> [extra scan args...]
    local label="$1" out="$2"; shift 2
    echo "--- $label ---"
    python3 -m pqc_radar scan "$WORK" --repo-name pr-walkthrough --out "$out" "$@"
    echo
}

fp_for() {
    # fp_for <report-file> <algorithm> — first matching fingerprint, via stdlib json (no jq dependency)
    python3 -c "
import json, sys
rep = json.load(open(sys.argv[1]))
for f in rep['findings']:
    if f['algorithm'] == sys.argv[2]:
        print(f['fingerprint']); break
" "$1" "$2"
}

# --------------------------------------------------------------------------
banner "Step 0 — establish main's baseline (hashlib.sha256 only, nothing alarming)"
cp "$SNAP/00_main/src/"* "$WORK/src/"
run_scan "baseline scan" "$WORK/report_00_main.json" --save-baseline

# --------------------------------------------------------------------------
banner "Scenario 1 — PR introduces a quantum-vulnerable algorithm (RSA signing key)"
cp "$SNAP/01_pr_rsa_signing/src/"* "$WORK/src/"
run_scan "PR gate: scan the branch, baseline NOT touched" "$WORK/report_01a_gate.json"

FP_RSA="$(fp_for "$WORK/report_01a_gate.json" RSA)"
echo "RSA fingerprint: $FP_RSA"
echo "Team decides this is a known, time-boxed exception (ticket SEC-900) and files it:"
python3 -m pqc_radar accept "$WORK" "$FP_RSA" --ticket SEC-900 --review-by 2026-12-15 \
    --reason "RSA token signing retiring once ML-DSA receipt signing ships; tracked for removal."
echo
run_scan "Re-scan after the ticket is filed, then merge (baseline updated)" "$WORK/report_01b_merge.json" --save-baseline

# --------------------------------------------------------------------------
banner "Scenario 2 — PR introduces a PQC-ready algorithm (ML-KEM/Kyber) and nothing else"
cp "$SNAP/02_pr_pqc_kyber/src/"* "$WORK/src/"
run_scan "PR gate + immediate merge (nothing to review, just progress)" "$WORK/report_02.json" --save-baseline

# --------------------------------------------------------------------------
banner "Scenario 3 — PR introduces BOTH an unsafe algorithm (ECDSA) and a PQC-ready one (ML-DSA)"
cp "$SNAP/03_pr_ecc_and_dilithium/src/"* "$WORK/src/"
run_scan "PR gate: scan the branch, baseline NOT touched" "$WORK/report_03a_gate.json"

FP_ECC="$(fp_for "$WORK/report_03a_gate.json" "ECC/ECDSA/ECDH")"
echo "ECC fingerprint: $FP_ECC"
echo "Team accepts this as a time-boxed partner exception (ticket SEC-905):"
python3 -m pqc_radar accept "$WORK" "$FP_ECC" --ticket SEC-905 --review-by 2026-12-15 \
    --reason "Partner X's integration requires ECDSA until their own PQC migration lands."
echo
run_scan "Re-scan after the ticket is filed, then merge (baseline updated)" "$WORK/report_03b_merge.json" --save-baseline

# --------------------------------------------------------------------------
banner "Cleanup PR — RSA signing is fully retired; generate_signing_key() is deleted"
cp "$SNAP/04a_cleanup_remove_rsa/src/"* "$WORK/src/"
run_scan "RSA drops out of the findings entirely; merge" "$WORK/report_04a_cleanup.json" --save-baseline

echo "--- simulating the passage of time ---"
echo "The register never auto-prunes an entry just because its code disappeared (SEC-900 is"
echo "still sitting there, accepted through 2026-12-15, for code that no longer exists). To"
echo "demonstrate what happens once that review date has genuinely passed — without waiting"
echo "for the calendar — we hand-edit the register file the same way examples/sample_app does:"
PY_REGISTER="$WORK/.pqc-radar/register.json"
python3 -c "
import json
path = '$PY_REGISTER'
data = json.load(open(path))
for fp, entry in data['entries'].items():
    if entry['ticket'] == 'SEC-900':
        entry['review_by'] = '2026-10-01'
json.dump(data, open(path, 'w'), indent=2)
open(path, 'a').write('\n')
"
echo "SEC-900's review_by backdated to 2026-10-01 (already past) in $PY_REGISTER"
echo

# --------------------------------------------------------------------------
banner "Scenario 4 — a revised PR reintroduces the SAME RSA call, months later"
cp "$SNAP/04b_pr_rsa_regression/src/"* "$WORK/src/"
run_scan "PR gate: scan the branch, baseline NOT touched" "$WORK/report_04b_regression.json"

banner "Final dashboard (built from Scenario 4's report — the most complete state)"
python3 -m pqc_radar dashboard "$WORK/report_04b_regression.json" --out "$FINAL/dashboard.html"
cp "$WORK/report_04b_regression.json" "$FINAL/report.json"
echo "Committed artifacts refreshed: $FINAL/report.json, $FINAL/dashboard.html"
