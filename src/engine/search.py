from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from models.board import Board, piece_type, side_of
from models.move import Move
from engine.rules import game_status, generate_legal_moves, in_check, opponent


PIECE_VALUES = {
    "K": 20000,
    "R": 900,
    "C": 450,
    "H": 400,
    "E": 200,
    "A": 200,
    "P": 100,
}


def evaluate(board: Board, perspective: str) -> int:
    # Positive means good for perspective.
    score = 0
    for r in range(10):
        for c in range(9):
            p = board.get(r, c)
            if not p:
                continue
            val = PIECE_VALUES[piece_type(p)]
            score += val if side_of(p) == perspective else -val
    # Small check bonus/penalty
    if in_check(board, opponent(perspective)):
        score += 20
    if in_check(board, perspective):
        score -= 20
    return score


def _move_order_key(mv: Move) -> int:
    # Captures first.
    return 1 if mv.captured else 0


@dataclass(slots=True)
class SearchResult:
    best_move: Optional[Move]
    score: int
    depth: int
    nodes: int


def choose_move(board: Board, side: Optional[str] = None, time_ms: int = 600, max_depth: int = 5) -> SearchResult:
    side = side or board.side_to_move
    deadline = time.perf_counter() + (time_ms / 1000.0)
    nodes = 0

    def timed_out() -> bool:
        return time.perf_counter() >= deadline

    # Simple transposition keyed by (side_to_move, grid string)
    tt: Dict[Tuple[str, str], Tuple[int, int]] = {}

    def key_of(b: Board) -> Tuple[str, str]:
        parts = []
        for r in range(10):
            for c in range(9):
                parts.append(b.get(r, c) or ".")
        return (b.side_to_move, "".join(parts))

    def negamax(depth: int, alpha: int, beta: int, perspective_side: str) -> int:
        nonlocal nodes
        nodes += 1

        if timed_out():
            return evaluate(board, perspective_side)

        status = game_status(board, board.side_to_move)
        if status == "checkmate":
            # side_to_move has no moves and is in check -> losing for side_to_move
            return -20000 + (max_depth - depth)
        if status == "stalemate":
            return 0

        if depth == 0:
            return evaluate(board, perspective_side)

        k = key_of(board)
        if k in tt and tt[k][1] >= depth:
            return tt[k][0]

        best = -math.inf
        moves = generate_legal_moves(board, board.side_to_move)
        moves.sort(key=_move_order_key, reverse=True)
        for mv in moves:
            board.make_move(mv)
            val = -negamax(depth - 1, -beta, -alpha, perspective_side)
            board.undo_move()
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        tt[k] = (int(best), depth)
        return int(best)

    best_move: Optional[Move] = None
    best_score = -math.inf
    last_complete_depth = 0

    for depth in range(1, max_depth + 1):
        if timed_out():
            break
        moves = generate_legal_moves(board, side)
        moves.sort(key=_move_order_key, reverse=True)
        local_best_move = None
        local_best_score = -math.inf
        alpha, beta = -30000, 30000

        for mv in moves:
            if timed_out():
                break
            board.make_move(mv)
            val = -negamax(depth - 1, -beta, -alpha, side)
            board.undo_move()
            if val > local_best_score:
                local_best_score = val
                local_best_move = mv
            if val > alpha:
                alpha = val

        if local_best_move is not None and not timed_out():
            best_move = local_best_move
            best_score = int(local_best_score)
            last_complete_depth = depth

    return SearchResult(best_move=best_move, score=int(best_score if best_move else evaluate(board, side)), depth=last_complete_depth, nodes=nodes)

