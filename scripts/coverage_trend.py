
import csv
import json
import os
import subprocess
import tempfile
from pathlib import Path

reports = Path("reports")
metrics_file = reports / "metrics.json"

if not metrics_file.exists():
    raise SystemExit("No metrics.json found")

current = json.loads(
    metrics_file.read_text(encoding="utf-8")
)

repository = os.getenv("GITHUB_REPOSITORY", "")
default_branch = os.getenv("DEFAULT_BRANCH", "main")

previous = []


def gh(*args):
    result = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip() or "GitHub CLI error"
        )

    return result.stdout


if repository and os.getenv("GH_TOKEN"):
    try:
        raw = gh(
            "api",
            f"repos/{repository}/actions/artifacts"
            "?name=lr5-coverage-metrics&per_page=100",
        )

        artifacts = json.loads(raw).get("artifacts", [])

        print(f"Found metric artifacts: {len(artifacts)}")

        seen_runs = set()

        with tempfile.TemporaryDirectory() as temporary:
            for artifact in artifacts:
                workflow = artifact.get("workflow_run") or {}

                run_id = str(workflow.get("id", ""))
                branch = workflow.get("head_branch", "")

                if not run_id:
                    continue

                if run_id == str(current["run_id"]):
                    continue

                if run_id in seen_runs:
                    continue

                if branch != default_branch:
                    continue

                if artifact.get("expired", False):
                    continue

                folder = Path(temporary) / run_id
                folder.mkdir(parents=True, exist_ok=True)

                try:
                    gh(
                        "run",
                        "download",
                        run_id,
                        "-R",
                        repository,
                        "--name",
                        "lr5-coverage-metrics",
                        "--dir",
                        str(folder),
                    )

                    files = list(folder.rglob("metrics.json"))

                    if not files:
                        print(
                            f"Run {run_id}: metrics.json missing"
                        )
                        continue

                    data = json.loads(
                        files[0].read_text(encoding="utf-8")
                    )

                    previous.append(data)
                    seen_runs.add(run_id)

                    print(f"Loaded history from run {run_id}")

                    if len(previous) >= 6:
                        break

                except (
                    RuntimeError,
                    OSError,
                    json.JSONDecodeError,
                ) as error:
                    print(
                        f"Run {run_id}: download failed: {error}"
                    )

    except (
        RuntimeError,
        OSError,
        json.JSONDecodeError,
    ) as error:
        print(f"History loading error: {error}")

else:
    print("GitHub token or repository is unavailable")


history = list(reversed(previous)) + [current]

print(f"Total runs in history: {len(history)}")

reports.mkdir(parents=True, exist_ok=True)

# Save CSV for Excel
with (reports / "coverage-history.csv").open(
    "w",
    newline="",
    encoding="utf-8-sig",
) as file:
    writer = csv.writer(file, delimiter=";")

    writer.writerow([
        "run_id",
        "lines_percent",
        "branches_percent",
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
        f"{item['lines']:.2f}% | "
        f"`{bar(item['branches'])}` "
        f"{item['branches']:.2f}% |"
    )

if len(history) == 1:
    lines.append("")
    lines.append(
        "No previous coverage artifacts were found."
    )

summary = "\n".join(lines) + "\n"

print(summary)

summary_file = os.getenv("GITHUB_STEP_SUMMARY")

if summary_file:
    with open(summary_file, "a", encoding="utf-8") as file:
        file.write(summary)
