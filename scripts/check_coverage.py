import json
import os
import sys
from pathlib import Path

report = Path("reports/coverage.json")

if not report.is_file():
    sys.exit("ERROR: reports/coverage.json is missing")

totals = json.loads(
    report.read_text(encoding="utf-8")
)["totals"]

total_lines = totals["num_statements"]
covered_lines = totals["covered_lines"]
total_branches = totals["num_branches"]
covered_branches = totals["covered_branches"]

if total_lines == 0 or total_branches == 0:
    sys.exit("ERROR: no executable lines or branches to check")

lines = covered_lines / total_lines * 100
branches = covered_branches / total_branches * 100

minimum_lines = 80.0
minimum_branches = 70.0

lines_ok = lines >= minimum_lines
branches_ok = branches >= minimum_branches

metrics = {
    "run_id": os.getenv("GITHUB_RUN_ID", "local"),
    "lines": round(lines, 2),
    "branches": round(branches, 2),
    "lines_ok": lines_ok,
    "branches_ok": branches_ok,
}

output = Path("reports/metrics.json")
output.write_text(
    json.dumps(metrics, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print(f"Lines: {lines:.2f}% (required: {minimum_lines:.0f}%)")
print(f"Branches: {branches:.2f}% (required: {minimum_branches:.0f}%)")

result_lines = "PASS" if lines_ok else "FAIL"
result_branches = "PASS" if branches_ok else "FAIL"

summary = f"""## Coverage Quality Gate

| Metric | Actual | Minimum | Result |
|---|---:|---:|---|
| Lines | {lines:.2f}% | {minimum_lines:.0f}% | {result_lines} |
| Branches | {branches:.2f}% | {minimum_branches:.0f}% | {result_branches} |
"""

summary_file = os.getenv("GITHUB_STEP_SUMMARY")

if summary_file:
    with open(summary_file, "a", encoding="utf-8") as target:
        target.write(summary + "\n")
else:
    print(summary)

if not (lines_ok and branches_ok):
    sys.exit("ERROR: one or more coverage thresholds not reached")

print("SUCCESS: both coverage thresholds are reached")
