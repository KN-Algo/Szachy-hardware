# castling.py
from typing import Dict, List

from config import LANE_OFFSET
from square_to_cords import square_to_coords
from standard_move import standard_move
from steps import Step


def castling_move(msg: Dict) -> List[Step]:

    moves = msg["moves"]

    if moves[0]["order"] != 1:
        moves.reverse()

    fen = msg["fen"]
    king_move, rook_move = moves
    from_rook = rook_move["from"]
    to_rook = rook_move["to"]

    fx, tx = square_to_coords(king_move["from"])
    fy, ty = square_to_coords(king_move["to"])

    steps = []

    steps.append(Step("move", fx, fy, tx, ty, "a"))
    steps.extend(standard_move(from_rook, to_rook, fen))

    return steps
