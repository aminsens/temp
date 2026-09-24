#!/usr/bin/env bash
# One-shot live DeepSeek validation runner (test-only, untracked).
#
# Credential rule: the API key must already be in the environment
# (export DEEPSEEK_API_KEY=...).  This script never stores, prints or
# embeds the key.
#
# Usage:
#   export DEEPSEEK_API_KEY=...
#   ./run_live_validation.sh
#
# Artifacts: live_validation/artifacts/live_<UTC-stamp>/
# Report:    docs/LIVE_DEEPSEEK_VALIDATION.md (via --write-docs, on)
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
if [ ! -x .venv-live/bin/python ]; then
  "$PYTHON" -m venv .venv-live
  .venv-live/bin/pip install -q pyyaml pytest requests
fi

export DEEPSEEK_MODEL="${DEEPSEEK_MODEL:-deepseek-flash}"
export DEEPSEEK_THINKING="${DEEPSEEK_THINKING:-enabled}"
export DEEPSEEK_REASONING_EFFORT="${DEEPSEEK_REASONING_EFFORT:-high}"
export DEEPSEEK_MAX_TOKENS="${DEEPSEEK_MAX_TOKENS:-1024}"

if [ -z "${DEEPSEEK_API_KEY:-}" ]; then
  echo "ERROR: set DEEPSEEK_API_KEY in the environment first (never in this script)." >&2
  exit 3
fi

exec .venv-live/bin/python live_harness.py --phase all --write-docs
