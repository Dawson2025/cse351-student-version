#!/usr/bin/env python3
import subprocess
import sys

repo_path = "/home/dawson/code/Parallelism and Concurrency/real/cse351-student-version"

# Get commits in upstream/main that aren't in personal-version
print("=" * 60)
print("Commits in upstream/main but not in personal-version:")
print("=" * 60)
result = subprocess.run(
    ['git', 'log', '--oneline', 'personal-version..upstream/main'],
    cwd=repo_path,
    capture_output=True,
    text=True
)
print(result.stdout)
print()

# Get files that differ
print("=" * 60)
print("Files that differ (lesson_08 only):")
print("=" * 60)
result = subprocess.run(
    ['git', 'diff', '--name-status', 'personal-version', 'upstream/main'],
    cwd=repo_path,
    capture_output=True,
    text=True
)
lesson08_files = [line for line in result.stdout.split('\n') if 'lesson_08' in line]
for line in lesson08_files:
    print(line)
print()

# Get summary stats
print("=" * 60)
print("Summary statistics:")
print("=" * 60)
result = subprocess.run(
    ['git', 'diff', '--shortstat', 'personal-version', 'upstream/main'],
    cwd=repo_path,
    capture_output=True,
    text=True
)
print(result.stdout)

