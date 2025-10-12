# promotion
from dataclasses import dataclass
from typing import Dict, List, Tuple

from config import FEN_SYMBOLS
from helpers import first_to_cementery, promoted_from_cementery
from square_to_cords import square_to_coords
from standard_move import standard_move
from steps import Step


# --- główna funkcja bicia oparta o FEN ---
def promotion_move(msg: dict) -> List[Step]:

    frm = msg["from"]
    to = msg["to"]
    fen = msg["fen"]
    piece_placed = msg.get("piece_placed", "piece")
    color = msg.get("color", "white")

    placed_symbol = FEN_SYMBOLS[piece_placed]
    removed_pawn = "p"

    if color == "white":
        placed_symbol = placed_symbol.upper()
        removed_pawn = removed_pawn.upper()

    to_cementary = first_to_cementery(removed_pawn, fen)
    from_cementary = promoted_from_cementery(placed_symbol, fen)

    steps = []

    steps.extend(standard_move(frm, to_cementary, fen))
    steps.extend(standard_move(from_cementary, to, fen))

    return steps
