"""Background worker: issue addenda on a timer so the watch agent runs without the web process.

    WATCH_EVERY_SECONDS=3600 python3 scripts/watch_worker.py

On Render, use this as the worker service start command (same env and disk as the web service).
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import watch_loop  # noqa: E402

if __name__ == '__main__':
    every = int(os.getenv('WATCH_EVERY_SECONDS', '3600'))
    watch_loop(every)
