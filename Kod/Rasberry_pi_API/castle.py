# castling.py
from typing import Dict, List

from config import LANE_OFFSET
from square_to_cords import square_to_coords
from standard_move import standard_move
from steps import Step


def castling_move(msg: Dict) -> List[Step]:
    """
    Przyjmuje JSON z roszadą
    Zwraca listę Step(...) dla króla i wieży
    """

    moves = msg["moves"]

    if moves[0]["order"] != 1:
        moves.reverse()

    king_move, rook_move = moves

    dir = -1 if msg["from"][1] == "1" else 1

    rf_x, rf_y = square_to_coords(rook_move["from"])
    rt_x, rt_y = square_to_coords(rook_move["to"])

    steps = list()

    steps.append(Step("rook offset", rf_x, rf_y, rf_x, rf_y + LANE_OFFSET * dir))

    steps.extend(standard_move(king_move, None))

    steps.extend(
        [
            Step(
                "rook slide V",
                rf_x,
                rf_y + LANE_OFFSET * dir,
                rt_x,
                rf_y + LANE_OFFSET * dir,
            ),
            Step(
                "rook recenter",
                rt_x,
                rf_y + LANE_OFFSET * dir,
                rt_x,
                rt_y,
            ),
        ]
    )

    return steps
