#!/usr/bin/env python3
"""Run Assignment14 multiple times and summarize DFS/BFS timings."""
import argparse
import os
import subprocess
from pathlib import Path
import json

PROVE_DIR = Path(__file__).resolve().parents[1]
LESSON_DIR = PROVE_DIR.parent
ASSIGNMENT_DIR = PROVE_DIR / "assignment14" / "Assignment14"
DEFAULT_LOG = LESSON_DIR / "assignment.log"
HISTORY_FILE = PROVE_DIR / "run_history.json"


def parse_latest(log_path: Path):
    lines = log_path.read_text().splitlines()
    times = []
    for line in lines:
        if "total_time" in line:
            try:
                times.append(float(line.split(":")[-1]))
            except ValueError:
                pass
    if len(times) >= 2:
        return times[-2], times[-1]
    raise RuntimeError("Log does not contain both DFS and BFS timings")


def load_history():
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text())
    return []


def save_history(history):
    HISTORY_FILE.write_text(json.dumps(history, indent=2))


def run_once():
    env = os.environ.copy()
    env["PATH"] = f"{env['HOME']}/.dotnet:" + env["PATH"]
    subprocess.run(["dotnet", "run"], cwd=str(ASSIGNMENT_DIR), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, env=env)


def main():
    parser = argparse.ArgumentParser(description="Run the Lesson14 solver multiple times and collect stats.")
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG, help="Path to assignment.log")
    parser.add_argument("--iterations", type=int, default=5, help="Number of runs to execute")
    parser.add_argument("--skip-run", action="store_true", help="Only summarize existing history without running new iterations")
    args = parser.parse_args()

    history = load_history()

    if not args.skip_run:
        for _ in range(args.iterations):
            run_once()
            dfs, bfs = parse_latest(args.log)
            history.append({"dfs": dfs, "bfs": bfs})
        save_history(history)

    total = len(history)
    dfs_under = sum(1 for entry in history if entry["dfs"] < 10)
    bfs_under = sum(1 for entry in history if entry["bfs"] < 10)
    both_under = sum(1 for entry in history if entry["dfs"] < 10 and entry["bfs"] < 10)

    print(f"Total recorded runs: {total}")
    if total:
        print(f"DFS < 10s: {dfs_under} ({dfs_under / total * 100:.1f}%)")
        print(f"BFS < 10s: {bfs_under} ({bfs_under / total * 100:.1f}%)")
        print(f"Both < 10s: {both_under} ({both_under / total * 100:.1f}%)")
    else:
        print("No runs recorded yet.")

    if not args.skip_run and args.iterations:
        latest = history[-args.iterations :]
        print("\nLatest runs:")
        start_idx = total - len(latest) + 1
        for offset, entry in enumerate(latest):
            print(f"Run {start_idx + offset:3d}: DFS={entry['dfs']:6.3f}s, BFS={entry['bfs']:6.3f}s")


if __name__ == "__main__":
    main()
