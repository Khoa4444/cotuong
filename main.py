# Main entry point for Xiangqi Game
from __future__ import annotations

import os
import sys


def _ensure_src_on_path() -> None:
    root = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(root, "src")
    if src not in sys.path:
        sys.path.insert(0, src)


def main() -> None:
    _ensure_src_on_path()
    from ui.pygame_app import PygameApp  # type: ignore

    app = PygameApp()
    app.run()


if __name__ == "__main__":
    main()
