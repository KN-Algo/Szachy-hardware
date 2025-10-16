# rozmiar pola w mm
SQUARE_SIZE = 43.6
HOME = (60.8, 46.2)
LANE_OFFSET = SQUARE_SIZE / 2
BOARD_ORIGIN_X_MM = 60.8  # X (kolumny a..h)
BOARD_ORIGIN_Y_MM = 46.2  # Y (rząd 1..8)

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

START_COUNTS = {
    "p": 8,
    "r": 2,
    "n": 2,
    "b": 2,
    "q": 1,
    "k": 1,
}
FEN_SYMBOLS = {
    "pawn": "p",
    "rook": "r",
    "bishop": "b",
    "knight": "n",
    "queen": "q",
    "king": "k",
}

CEMENTERY_FILES = {
    "P": ["`1", "`2", "`3", "`4", "`5", "`6", "`7", "`8"],
    "R": ["a0", "h0"],
    "N": ["b0", "g0"],
    "B": ["c0", "f0"],
    "Q": ["d0"],
    "K": ["e0"],
    "p": ["i8", "i7", "i6", "i5", "i4", "i3", "i2", "i1"],
    "r": ["h9", "a9"],
    "n": ["g9", "b9"],
    "b": ["f9", "c9"],
    "q": ["d9"],
    "k": ["e9"],
}


FILES = "abcdefgh"
