# promotion
from dataclasses import dataclass
from typing import Dict, List, Tuple

from config import FEN_SYMBOLS
from helpers import first_to_cementery, promoted_from_cementery
from square_to_cords import square_to_coords
from standard_move import standard_move
from steps import Step


# --- główna funkcja bicia oparta o FEN ---
def promotion_capture_move(msg: dict) -> List[Step]:

    frm = msg["from"]
    to = msg["to"]
    fen = msg["fen"]
    piece_placed = msg.get("piece_placed", "piece")
    piece_captured = msg.get("piece_captured", "piece")
    color = msg.get("color", "white")

    placed_symbol = FEN_SYMBOLS[piece_placed]
    captured_symbol = FEN_SYMBOLS[piece_captured]
    removed_pawn = "p"

    if color == "white":
        placed_symbol = placed_symbol.upper()
        removed_pawn = removed_pawn.upper()
    else:
        captured_symbol = captured_symbol.upper()

    pawn_to_cementary = first_to_cementery(removed_pawn, fen)
    figure_to_cementary = first_to_cementery(captured_symbol, fen)
    from_cementary = promoted_from_cementery(placed_symbol, fen)

    steps = []

    steps.extend(standard_move(to, figure_to_cementary, fen))
    steps.extend(standard_move(frm, pawn_to_cementary, fen))
    steps.extend(standard_move(from_cementary, to, fen))

    return steps
