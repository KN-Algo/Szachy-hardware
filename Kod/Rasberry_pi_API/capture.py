# capture.py
from dataclasses import dataclass
from typing import Dict, List, Tuple

from config import CEMENTERY_FILES, FEN_SYMBOLS, START_COUNTS
from helpers import first_to_cementery
from square_to_cords import square_to_coords
from standard_move import standard_move
from steps import Step


# --- główna funkcja bicia oparta o FEN ---
def capture_move(msg: dict) -> List[Step]:
    frm = msg["from"]
    to = msg["to"]
    fen = msg["fen"]
    piece_captured = msg.get("piece_captured", "piece")
    color_captured = msg.get("color_captured", "white")

    captured_symbol = FEN_SYMBOLS[piece_captured]

    if color_captured == "white":
        captured_symbol = captured_symbol.upper()

    to_cementary = first_to_cementery(captured_symbol, fen)

    steps = []

    steps.extend(standard_move(to, to_cementary, fen))
    steps.extend(standard_move(frm, to, fen))

    return steps
