# rozmiar pola w mm
SQUARE_SIZE = 43.6
HOME = (60.8, 46.2)
LANE_OFFSET = SQUARE_SIZE / 2
BOARD_ORIGIN_X_MM = 60.8  # X (kolumny a..h)
BOARD_ORIGIN_Y_MM = 46.2  # Y (rząd 1..8)

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

START_COUNTS = {
    "pawn": 8,
    "rook": 2,
    "knight": 2,
    "bishop": 2,
    "queen": 1,
    "king": 1,
}
FEN_SYMBOLS = {
    "P": ("white", "pawn"),
    "R": ("white", "rook"),
    "N": ("white", "knight"),
    "B": ("white", "bishop"),
    "Q": ("white", "queen"),
    "K": ("white", "king"),
    "p": ("black", "pawn"),
    "r": ("black", "rook"),
    "n": ("black", "knight"),
    "b": ("black", "bishop"),
    "q": ("black", "queen"),
    "k": ("black", "king"),
}
FILES = "abcdefgh"