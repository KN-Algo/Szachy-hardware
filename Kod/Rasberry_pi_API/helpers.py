from typing import Dict, List, Tuple

from config import CEMENTERY_FILES, START_COUNTS


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


def first_to_cementery(piece, fen):
    dedicated_files = CEMENTERY_FILES[piece]
    cementery_file = ""
    if isinstance(dedicated_files, list):
        cementery_file = dedicated_files[0 + captured_counts_from_fen(fen)[piece] - 1]
    else:
        cementery_file = dedicated_files
    return cementery_file


def promoted_from_cementery(piece, fen):
    dedicated_files = CEMENTERY_FILES[piece]
    cementery_file = ""
    if isinstance(dedicated_files, list):
        cementery_file = dedicated_files[0 + captured_counts_from_fen(fen)[piece]]
    else:
        cementery_file = dedicated_files
    return cementery_file
