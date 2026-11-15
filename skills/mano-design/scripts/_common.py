"""共享工具：UTF-8 输出、路径。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def utf8_stdio():
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            try:
                s.reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass
