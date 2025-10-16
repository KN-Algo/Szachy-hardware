from copy import deepcopy

from config import CEMENTERY_FILES, START_COUNTS, START_FEN
from helpers import captured_counts_from_fen
from standard_move import standard_move
from steps import Step


def reset_pieces_to_start(fen: str) -> str:

    steps = []

    def fen_to_board(fen_str):
        rows = fen_str.split()[0].split("/")
        board = []
        for row in rows:
            expanded = []
            for ch in row:
                if ch.isdigit():
                    expanded.extend(["."] * int(ch))
                else:
                    expanded.append(ch)
            board.append(expanded)
        return board

    def board_to_fen(board):
        fen_rows = []
        for row in board:
            fen_row = ""
            empty = 0
            for ch in row:
                if ch == ".":
                    empty += 1
                else:
                    if empty:
                        fen_row += str(empty)
                        empty = 0
                    fen_row += ch
            if empty:
                fen_row += str(empty)
            fen_rows.append(fen_row)
        return "/".join(fen_rows) + " w KQkq - 0 1"

    # 🧩 Pozycje startowe
    start_positions = {
        "P": ["a2", "b2", "c2", "d2", "e2", "f2", "g2", "h2"],
        "R": ["a1", "h1"],
        "N": ["b1", "g1"],
        "B": ["c1", "f1"],
        "Q": ["d1"],
        "K": ["e1"],
        "p": ["a7", "b7", "c7", "d7", "e7", "f7", "g7", "h7"],
        "r": ["a8", "h8"],
        "n": ["b8", "g8"],
        "b": ["c8", "f8"],
        "q": ["d8"],
        "k": ["e8"],
    }

    def square_to_coords(square):
        if not isinstance(square, str) or len(square) != 2:
            raise ValueError(f"Invalid square name: {square!r}")
        file = ord(square[0]) - ord("a")
        rank = 8 - int(square[1])
        if not (0 <= file <= 7 and 0 <= rank <= 7):
            raise ValueError(f"Invalid square coordinates: {square!r}")
        return rank, file

    board = fen_to_board(fen)
    new_board = deepcopy(board)
    occupied_white = set()
    occupied_black = set()

    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == ".":
                continue
            sq = f"{chr(ord('a') + c)}{8 - r}"
            if piece.isupper():
                occupied_white.add(sq)
            else:
                occupied_black.add(sq)

    def place_on_first_free(piece, color):
        # Pobierz pola startowe (lista lub string)
        raw_pos = start_positions.get(piece)
        if not raw_pos:
            print(f"⚠️ Brak startowej pozycji dla {piece}")
            return None
        start_list = raw_pos

        # Walidacja pól
        valid_squares = [
            sq
            for sq in start_list
            if isinstance(sq, str)
            and len(sq) == 2
            and sq[0].isalpha()
            and sq[1].isdigit()
        ]
        if not valid_squares:
            print(f"⚠️ Nieprawidłowe pola startowe dla {piece}: {start_list}")
            return None

        check_range = reversed(valid_squares) if color == "white" else valid_squares
        occupied = occupied_white if color == "white" else occupied_black
        print(occupied)
        for sq in check_range:
            if sq not in occupied:
                r, c = square_to_coords(sq)
                new_board[r][c] = piece
                occupied.add(sq)
                return sq
        print(f"⚠️ Brak wolnego pola startowego dla {piece}")
        return None

    print("=== START ===")
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == ".":
                continue
            sq = f"{chr(ord('a') + c)}{8 - r}"
            color = "white" if piece.isupper() else "black"

            # sprawdź czy jest na pozycji startowej
            start_list = start_positions.get(piece)
            is_home = False
            if isinstance(start_list, list) and sq in start_list:
                is_home = True

            if is_home:
                continue  # zostaje

            print(f"{piece} z {sq} → reset")
            new_board[r][c] = "."
            dest = place_on_first_free(piece, color)
            if dest:
                print(f"→ ustawiono na {dest}")
            steps.extend(standard_move(sq, dest, board_to_fen(new_board)))
            if color == "white":
                occupied_white.remove(sq)
            elif color == "black":
                occupied_black.remove(sq)
            print("Aktualny FEN:", board_to_fen(new_board))
            print("-----------------------")

    final_fen = board_to_fen(new_board)

    missing_pieces = captured_counts_from_fen(final_fen)

    # --- Wypisz ruchy ---
    print("=== Brakujące figury ===")

    print(board_to_fen(new_board))

    for piece, diff in missing_pieces.items():
        if diff <= 0:
            continue
        cementery_slots = CEMENTERY_FILES.get(piece, [])
        color = "white" if piece.isupper() else "black"
        for i in range(diff):
            sq = cementery_slots[diff - i - 1]
            print(f"{piece} z {sq} → reset")
            dest = place_on_first_free(piece, color)
            if dest:
                print(f"→ ustawiono na {dest}")
            steps.extend(standard_move(sq, dest, board_to_fen(new_board)))
            print("Aktualny FEN:", board_to_fen(new_board))
            print("-----------------------")
    final_fen = START_FEN
    print("=== KONIEC ===")
    print("Końcowy FEN:", final_fen)

    return steps
