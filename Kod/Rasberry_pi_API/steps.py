from dataclasses import dataclass


@dataclass
class Step:
    action: str
    f_x: float
    f_y: float
    t_x: float
    t_y: float
    note: str = ""
