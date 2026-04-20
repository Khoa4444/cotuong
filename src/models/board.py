from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .move import Move

Coord = Tuple[int, int]


def is_red(piece: str) -> bool:
    return piece.isupper()


def side_of(piece: str) -> str:
    return "r" if is_red(piece) else "b"


def piece_type(piece: str) -> str:
    return piece.upper()


@dataclass(slots=True)
class Undo:
    move: Move
    moved_piece: str
    prev_side_to_move: str


@dataclass(slots=True)
class Board:
    # 10 rows x 9 cols
    grid: List[List[Optional[str]]] = field(default_factory=lambda: [[None] * 9 for _ in range(10)])
    side_to_move: str = "r"  # 'r' red, 'b' black
    history: List[Undo] = field(default_factory=list)

    @staticmethod
    def initial() -> "Board":
        b = Board()
        # Black side at top (rows 0..4), Red at bottom (rows 5..9).
        # Pieces: K/A/E/H/R/C/P  (king/advisor/elephant/horse/rook/cannon/pawn)
        # Black
        b._put(0, 0, "r"); b._put(0, 8, "r")
        b._put(0, 1, "h"); b._put(0, 7, "h")
        b._put(0, 2, "e"); b._put(0, 6, "e")
        b._put(0, 3, "a"); b._put(0, 5, "a")
        b._put(0, 4, "k")
        b._put(2, 1, "c"); b._put(2, 7, "c")
        for col in (0, 2, 4, 6, 8):
            b._put(3, col, "p")

        # Red
        b._put(9, 0, "R"); b._put(9, 8, "R")
        b._put(9, 1, "H"); b._put(9, 7, "H")
        b._put(9, 2, "E"); b._put(9, 6, "E")
        b._put(9, 3, "A"); b._put(9, 5, "A")
        b._put(9, 4, "K")
        b._put(7, 1, "C"); b._put(7, 7, "C")
        for col in (0, 2, 4, 6, 8):
            b._put(6, col, "P")

        b.side_to_move = "r"
        return b

    def _put(self, r: int, c: int, piece: str) -> None:
        self.grid[r][c] = piece

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < 10 and 0 <= c < 9

    def get(self, r: int, c: int) -> Optional[str]:
        return self.grid[r][c]

    def set(self, r: int, c: int, piece: Optional[str]) -> None:
        self.grid[r][c] = piece

    def find_king(self, side: str) -> Coord:
        target = "K" if side == "r" else "k"
        for r in range(10):
            for c in range(9):
                if self.grid[r][c] == target:
                    return (r, c)
        raise ValueError(f"King not found for side {side}")

    def make_move(self, mv: Move) -> None:
        fr_r, fr_c = mv.fr
        to_r, to_c = mv.to
        moved = self.get(fr_r, fr_c)
        if moved is None:
            raise ValueError("No piece to move")
        captured = self.get(to_r, to_c)
        self.history.append(Undo(move=Move(mv.fr, mv.to, captured=captured), moved_piece=moved, prev_side_to_move=self.side_to_move))
        self.set(fr_r, fr_c, None)
        self.set(to_r, to_c, moved)
        self.side_to_move = "b" if self.side_to_move == "r" else "r"

    def undo_move(self) -> None:
        if not self.history:
            return
        u = self.history.pop()
        fr_r, fr_c = u.move.fr
        to_r, to_c = u.move.to
        self.set(to_r, to_c, u.move.captured)
        self.set(fr_r, fr_c, u.moved_piece)
        self.side_to_move = u.prev_side_to_move

