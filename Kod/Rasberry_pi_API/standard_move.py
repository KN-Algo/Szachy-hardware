import json

from square_to_cords import square_to_coords
from steps import Step
from config import LANE_OFFSET

def standard_move(data, obstacles): 

    frm = data["from"]
    to = data["to"]

    fx, fy = square_to_coords(frm)
    tx, ty = square_to_coords(to)

    print(obstacles)
    if obstacles:
        steps = [
            Step("offset", fx, fy, fx, fy + LANE_OFFSET, f"make offset"),
            Step("H slide", fx, fy +LANE_OFFSET, tx + LANE_OFFSET, fy + LANE_OFFSET, f"slide on H lane"),
            Step("V slide", tx + LANE_OFFSET, fy + LANE_OFFSET, tx + LANE_OFFSET, ty, "slide on V lane"),
            Step("recenter", tx + LANE_OFFSET, ty, tx, ty, f"recenter piece")
        ]
        return steps
    steps = [Step("move", fx, fy, tx, ty, f"mave a pice from {frm} to {to}")]

    return steps
