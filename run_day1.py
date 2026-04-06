#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
DAY1_DIR = PROJECT_DIR / "src" / "每日应用" / "day1-multi-agent-meeting-system"


def main() -> int:
    sys.path.insert(0, str(DAY1_DIR))
    module_path = DAY1_DIR / "main.py"
    spec = importlib.util.spec_from_file_location("day1_main", module_path)
    module = importlib.util.module_from_spec(spec)

    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载 Day 1 入口文件: {module_path}")

    spec.loader.exec_module(module)
    return module.main()


if __name__ == "__main__":
    raise SystemExit(main())
