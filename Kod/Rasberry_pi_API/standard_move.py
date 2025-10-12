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
    y_dir = -1 if fy < ty else 1

    if obst:
        steps = [
            Step("offset", fx, fy, fx, fy + LANE_OFFSET * y_dir, f"make offset"),
            Step(
                "H slide",
                fx,
                fy + LANE_OFFSET * y_dir,
                tx + LANE_OFFSET * x_dir,
                fy + LANE_OFFSET * y_dir,
                f"slide on H lane",
            ),
            Step(
                "V slide",
                tx + LANE_OFFSET * x_dir,
                fy + LANE_OFFSET * y_dir,
                tx + LANE_OFFSET,
                ty,
                "slide on V lane",
            ),
            Step("recenter", tx + LANE_OFFSET * x_dir, ty, tx, ty, f"recenter piece"),
        ]
        return steps
    steps = [Step("move", fx, fy, tx, ty, f"mave a pice from {frm} to {to}")]

    return steps
