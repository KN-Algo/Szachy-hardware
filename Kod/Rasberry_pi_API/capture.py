# capture.py
from dataclasses import dataclass
from typing import Dict, List, Tuple

from config import CEMENTERY_FILES, FEN_SYMBOLS, START_COUNTS
from square_to_cords import square_to_coords
from standard_move import standard_move
from steps import Step


def first_to_cementery(piece, fen):
    dedicated_files = CEMENTERY_FILES[piece]
    cementery_file = ""
    if isinstance(dedicated_files, list):
        cementery_file = dedicated_files[0 + captured_counts_from_fen(fen)[piece] - 1]
    else:
        cementery_file = dedicated_files
    print(cementery_file)
    return cementery_file


# --- parser FEN (tylko część z figurami) -> liczniki na planszy ---
def counts_from_fen(fen: str) -> Dict[str, int]:
    count_board = fen.split()[0]
    counts = {k: 0 for k in CEMENTERY_FILES.keys()}

    for char in count_board:
        if char.isalpha():  # pomijamy cyfry i ukośniki
            counts[char] += 1
    return counts


def captured_counts_from_fen(fen: str) -> Dict[str, int]:
    present = counts_from_fen(fen)
    captured = {k: 0 for k in CEMENTERY_FILES.keys()}

    for piece in captured.keys():
        captured[piece] = START_COUNTS[piece.lower()] - present[piece]

    return captured


# --- główna funkcja bicia oparta o FEN ---
def capture_move(msg: dict) -> List[Step]:
    frm = msg["from"]
    to = msg["to"]
    fen = msg["fen"]
    piece_captured = msg.get("piece_captured", "piece")
    color_captured = msg.get("color_captured", "white")

    captured_symbol = FEN_SYMBOLS[piece_captured]
    print(color_captured)
    if color_captured == "white":
        captured_symbol.upper()

    to_cementary = first_to_cementery(captured_symbol, fen)

    steps = []

    steps.extend(standard_move(to, to_cementary, fen))
    steps.extend(standard_move(frm, to, fen))

    return steps
