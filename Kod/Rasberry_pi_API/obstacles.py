from typing import Dict, List, Set, Tuple

from config import CEMENTERY_FILES
from helpers import captured_counts_from_fen


def algebraic_to_idx(square):
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
            if ch in CEMENTERY_FILES:
                occ.add((file, rank))
            file += 1

    dedicated_files = ""
    occ_on_cementery = captured_counts_from_fen(fen)
    for piece, count in occ_on_cementery.items():
        if count < 0:
            dedicated_files = CEMENTERY_FILES[piece]
            for figure in range(count):
                if isinstance(dedicated_files, list):
                    occ.add(algebraic_to_idx(dedicated_files[figure]))
                else:
                    occ.add(algebraic_to_idx(dedicated_files))

    return occ


def obstacles(frm_sq, to_sq, fen):
    f_idx_from, r_idx_from = algebraic_to_idx(frm_sq)
    f_idx_to, r_idx_to = algebraic_to_idx(to_sq)
    # Zajęte pola wg aktualnego FEN
    occupied = get_occupied_from_fen(fen)

    if (f_idx_to, r_idx_to) in occupied:
        occupied.discard((f_idx_to, r_idx_to))

    xy_obstacles = [
        (f, r_idx_from)
        for f in range(min(f_idx_from, f_idx_to) + 1, max(f_idx_from, f_idx_to))
        if (f, r_idx_from) in occupied
    ] + [
        (f_idx_to, r)
        for r in range(min(r_idx_from, r_idx_to), max(r_idx_from, r_idx_to) + 1)
        if (f_idx_to, r) in occupied
    ]
    print(xy_obstacles)
    return xy_obstacles

