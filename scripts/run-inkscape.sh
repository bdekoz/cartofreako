#!/usr/bin/env bash

# Run Inkscape directly when a session bus is available. Headless hosts
# without one, and parallel export jobs that would collide on the GApplication
# D-Bus name, run under an isolated per-invocation dbus-run-session instead of
# aborting with Gio::DBus::Error. If the isolated bus cannot start, fall back
# to a direct invocation.
set -euo pipefail

bus_address=${DBUS_SESSION_BUS_ADDRESS:-}
if [ -z "$bus_address" ] && [ -n "${XDG_RUNTIME_DIR:-}" ] && [ -S "$XDG_RUNTIME_DIR/bus" ]; then
  bus_address="unix:path=$XDG_RUNTIME_DIR/bus"
fi
if [ -n "$bus_address" ] || ! command -v dbus-run-session >/dev/null 2>&1; then
  exec "$@"
fi
dbus-run-session -- "$@"
status=$?
if [ "$status" -eq 126 ] || [ "$status" -eq 127 ]; then
  exec "$@"
fi
exit "$status"
exec "$@"
