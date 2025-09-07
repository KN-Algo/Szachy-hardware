# castling.py
from typing import Dict, List, Tuple

from config import SQUARE_SIZE
from square_to_cords import square_to_coords
from steps import Step

FILES = "abcdefgh"
FILE_TO_IDX = {c: i for i, c in enumerate(FILES)}


def rank_idx(square: str) -> int:
    return int(square[1]) - 1  # 0..7


def _castling_waypoints(from_sq: str, to_sq: str) -> List[Step]:
    """
    Dla pojedynczej figury w roszadzie zwraca 3 odcinki z odskokiem o 0.5 pola w osi Y.
    """
    fx, fy = square_to_coords(from_sq)
    tx, ty = square_to_coords(to_sq)

    r = rank_idx(from_sq)
    # białe roszadują na rank 0 (1. rząd), czarne na rank 7 (8. rząd)
    if r == 0:
        delta_y = -0.5 * SQUARE_SIZE  # "w dół" od perspektywy białych
    elif r == 7:
        delta_y = +0.5 * SQUARE_SIZE  # "w górę" od perspektywy czarnych
    else:
        # awaryjnie: wybierz kierunek dalej od środka, by nie wjechać w figury
        delta_y = -0.5 * SQUARE_SIZE if r < 4 else +0.5 * SQUARE_SIZE

    w1_x, w1_y = fx, fy + delta_y
    w2_x, w2_y = tx, ty + delta_y

    return [
        Step(
            "castle side move",
            f_x=fx,
            f_y=fy,
            t_x=w1_x,
            t_y=w1_y,
            note=f"Castling: offset from {from_sq}",
        ),
        Step(
            "castle slide",
            f_x=w1_x,
            f_y=w1_y,
            t_x=w2_x,
            t_y=w2_y,
            note=f"Castling: slide to {to_sq} (offset lane)",
        ),
        Step(
            "castle recenter",
            f_x=w2_x,
            f_y=w2_y,
            t_x=tx,
            t_y=ty,
            note=f"Castling: recenter on {to_sq}",
        ),
    ]


def castling_move(msg: Dict) -> List[Step]:
    """
    Przyjmuje JSON z roszadą (jak w Twoich przykładach).
    Zwraca listę Step(...) dla króla i wieży, w kolejności wg 'order' w msg['moves'].
    """
    moves = msg.get("moves", [])
    if not moves:
        # fallback: jeśli nie ma moves, spróbuj domyślić roszadę z from/to (król), a wieżę wywnioskuj
        from_sq = msg["from"]
        to_sq = msg["to"]
        # wyznacz wieżę po stronie roszady
        if to_sq[0] < from_sq[0]:  # długa (queenside)
            rook_from = "a" + from_sq[1]
            rook_to = "d" + from_sq[1]
        else:  # krótka (kingside)
            rook_from = "h" + from_sq[1]
            rook_to = "f" + from_sq[1]
        ordered = [
            {"from": from_sq, "to": to_sq, "piece": "king", "order": 1},
            {"from": rook_from, "to": rook_to, "piece": "rook", "order": 2},
        ]
    else:
        # posortuj wg 'order' jeśli jest, w przeciwnym razie kolejność jak w liście
        ordered = sorted(moves, key=lambda m: m.get("order", 9999))

    steps: List[Step] = []
    for m in ordered:
        steps.extend(_castling_waypoints(m["from"], m["to"]))
    return steps
