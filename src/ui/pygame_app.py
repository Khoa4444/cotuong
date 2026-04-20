from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import pygame

from engine.rules import game_status, generate_legal_moves, in_check
from engine.search import choose_move
from models.board import Board, side_of
from models.move import Move

Coord = Tuple[int, int]


PIECE_LABELS: Dict[str, str] = {
    "K": "K", "A": "A", "E": "E", "H": "H", "R": "R", "C": "C", "P": "P",
    "k": "k", "a": "a", "e": "e", "h": "h", "r": "r", "c": "c", "p": "p",
}


@dataclass(slots=True)
class UIState:
    selected: Optional[Coord] = None
    legal_from_selected: Optional[list[Move]] = None
    human_side: str = "r"   # human plays red by default
    ai_side: Optional[str] = "b"
    ai_time_ms: int = 600
    ai_max_depth: int = 5


class PygameApp:
    def __init__(self, board: Optional[Board] = None) -> None:
        self.board = board or Board.initial()
        self.state = UIState()

        self.cell = 64
        self.margin = 40
        self.w = self.margin * 2 + self.cell * 8
        self.h = self.margin * 2 + self.cell * 9

        pygame.init()
        self.screen = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption("Cờ Tướng (Xiangqi)")
        self.font = pygame.font.SysFont("Consolas", 28, bold=True)
        self.small = pygame.font.SysFont("Consolas", 18)
        self.clock = pygame.time.Clock()

    def run(self) -> None:
        running = True
        while running:
            running = self._handle_events()
            self._maybe_ai_move()
            self._draw()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()

    def _maybe_ai_move(self) -> None:
        if self.state.ai_side is None:
            return
        if self.board.side_to_move != self.state.ai_side:
            return
        if game_status(self.board) in ("checkmate", "stalemate"):
            return

        res = choose_move(self.board, side=self.state.ai_side, time_ms=self.state.ai_time_ms, max_depth=self.state.ai_max_depth)
        if res.best_move:
            self.board.make_move(res.best_move)
            self.state.selected = None
            self.state.legal_from_selected = None

    def _handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_u:
                    # Undo last ply (and also AI reply if present)
                    self.board.undo_move()
                    if self.state.ai_side is not None:
                        self.board.undo_move()
                    self.state.selected = None
                    self.state.legal_from_selected = None
                if event.key == pygame.K_r:
                    self.board = Board.initial()
                    self.state.selected = None
                    self.state.legal_from_selected = None
                if event.key == pygame.K_a:
                    # Toggle AI for black
                    self.state.ai_side = None if self.state.ai_side else "b"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._click(event.pos)
        return True

    def _click(self, pos: Tuple[int, int]) -> None:
        if game_status(self.board) in ("checkmate", "stalemate"):
            return
        if self.state.ai_side == self.board.side_to_move:
            return

        sq = self._pixel_to_square(pos)
        if sq is None:
            return

        r, c = sq
        piece = self.board.get(r, c)
        side = self.board.side_to_move

        # Select own piece
        if piece is not None and side_of(piece) == side:
            self.state.selected = (r, c)
            legal = generate_legal_moves(self.board, side)
            self.state.legal_from_selected = [m for m in legal if m.fr == (r, c)]
            return

        # If selected, try move
        if self.state.selected and self.state.legal_from_selected:
            for mv in self.state.legal_from_selected:
                if mv.to == (r, c):
                    self.board.make_move(mv)
                    self.state.selected = None
                    self.state.legal_from_selected = None
                    return

        # Clicking empty or opponent piece clears selection
        self.state.selected = None
        self.state.legal_from_selected = None

    def _square_to_pixel(self, r: int, c: int) -> Tuple[int, int]:
        x = self.margin + c * self.cell
        y = self.margin + r * self.cell
        return x, y

    def _pixel_to_square(self, pos: Tuple[int, int]) -> Optional[Coord]:
        x, y = pos
        x0, y0 = self.margin, self.margin
        if x < x0 - self.cell * 0.4 or y < y0 - self.cell * 0.4:
            return None
        c = round((x - x0) / self.cell)
        r = round((y - y0) / self.cell)
        if 0 <= r < 10 and 0 <= c < 9:
            return (r, c)
        return None

    def _draw(self) -> None:
        self.screen.fill((245, 222, 179))

        # grid lines
        for r in range(10):
            x1, y = self._square_to_pixel(r, 0)
            x2, _ = self._square_to_pixel(r, 8)
            pygame.draw.line(self.screen, (60, 40, 20), (x1, y), (x2, y), 2)
        for c in range(9):
            x, y1 = self._square_to_pixel(0, c)
            _, y2 = self._square_to_pixel(9, c)
            pygame.draw.line(self.screen, (60, 40, 20), (x, y1), (x, y2), 2)

        # river label
        river_y = (self._square_to_pixel(4, 0)[1] + self._square_to_pixel(5, 0)[1]) // 2
        label = self.small.render("楚河 / 漢界", True, (70, 50, 30))
        self.screen.blit(label, (self.w // 2 - label.get_width() // 2, river_y - label.get_height() // 2))

        # highlights for selected and legal targets
        if self.state.selected:
            self._draw_highlight(self.state.selected, (0, 120, 255))
        if self.state.legal_from_selected:
            for mv in self.state.legal_from_selected:
                self._draw_target(mv.to)

        # pieces
        for r in range(10):
            for c in range(9):
                p = self.board.get(r, c)
                if not p:
                    continue
                self._draw_piece((r, c), p)

        # status text
        status = game_status(self.board)
        stm = "RED" if self.board.side_to_move == "r" else "BLACK"
        check = " (CHECK)" if in_check(self.board, self.board.side_to_move) else ""
        ai = "AI: ON" if self.state.ai_side else "AI: OFF"
        text = f"Turn: {stm}{check} | {status.upper()} | {ai}  (U=undo, R=reset, A=toggle AI)"
        surf = self.small.render(text, True, (30, 20, 10))
        self.screen.blit(surf, (10, 10))

    def _draw_piece(self, sq: Coord, piece: str) -> None:
        r, c = sq
        x, y = self._square_to_pixel(r, c)
        radius = int(self.cell * 0.38)
        color = (220, 60, 60) if piece.isupper() else (40, 40, 40)
        pygame.draw.circle(self.screen, (250, 245, 235), (x, y), radius + 4)
        pygame.draw.circle(self.screen, color, (x, y), radius, 3)
        label = PIECE_LABELS.get(piece, piece)
        surf = self.font.render(label, True, color)
        self.screen.blit(surf, (x - surf.get_width() // 2, y - surf.get_height() // 2))

    def _draw_highlight(self, sq: Coord, color: Tuple[int, int, int]) -> None:
        r, c = sq
        x, y = self._square_to_pixel(r, c)
        pygame.draw.circle(self.screen, color, (x, y), int(self.cell * 0.46), 3)

    def _draw_target(self, sq: Coord) -> None:
        r, c = sq
        x, y = self._square_to_pixel(r, c)
        pygame.draw.circle(self.screen, (0, 180, 80), (x, y), int(self.cell * 0.12))

