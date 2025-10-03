from config import SQUARE_SIZE, BOARD_ORIGIN_X_MM, BOARD_ORIGIN_Y_MM


def square_to_coords(square):
    file = square[0].lower()  # a-h
    rank = square[1]  # 1-8
    x = (ord(file) - ord("a")) * SQUARE_SIZE + BOARD_ORIGIN_X_MM
    y = (int(rank) - 1) * SQUARE_SIZE + BOARD_ORIGIN_Y_MM
    return x, y
