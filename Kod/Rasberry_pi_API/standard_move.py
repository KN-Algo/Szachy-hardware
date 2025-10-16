import json

from config import LANE_OFFSET
from obstacles import obstacles
from square_to_cords import square_to_coords
from steps import Step


def standard_move(frm, to, fen):

    fx, fy = square_to_coords(frm)
    tx, ty = square_to_coords(to)

    obst = obstacles(frm, to, fen)

    x_dir = -1 if fx < tx else 1
    y_dir = 1 if fy < ty else -1

    if obst:
        steps = [
            Step(
                "offset", fx, fy, fx, fy + round(LANE_OFFSET * y_dir, 2), f"make offset"
            ),
            Step(
                "H slide",
                fx,
                fy + round(LANE_OFFSET * y_dir, 2),
                tx + round(LANE_OFFSET * x_dir, 2),
                fy + round(LANE_OFFSET * y_dir, 2),
                f"slide on H lane",
            ),
            Step(
                "V slide",
                tx + round(LANE_OFFSET * x_dir, 2),
                fy + round(LANE_OFFSET * y_dir, 2),
                tx + round(LANE_OFFSET * x_dir, 2),
                ty,
                "slide on V lane",
            ),
            Step(
                "recenter",
                tx + round(LANE_OFFSET * x_dir, 2),
                ty,
                tx,
                ty,
                f"recenter piece",
            ),
        ]
        return steps
    steps = [Step("move", fx, fy, tx, ty, f"mave a pice from {frm} to {to}")]

    return steps
