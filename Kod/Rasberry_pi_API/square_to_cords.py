from config import SQUARE_SIZE


def square_to_coords(square):
    file = square[0].lower()  # a-h
    rank = square[1]  # 1-8
    x = (ord(file) - ord("a")) * SQUARE_SIZE
    y = (int(rank) - 1) * SQUARE_SIZE
    return x, y
