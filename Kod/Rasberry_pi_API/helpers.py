from typing import Dict, List, Tuple

import chess

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


def detect_move_type(fen_before: str, fen_after: str) -> str:
    board_before = chess.Board(fen_before)
    board_after = chess.Board(fen_after)

    # znajdź ruch, który prowadzi z fen_before do fen_after
    move_found = None
    for move in board_before.legal_moves:
        temp_board = board_before.copy()
        temp_board.push(move)
        if temp_board.fen().split(" ", 1)[0] == board_after.fen().split(" ", 1)[0]:
            move_found = move
            break

    if not move_found:
        return "unknown"

    # Analiza typu ruchu
    is_capture = board_before.is_capture(move_found)
    is_castle = board_before.is_castling(move_found)
    is_promo = move_found.promotion is not None

    if is_castle:
        return "castle"
    elif is_promo and is_capture:
        return "promotion capture"
    elif is_promo:
        return "promotion"
    elif is_capture:
        return "capture"
    else:
        return "standard"


def generate_move_json(fen_before: str, fen_after: str):
    board_before = chess.Board(fen_before)

    # najpierw wykrywamy typ ruchu
    move_type = detect_move_type(fen_before, fen_after)

    # szukamy faktycznego ruchu
    move_found = None
    for move in board_before.legal_moves:
        temp_board = board_before.copy()
        temp_board.push(move)
        if (
            temp_board.fen().split(" ", 1)[0]
            == chess.Board(fen_after).fen().split(" ", 1)[0]
        ):
            move_found = move
            break

    if not move_found:
        return {"error": "could not detect move"}

    # generujemy JSON w zależności od typu
    if move_type == "standard":
        return {
            "from": chess.square_name(move_found.from_square),
            "to": chess.square_name(move_found.to_square),
            "fen": fen_after,
        }

    elif move_type == "capture":
        captured_piece = board_before.piece_at(move_found.to_square)
        captured_name = (
            chess.PIECE_NAMES[captured_piece.piece_type] if captured_piece else None
        )
        captured_color = (
            "white"
            if captured_piece and captured_piece.color == chess.WHITE
            else "black"
        )

        mover_color = "white" if board_before.turn == chess.WHITE else "black"

        return {
            "from": chess.square_name(move_found.from_square),
            "to": chess.square_name(move_found.to_square),
            "fen": fen_after,
            "type": "capture",
            "piece_captured": captured_name,
            "capture": True,
            "color_moved": mover_color,
            "color_captured": captured_color,
        }

    elif move_type == "promotion":
        mover_color = "white" if board_before.turn == chess.WHITE else "black"
        promoted_piece = move_found.promotion  # np. chess.QUEEN
        promoted_name = chess.PIECE_NAMES[promoted_piece] if promoted_piece else None

        return {
            "from": chess.square_name(move_found.from_square),
            "to": chess.square_name(move_found.to_square),
            "fen": fen_after,
            "type": "promotion",
            "piece_removed": "pawn",
            "piece_placed": promoted_name,
            "color": mover_color,
        }

    elif move_type == "promotion capture":
        mover_color = "white" if board_before.turn == chess.WHITE else "black"
        captured_piece = board_before.piece_at(move_found.to_square)
        captured_name = (
            chess.PIECE_NAMES[captured_piece.piece_type] if captured_piece else None
        )
        captured_color = (
            "white"
            if captured_piece and captured_piece.color == chess.WHITE
            else "black"
        )

        promoted_piece = move_found.promotion
        promoted_name = chess.PIECE_NAMES[promoted_piece] if promoted_piece else None

        return {
            "from": chess.square_name(move_found.from_square),
            "to": chess.square_name(move_found.to_square),
            "fen": fen_after,
            "type": "promotion_capture",
            "piece_removed": "pawn",
            "piece_placed": promoted_name,
            "piece_captured": captured_name,
            "capture": True,
            "color": mover_color,
        }

    elif move_type == "castle":
        mover_color = "white" if board_before.turn == chess.WHITE else "black"
        king_from = chess.square_name(move_found.from_square)
        king_to = chess.square_name(move_found.to_square)

        # Określamy czy to roszada krótka czy długa
        if move_found.to_square > move_found.from_square:
            # krótka roszada (king-side)
            rook_from = "h1" if mover_color == "white" else "h8"
            rook_to = "f1" if mover_color == "white" else "f8"
        else:
            # długa roszada (queen-side)
            rook_from = "a1" if mover_color == "white" else "a8"
            rook_to = "d1" if mover_color == "white" else "d8"

        return {
            "from": king_from,
            "to": king_to,
            "fen": fen_after,
            "type": "castling",
            "moves": [
                {"from": king_from, "to": king_to, "piece": "king", "order": 1},
                {"from": rook_from, "to": rook_to, "piece": "rook", "order": 2},
            ],
        }
