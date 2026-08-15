#!/usr/bin/env bash

# Run Inkscape under an isolated per-invocation dbus-run-session so parallel
# export jobs never collide on the GApplication D-Bus name, regardless of an
# existing session bus or Inkscape --app-id-tag support. If the isolated bus
# cannot start, or dbus-run-session is unavailable, fall back to a direct
# invocation.
set -euo pipefail

if ! command -v dbus-run-session >/dev/null 2>&1; then
  exec "$@"
fi

if dbus-run-session -- "$@"; then
  exit 0
fi
status=$?
if [ "$status" -eq 126 ] || [ "$status" -eq 127 ]; then
  exec "$@"
fi
exit "$status"
