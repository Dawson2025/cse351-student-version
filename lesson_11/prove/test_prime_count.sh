#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${SCRIPT_DIR}/Assignment11"
WORKERS="${WORKERS:-10}"

echo "Running Lesson 11 prime check (workers=${WORKERS})..."
OUTPUT="$(dotnet run --configuration Release --project "${PROJECT_DIR}" -- --quiet "${WORKERS}")"

# Show the tail to surface summary info while keeping output small
echo "${OUTPUT}" | tail -n 6

EXPECTED=43427
PRIMES="$(echo "${OUTPUT}" | grep "Primes found" | awk '{print $4}')"

if [[ "${PRIMES}" != "${EXPECTED}" ]]; then
  echo "Expected ${EXPECTED} primes, got ${PRIMES}" >&2
  exit 1
fi

echo "Prime count OK (${PRIMES})"
