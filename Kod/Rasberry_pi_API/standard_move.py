import json

from square_to_cords import square_to_coords
from steps import Step


def standard_move(data):
    frm = data["from"]
    to = data["to"]

    fx, fy = square_to_coords(frm)
    tx, ty = square_to_coords(to)

    steps = [Step("move", fx, fy, tx, ty, f"mave a pice from {frm} to {to}")]

    return steps
