import csv
import json
import os
import subprocess
import tempfile
from pathlib import Path

reports = Path("reports")
metrics_path = reports / "metrics.json"

if not metrics_path.exists():
    print("No coverage metrics. Trend was not created.")
    raise SystemExit(0)

current = json.loads(metrics_path.read_text(encoding="utf-8"))

repository = os.getenv("GITHUB_REPOSITORY", "")
default_branch = os.getenv("DEFAULT_BRANCH", "main")

previous = []


def gh(*args):
    result = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(
            result.stderr.strip() or "GitHub CLI error"
        )
    return result.stdout


if repository and os.getenv("GH_TOKEN"):
    try:
        raw = gh(
            "run", "list",
            "-R", repository,
            "--workflow", "02-coverage-advanced.yml",
            "--branch", default_branch,
            "--json", "databaseId,createdAt",
            "--limit", "20",
        )

        runs = json.loads(raw)

        with tempfile.TemporaryDirectory() as temporary:
            for run in runs:
                run_id = str(run["databaseId"])

                if run_id == str(current["run_id"]):
                    continue

                folder = Path(temporary) / run_id
                folder.mkdir()

                try:
                    gh(
                        "run", "download", run_id,
                        "-R", repository,
                        "--name", "lr5-coverage-metrics",
                        "--dir", str(folder),
                    )

                    found = list(folder.rglob("metrics.json"))

                    if not found:
                        continue

                    item = json.loads(
                        found[0].read_text(encoding="utf-8")
                    )
                    previous.append(item)

                    if len(previous) == 6:
                        break

                except (
                    RuntimeError,
                    OSError,
                    json.JSONDecodeError
                ) as error:
                    print(f"Skipping run {run_id}: {error}")

    except (
        RuntimeError,
        OSError,
        json.JSONDecodeError
    ) as error:
        print(f"Cannot load previous runs: {error}")


history = list(reversed(previous)) + [current]

reports.mkdir(exist_ok=True)

with (reports / "coverage-history.csv").open(
    "w", newline="", encoding="utf-8"
) as file:
    writer = csv.writer(file)
    writer.writerow([
        "run_id", "lines_percent", "branches_percent"
    ])

    for item in history:
        writer.writerow([
            item["run_id"],
            item["lines"],
            item["branches"],
        ])


def bar(percent):
    filled = round(float(percent) / 5)
    filled = max(0, min(20, filled))

    return "█" * filled + "░" * (20 - filled)


lines = [
    "## Coverage Trend",
    "",
    "| Run | Lines | Branches |",
    "|---|---|---|",
]

for item in history:
    run_id = str(item["run_id"])

    if run_id == str(current["run_id"]):
        name = f"Current (#{run_id})"
    else:
        name = f"#{run_id}"

    if repository and run_id.isdigit():
        name = (
            f"[{name}](https://github.com/"
            f"{repository}/actions/runs/{run_id})"
        )

    lines.append(
        f"| {name} | `{bar(item['lines'])}` "
        f"{item['lines']:.2f}%"
        f" | `{bar(item['branches'])}` "
        f"{item['branches']:.2f}% |"
    )

if len(history) == 1:
    lines.extend([
        "",
        "History will appear after the next workflow run "
        "on the default branch.",
    ])

summary = "\n".join(lines) + "\n"

print(summary)

summary_file = os.getenv("GITHUB_STEP_SUMMARY")

if summary_file:
    with open(summary_file, "a", encoding="utf-8") as file:
        file.write(summary)
