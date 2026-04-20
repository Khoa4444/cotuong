from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

from models.board import Board, is_red, piece_type, side_of
from models.move import Move

Coord = Tuple[int, int]


def opponent(side: str) -> str:
    return "b" if side == "r" else "r"


def palace_contains(side: str, r: int, c: int) -> bool:
    if not (3 <= c <= 5):
        return False
    if side == "b":
        return 0 <= r <= 2
    return 7 <= r <= 9


def crossed_river(side: str, r: int) -> bool:
    # For red moving up (decreasing row), river is between rows 4 and 5.
    # Red crosses when r <= 4. Black crosses when r >= 5.
    return (side == "r" and r <= 4) or (side == "b" and r >= 5)


def iter_squares_line(board: Board, fr: Coord, delta: Coord) -> Iterable[Coord]:
    r, c = fr
    dr, dc = delta
    r += dr
    c += dc
    while board.in_bounds(r, c):
        yield (r, c)
        r += dr
        c += dc


def generate_pseudo_legal_moves(board: Board, side: str) -> List[Move]:
    moves: List[Move] = []
    for r in range(10):
        for c in range(9):
            p = board.get(r, c)
            if not p:
                continue
            if side_of(p) != side:
                continue
            moves.extend(_piece_moves(board, (r, c), p))
    return moves


def generate_legal_moves(board: Board, side: Optional[str] = None) -> List[Move]:
    side = side or board.side_to_move
    out: List[Move] = []
    for mv in generate_pseudo_legal_moves(board, side):
        board.make_move(mv)
        illegal = in_check(board, side) or flying_generals(board)
        board.undo_move()
        if not illegal:
            out.append(mv)
    return out


def flying_generals(board: Board) -> bool:
    rk = board.find_king("r")
    bk = board.find_king("b")
    if rk[1] != bk[1]:
        return False
    col = rk[1]
    r1, r2 = sorted([rk[0], bk[0]])
    for r in range(r1 + 1, r2):
        if board.get(r, col) is not None:
            return False
    return True


def in_check(board: Board, side: str) -> bool:
    kpos = board.find_king(side)
    return is_attacked(board, kpos, opponent(side))


def is_attacked(board: Board, square: Coord, by_side: str) -> bool:
    # Generate pseudo moves for attacker and see if any ends on square.
    # This is slower but simple; for Xiangqi board it's fine for small depths.
    for mv in generate_pseudo_legal_moves(board, by_side):
        if mv.to == square:
            return True
    return False


def game_status(board: Board, side: Optional[str] = None) -> str:
    side = side or board.side_to_move
    legal = generate_legal_moves(board, side)
    if legal:
        return "check" if in_check(board, side) else "ok"
    return "checkmate" if in_check(board, side) else "stalemate"


def _maybe_add(board: Board, moves: List[Move], fr: Coord, to: Coord, side: str) -> None:
    tr, tc = to
    if not board.in_bounds(tr, tc):
        return
    target = board.get(tr, tc)
    if target is None:
        moves.append(Move(fr, to, None))
    else:
        if side_of(target) != side:
            moves.append(Move(fr, to, target))


def _piece_moves(board: Board, fr: Coord, p: str) -> List[Move]:
    side = side_of(p)
    t = piece_type(p)
    r, c = fr
    moves: List[Move] = []

    if t == "R":  # rook
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            for tr, tc in iter_squares_line(board, fr, (dr, dc)):
                target = board.get(tr, tc)
                if target is None:
                    moves.append(Move(fr, (tr, tc), None))
                else:
                    if side_of(target) != side:
                        moves.append(Move(fr, (tr, tc), target))
                    break
        return moves

    if t == "C":  # cannon
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            screened = False
            for tr, tc in iter_squares_line(board, fr, (dr, dc)):
                target = board.get(tr, tc)
                if not screened:
                    if target is None:
                        moves.append(Move(fr, (tr, tc), None))
                    else:
                        screened = True
                else:
                    if target is None:
                        continue
                    if side_of(target) != side:
                        moves.append(Move(fr, (tr, tc), target))
                    break
        return moves

    if t == "H":  # horse (knight) with leg blocking
        # (delta_to, delta_leg)
        patterns = [
            ((-2, -1), (-1, 0)),
            ((-2, 1), (-1, 0)),
            ((2, -1), (1, 0)),
            ((2, 1), (1, 0)),
            ((-1, -2), (0, -1)),
            ((1, -2), (0, -1)),
            ((-1, 2), (0, 1)),
            ((1, 2), (0, 1)),
        ]
        for (dr, dc), (lr, lc) in patterns:
            leg_r, leg_c = r + lr, c + lc
            if not board.in_bounds(leg_r, leg_c) or board.get(leg_r, leg_c) is not None:
                continue
            _maybe_add(board, moves, fr, (r + dr, c + dc), side)
        return moves

    if t == "E":  # elephant/bishop: 2 diagonal, cannot cross river, eye blocking
        for dr, dc in ((-2, -2), (-2, 2), (2, -2), (2, 2)):
            tr, tc = r + dr, c + dc
            if not board.in_bounds(tr, tc):
                continue
            # River constraint
            if side == "r" and tr < 5:
                continue
            if side == "b" and tr > 4:
                continue
            eye_r, eye_c = r + dr // 2, c + dc // 2
            if board.get(eye_r, eye_c) is not None:
                continue
            _maybe_add(board, moves, fr, (tr, tc), side)
        return moves

    if t == "A":  # advisor/guard: 1 diagonal within palace
        for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            tr, tc = r + dr, c + dc
            if palace_contains(side, tr, tc):
                _maybe_add(board, moves, fr, (tr, tc), side)
        return moves

    if t == "K":  # king/general
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            tr, tc = r + dr, c + dc
            if palace_contains(side, tr, tc):
                _maybe_add(board, moves, fr, (tr, tc), side)
        # Flying capture of opposing king if facing with no pieces between.
        ok = board.find_king(opponent(side))
        if ok[1] == c:
            r1, r2 = sorted([r, ok[0]])
            clear = True
            for rr in range(r1 + 1, r2):
                if board.get(rr, c) is not None:
                    clear = False
                    break
            if clear:
                moves.append(Move(fr, ok, board.get(ok[0], ok[1])))
        return moves

    if t == "P":  # pawn/soldier
        forward = -1 if side == "r" else 1
        _maybe_add(board, moves, fr, (r + forward, c), side)
        if crossed_river(side, r):
            _maybe_add(board, moves, fr, (r, c - 1), side)
            _maybe_add(board, moves, fr, (r, c + 1), side)
        return moves

    return moves

