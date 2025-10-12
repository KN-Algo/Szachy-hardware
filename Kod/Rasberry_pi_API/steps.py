from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Step:
    action: str
    f_x: float
    f_y: float
    t_x: float
    t_y: float
    note: str
