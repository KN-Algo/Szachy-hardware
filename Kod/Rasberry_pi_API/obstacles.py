from config import FEN_SYMBOLS
from typing import Dict, List, Set, Tuple

def algebraic_to_idx(square: str) -> Tuple[int, int]:
    f = ord(square[0].lower()) - ord("a")  # 0..7
    r = int(square[1]) - 1  # 0..7
    return f, r

def get_occupied_from_fen(fen: str) -> Set[Tuple[int, int]]:
    board = fen.split()[0]
    occ: Set[Tuple[int, int]] = set()
    rank = 7
    file = 0
    for ch in board:
        if ch == "/":
            rank -= 1
            file = 0
        elif ch.isdigit():
            file += int(ch)
        else:
            if ch in FEN_SYMBOLS:
                occ.add((file, rank))
            file += 1
    return occ


def obstacles(data: dict):
    frm_sq = data["from"]
    to_sq = data["to"]
    f_idx_from, r_idx_from = algebraic_to_idx(frm_sq)
    f_idx_to, r_idx_to = algebraic_to_idx(to_sq)
    # Zajęte pola wg aktualnego FEN
    occupied = get_occupied_from_fen(data['fen'])

    if (f_idx_to, r_idx_to) in occupied:
        occupied.discard((f_idx_to, r_idx_to))

    x_obstacles = [
        (f, r_idx_from)
        for f in range(min(f_idx_from, f_idx_to) + 1, max(f_idx_from, f_idx_to))
        if (f, r_idx_from) in occupied
    ] + [
        (f_idx_to, r)
        for r in range(min(r_idx_from, r_idx_to), max(r_idx_from, r_idx_to) + 1)
        if (f_idx_to, r) in occupied
    ]

    # Przeszkody w osi Y (V)
    y_obstacles = [
        (f_idx_to, r)
        for r in range(min(r_idx_from, r_idx_to) + 1, max(r_idx_from, r_idx_to))
        if (f_idx_to, r) in occupied
    ] + [
        (f, r_idx_from)
        for f in range(min(f_idx_from, f_idx_to), max(f_idx_from, f_idx_to) + 1)
        if (f, r_idx_from) in occupied
    ]

    return x_obstacles + y_obstacles