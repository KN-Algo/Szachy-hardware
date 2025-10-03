# capture.py
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
from standard_move import standard_move
from steps import Step

# --- stałe i pomocnicze ---
FILE_TO_IDX = {c: i for i, c in enumerate(FILES)}


def left_file_index_for(color: str) -> int:
    # lewa z perspektywy koloru
    return 0 if color == "white" else 7


def right_file_index_for(color: str) -> int:
    return 7 if color == "white" else 0


def front_outside_rank_for(color: str) -> int:
    # „przed planszą” (w stronę gracza): białe -1, czarne 8
    return -1 if color == "white" else 8


def left_outside_file_for(color: str) -> int:
    # „lewa krawędź” poza planszą: białe x=-1 (przy a), czarne x=8 (przy h)
    return -1 if color == "white" else 8


def away_dir_for(color: str) -> int:
    # w głąb od gracza: białe +1 (w górę), czarne -1 (w dół)
    return +1 if color == "white" else -1


def order_files_left_preferred(file_idx_list: List[int], color: str) -> List[int]:
    """
    Zwraca listę plików posortowaną tak, że „lewy” z perspektywy koloru jest pierwszy.
    Dla białych: rosnąco, dla czarnych: malejąco (bo ich lewy to wyższy indeks: h..a).
    """
    return sorted(file_idx_list, reverse=(color == "black"))


def starting_files_for_piece(piece: str, color: str) -> List[int]:
    """
    Pliki startowe danej figury, uporządkowane z preferencją LEWEJ strony.
    """
    p = piece.lower()
    if p == "rook":
        lst = [left_file_index_for(color), right_file_index_for(color)]
    elif p == "knight":
        lst = [1, 6]  # b, g
    elif p == "bishop":
        lst = [2, 5]  # c, f
    elif p == "queen":
        lst = [3]  # d
    elif p == "king":
        lst = [4]  # e
    else:
        lst = list(range(8))
    return order_files_left_preferred(lst, color)


# --- parser FEN (tylko część z figurami) -> liczniki na planszy ---
def counts_from_fen(fen: str) -> Dict[str, Dict[str, int]]:
    """
    Zwraca dict: counts[color][piece] = ile jest na planszy wg FEN.
    """
    board = fen.split()[0]
    counts = {
        "white": {k: 0 for k in START_COUNTS},
        "black": {k: 0 for k in START_COUNTS},
    }
    for ch in board:
        if ch == "/":
            continue
        if ch.isdigit():
            continue
        color_piece = FEN_SYMBOLS.get(ch)
        if color_piece:
            color, piece = color_piece
            counts[color][piece] += 1
    return counts


def captured_counts_from_fen(fen: str) -> Dict[str, Dict[str, int]]:
    """
    Zwraca dict: captured[color][piece] = ile zostało już zbitych (liczba startowa - bieżąca z FEN).
    FEN przychodzi po ruchu, więc uwzględnia bieżące bicie.
    """
    present = counts_from_fen(fen)
    captured = {"white": {}, "black": {}}
    for color in ("white", "black"):
        for piece, start_n in START_COUNTS.items():
            captured[color][piece] = max(0, start_n - present[color][piece])
    return captured


# --- wyliczanie docelowego slotu parkingowego na podstawie FEN ---
def parking_mm_for_pawn_from_fen(color_captured: str, fen: str) -> Tuple[float, float]:
    """
    Pionki: lewa krawędź planszy (x=-1 dla white, x=8 dla black), układane „w głąb” od gracza.
    Indeks slotu = liczba już zbitych pionków (z FEN) - 1 (bo indeksujemy od 0).
    """
    caps = captured_counts_from_fen(fen)
    k = caps[color_captured]["pawn"] - 1  # slot bieżącego bicia
    if k < 0:
        k = 0
    x_file = left_outside_file_for(color_captured)
    base_rank = 0 if color_captured == "white" else 7
    y_rank = base_rank + away_dir_for(color_captured) * k
    x_mm = x_file * SQUARE_SIZE + BOARD_ORIGIN_X_MM
    y_mm = y_rank * SQUARE_SIZE + BOARD_ORIGIN_Y_MM
    return x_mm, y_mm


def parking_mm_for_special_from_fen(
    piece: str, color_captured: str, fen: str
) -> Tuple[float, float]:
    """
    Figury nieszeregowe (rook/knight/bishop/queen/king): 1 pole „przed planszą” (Y=-1 dla white, Y=8 dla black),
    na plikach startowych **z preferencją LEWEJ** dla KAŻDEJ figury.
    Jeśli zbito już N figur tego typu, zajmujemy N-ty preferowany slot (0-indeks).
    """
    caps = captured_counts_from_fen(fen)
    n_captured = caps[color_captured][piece.lower()]
    idx = max(
        0, n_captured - 1
    )  # bieżący slot (0 dla pierwszej zbitej, 1 dla drugiej itd.)
    files_pref = starting_files_for_piece(piece, color_captured)
    # zabezpieczenie, gdyby idx wyszedł poza listę (teoretycznie nie powinien, poza pionami)
    file_idx = files_pref[idx] if idx < len(files_pref) else files_pref[-1]
    y_rank = front_outside_rank_for(color_captured)
    x_mm = file_idx * SQUARE_SIZE + BOARD_ORIGIN_X_MM
    y_mm = y_rank * SQUARE_SIZE + BOARD_ORIGIN_Y_MM
    return x_mm, y_mm


def compute_capture_parking_from_fen(
    piece_captured: str, color_captured: str, fen: str
) -> Tuple[float, float]:
    if piece_captured.lower() == "pawn":
        return parking_mm_for_pawn_from_fen(color_captured, fen)
    return parking_mm_for_special_from_fen(piece_captured, color_captured, fen)


# --- główna funkcja bicia oparta o FEN ---
def capture_move(msg: dict, obstacles: list) -> List[Step]:
    """
    Zwraca listę Step(f_x, f_y, t_x, t_y, note) w kolejności:
      1) TO  -> PARKING  (usunąć zbitą figurę)
      2) FROM -> TO      (przenieść bijącą figurę)
    Nie wymaga pamiętania stanu – korzysta z FEN po ruchu.
    """
    frm = msg["from"]
    to = msg["to"]
    fen = msg["fen"]
    piece_captured = msg.get("piece_captured", "piece")
    color_captured = msg.get("color_captured", "white")

    # 1) usuwamy zbitą figurę na wyliczony parking
    tx, ty = square_to_coords(to)
    park_x, park_y = compute_capture_parking_from_fen(
        piece_captured, color_captured, fen
    )

    steps = [
        Step(
            "taken figure offset",
            tx,
            ty,
            tx,
            ty + LANE_OFFSET,
            f"captured: make offset",
        ),
        Step(
            "H slide",
            tx,
            ty + LANE_OFFSET,
            park_x + LANE_OFFSET,
            ty + LANE_OFFSET,
            f"slide on H lane",
        ),
        Step(
            "V slide",
            park_x + LANE_OFFSET,
            ty + LANE_OFFSET,
            park_x + LANE_OFFSET,
            park_y + LANE_OFFSET,
            "slide on V lane",
        ),
        Step(
            "recenter on parking",
            park_x + LANE_OFFSET,
            park_y + LANE_OFFSET,
            park_x,
            park_y,
            f"recenter piece on parking",
        ),
    ]

    steps += standard_move(msg, obstacles)

    return steps
