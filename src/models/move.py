from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


Coord = Tuple[int, int]  # (row, col)


@dataclass(frozen=True, slots=True)
class Move:
    fr: Coord
    to: Coord
    captured: Optional[str] = None

    def uci_like(self) -> str:
        # Not standard Xiangqi notation; stable debug string.
        return f"{self.fr[0]}{self.fr[1]}-{self.to[0]}{self.to[1]}"

