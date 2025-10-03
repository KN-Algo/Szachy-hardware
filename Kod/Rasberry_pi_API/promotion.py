# promotion.py
from dataclasses import dataclass
from typing import Dict, List, Tuple

from config import (
    BOARD_ORIGIN_X_MM,
    BOARD_ORIGIN_Y_MM,
    FEN_SYMBOLS,
    FILES,
    LANE_OFFSET,
    SQUARE_SIZE,
    START_COUNTS,
)
from square_to_cords import square_to_coords
from steps import Step


def left_file_index_for(color: str) -> int:
    return 0 if color == "white" else 7


def right_file_index_for(color: str) -> int:
    return 7 if color == "white" else 0


def front_outside_rank_for(color: str) -> int:
    # „przed planszą” (w stronę gracza): białe -1, czarne 8
    return -1 if color == "white" else 8


def left_outside_file_for(color: str) -> int:
    # „lewa krawędź” poza planszą: białe x=-1, czarne x=8
    return -1 if color == "white" else 8


def away_dir_for(color: str) -> int:
    # od gracza w dal: białe +1, czarne -1 (po osi rank)
    return +1 if color == "white" else -1


def order_files_left_preferred(files: List[int], color: str) -> List[int]:
    # preferencja lewej strony: białe rosnąco (a..h), czarne malejąco (h..a)
    return sorted(files, reverse=(color == "black"))


def starting_files_for_piece(piece: str, color: str) -> List[int]:
    p = piece.lower()
    if p == "rook":
        lst = [left_file_index_for(color), right_file_index_for(color)]
    elif p == "knight":
        lst = [1, 6]
    elif p == "bishop":
        lst = [2, 5]
    elif p == "queen":
        lst = [3]
    elif p == "king":
        lst = [4]
    else:
        lst = list(range(8))
    return order_files_left_preferred(lst, color)


# --- FEN -> liczniki ---
def counts_from_fen(fen: str) -> Dict[str, Dict[str, int]]:
    board = fen.split()[0]
    counts = {
        "white": {k: 0 for k in START_COUNTS},
        "black": {k: 0 for k in START_COUNTS},
    }
    for ch in board:
        if ch == "/" or ch.isdigit():
            continue
        cp = FEN_SYMBOLS.get(ch)
        if cp:
            color, piece = cp
            counts[color][piece] += 1
    return counts


def captured_counts_from_fen(fen: str) -> Dict[str, Dict[str, int]]:
    present = counts_from_fen(fen)
    captured = {"white": {}, "black": {}}
    for color in ("white", "black"):
        for piece, start_n in START_COUNTS.items():
            captured[color][piece] = max(0, start_n - present[color][piece])
    return captured


# --- parking pionków (gdzie odwozimy pionka) ---
def pawn_parking_mm_for_color_from_fen(color: str, fen: str) -> Tuple[float, float]:
    """
    Pionka odkładamy na „lewej” krawędzi planszy jego koloru.
    Slot = (liczba już „odłożonych” pionków tego koloru po ruchu) - 1.
    """
    caps = captured_counts_from_fen(fen)
    k = caps[color]["pawn"] - 1
    if k < 0:
        k = 0
    x_file = left_outside_file_for(color)
    base_rank = 0 if color == "white" else 7
    y_rank = base_rank + away_dir_for(color) * k
    x_mm = x_file * SQUARE_SIZE + BOARD_ORIGIN_X_MM
    y_mm = y_rank * SQUARE_SIZE + BOARD_ORIGIN_Y_MM

    return x_mm, y_mm


# --- parking figur (skąd bierzemy promowaną figurę) ---
def piece_parking_pick_mm_from_fen(
    piece: str, color: str, fen: str
) -> Tuple[float, float]:
    """
    Skąd zabrać figurę do promocji:
      - rząd „przed planszą” (Y=-1 dla white, Y=8 dla black)
      - pliki startowe z preferencją LEWEJ dla każdej figury
      - indeks = liczba ZBITYCH figur tego typu PO ruchu (z FEN)
    """
    caps = captured_counts_from_fen(fen)
    n_after = caps[color][piece.lower()]
    files_pref = starting_files_for_piece(piece, color)
    file_idx = files_pref[n_after] if n_after < len(files_pref) else files_pref[-1]
    y_rank = front_outside_rank_for(color)
    x_mm = file_idx * SQUARE_SIZE + BOARD_ORIGIN_X_MM
    y_mm = y_rank * SQUARE_SIZE + BOARD_ORIGIN_Y_MM
    return x_mm, y_mm


# --- główna funkcja: Twoja sekwencja promocji ---
def promotion_move(msg: dict) -> List[Step]:
    """
    Sekwencja wymagana przez Ciebie:
      A) pionek z 'from' -> parking pionków (kolor ruchu)
      B) promowana figura z parkingu -> NA STARE POLE PIONKA ('from')
    """
    frm = msg["from"]  # np. "e7"
    to = msg["to"]  # np. "e8" (tu NIE odkładamy)
    fen = msg["fen"]  # FEN po ruchu (z promowaną figurą na planszy)
    color = msg.get("color", "white")  # kolor gracza wykonującego promocję
    piece_placed = msg.get("piece_placed", "queen")  # np. "queen"

    # punkt docelowy dla figury: stare pole pionka (from)
    target_x, target_y = square_to_coords(frm)

    # A) pionek -> parking pionków
    from_x, from_y = square_to_coords(frm)
    pawn_park_x, pawn_park_y = pawn_parking_mm_for_color_from_fen(color, fen)
    step_a = Step(
        "remove pawn",
        f_x=from_x,
        f_y=from_y,
        t_x=pawn_park_x,
        t_y=pawn_park_y,
        note=f"Promotion: move pawn {frm} -> pawn parking ({color})",
    )

    # B) promowana figura z parkingu -> stare pole pionka
    to_x, to_y = square_to_coords(to)
    piece_park_x, piece_park_y = piece_parking_pick_mm_from_fen(
        piece_placed, color, fen
    )
    step_b = Step(
        "promote figure",
        f_x=piece_park_x,
        f_y=piece_park_y,
        t_x=to_x,
        t_y=to_y,
        note=f"Promotion: place {piece_placed} ({color}) on former pawn square {frm}",
    )

    return [step_a, step_b]
