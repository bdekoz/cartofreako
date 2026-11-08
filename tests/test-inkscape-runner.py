#!/usr/bin/env python3
"""Renderer failures must reach the caller instead of becoming success."""
import os
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as folder:
    runner=Path(folder)/'dbus-run-session'
    runner.write_text('#!/bin/sh\nshift\nexec "$@"\n');runner.chmod(0o755)
    env={**os.environ,'PATH':folder+os.pathsep+os.environ['PATH']}
    for expected in (0,23):
        result=subprocess.run(['bash',str(ROOT/'scripts/run-inkscape.sh'),'sh','-c',f'exit {expected}'],env=env)
        assert result.returncode==expected,(expected,result.returncode)
print('Isolated Inkscape runner preserves success and renderer failure codes')
