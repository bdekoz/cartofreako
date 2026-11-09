#!/bin/sh
# Python dependencies live in a repository-local environment, never sudo pip.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
if python3 "$root/scripts/check-atlas-prerequisites.py" >/dev/null 2>&1; then
  echo 'Scientific atlas dependencies are already available to python3.'
  exit 0
fi
python3 -m venv --system-site-packages "$root/.venv-data"
"$root/.venv-data/bin/python" -m pip install --requirement "$root/scripts/requirements-atlas.txt"
"$root/.venv-data/bin/python" "$root/scripts/check-atlas-prerequisites.py"
