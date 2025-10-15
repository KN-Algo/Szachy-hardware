from config import BOARD_ORIGIN_X_MM, BOARD_ORIGIN_Y_MM, SQUARE_SIZE


def square_to_coords(square):
    file = square[0].lower()  # a-h
    rank = square[1]  # 1-8
    x = round((ord(file) - ord("a")) * SQUARE_SIZE + BOARD_ORIGIN_X_MM, 2)
    y = round((int(rank) - 1) * SQUARE_SIZE + BOARD_ORIGIN_Y_MM, 2)
    return x, y
