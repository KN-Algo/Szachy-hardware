# promotion_capture.py
from typing import Dict, List, Tuple

from config import SQUARE_SIZE
from square_to_cords import square_to_coords
from steps import Step

# --- wspólne mapowania/utility (te same co w promotion.py) ---
START_COUNTS = {"pawn": 8, "rook": 2, "knight": 2, "bishop": 2, "queen": 1, "king": 1}
FEN_SYMBOLS = {
    "P": ("white", "pawn"),
    "R": ("white", "rook"),
    "N": ("white", "knight"),
    "B": ("white", "bishop"),
    "Q": ("white", "queen"),
    "K": ("white", "king"),
    "p": ("black", "pawn"),
    "r": ("black", "rook"),
    "n": ("black", "knight"),
    "b": ("black", "bishop"),
    "q": ("black", "queen"),
    "k": ("black", "king"),
}


def opponent(color: str) -> str:
    return "black" if color == "white" else "white"


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
    return +1 if color == "white" else -1


def order_files_left_preferred(files, color):
    # preferencja lewej strony: białe rosnąco (a..h), czarne malejąco (h..a)
    return sorted(files, reverse=(color == "black"))


def starting_files_for_piece(piece: str, color: str):
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


# --- parkingi w mm wyliczane z FEN (po ruchu) ---
def captured_piece_parking_mm_from_fen(
    piece: str, color_captured: str, fen: str
) -> Tuple[float, float]:
    """
    Gdzie odłożyć ZBITĄ figurę przeciwnika:
      - rząd „przed planszą” (Y=-1 dla white, Y=8 dla black),
      - pliki startowe z preferencją lewej,
      - slot = liczba JUŻ zbitych figur tego typu (po ruchu) - 1.
    """
    caps = captured_counts_from_fen(fen)
    idx = max(0, caps[color_captured][piece.lower()] - 1)
    files_pref = starting_files_for_piece(piece, color_captured)
    file_idx = files_pref[idx] if idx < len(files_pref) else files_pref[-1]
    y_rank = front_outside_rank_for(color_captured)
    x_mm = (file_idx) * SQUARE_SIZE
    y_mm = (y_rank) * SQUARE_SIZE
    return x_mm, y_mm


def pawn_parking_mm_for_color_from_fen(color: str, fen: str) -> Tuple[float, float]:
    """
    Gdzie odwieźć pionka gracza:
      - lewa krawędź (x=-1 dla white, x=8 dla black),
      - w głąb od gracza,
      - slot = liczba już „odłożonych” pionków po ruchu - 1.
    """
    caps = captured_counts_from_fen(fen)
    k = max(0, caps[color]["pawn"] - 1)
    x_file = left_outside_file_for(color)
    base_rank = 0 if color == "white" else 7
    y_rank = base_rank + away_dir_for(color) * k
    x_mm = (x_file) * SQUARE_SIZE
    y_mm = (y_rank) * SQUARE_SIZE
    return x_mm, y_mm


def piece_parking_pick_mm_from_fen(
    piece: str, color: str, fen: str
) -> Tuple[float, float]:
    """
    Skąd zabrać promowaną figurę gracza:
      - rząd „przed planszą”,
      - pliki startowe (preferencja lewej),
      - indeks = liczba ZBITYCH figur tego typu po ruchu (z FEN).
    """
    caps = captured_counts_from_fen(fen)
    n_after = caps[color][piece.lower()]
    files_pref = starting_files_for_piece(piece, color)
    file_idx = files_pref[n_after] if n_after < len(files_pref) else files_pref[-1]
    y_rank = front_outside_rank_for(color)
    x_mm = (file_idx) * SQUARE_SIZE
    y_mm = (y_rank) * SQUARE_SIZE
    return x_mm, y_mm


# --- główna funkcja: PROMOTION + CAPTURE ---
def promotion_capture_move(msg: dict) -> List[Step]:
    """
    Kolejność:
      A) Usuń zbitą figurę z 'to' -> odstaw na parking przeciwnika
      B) Odwieź pionka z 'from'   -> parking pionków gracza
      C) Weź promowaną figurę z parkingu gracza -> połóż na 'to'
    """
    frm = msg["from"]  # np. "e7"
    to = msg["to"]  # np. "f8"
    fen = msg["fen"]  # FEN po ruchu (z nową figurą na 'to')
    color = msg.get("color", "white")  # kolor wykonujący promocję
    piece_placed = msg.get("piece_placed", "queen")
    piece_captured = msg.get("piece_captured", "piece")
    color_captured = opponent(color)

    # współrzędne kluczowych punktów
    to_x, to_y = square_to_coords(to)
    from_x, from_y = square_to_coords(frm)

    # A) zbijana figura -> parking przeciwnika
    cap_park_x, cap_park_y = captured_piece_parking_mm_from_fen(
        piece_captured, color_captured, fen
    )
    step_a = Step(
        "remove figure",
        f_x=to_x,
        f_y=to_y,
        t_x=cap_park_x,
        t_y=cap_park_y,
        note=f"Promotion-capture: remove captured {piece_captured} ({color_captured}) from {to} -> parking",
    )

    # B) pionek -> parking pionków gracza
    pawn_park_x, pawn_park_y = pawn_parking_mm_for_color_from_fen(color, fen)
    step_b = Step(
        "remove pawn",
        f_x=from_x,
        f_y=from_y,
        t_x=pawn_park_x,
        t_y=pawn_park_y,
        note=f"Promotion-capture: move pawn {frm} -> pawn parking ({color})",
    )

    # C) promowana figura z parkingu gracza -> pole 'to'
    promo_pick_x, promo_pick_y = piece_parking_pick_mm_from_fen(
        piece_placed, color, fen
    )
    step_c = Step(
        "promote figure",
        f_x=promo_pick_x,
        f_y=promo_pick_y,
        t_x=to_x,
        t_y=to_y,
        note=f"Promotion-capture: place {piece_placed} ({color}) on {to}",
    )

    return [step_a, step_b, step_c]
