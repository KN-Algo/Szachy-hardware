from dataclasses import dataclass, field


@dataclass
class Step:
    action: str
    f_x: float
    f_y: float
    t_x: float
    t_y: float
    note: str = field(default=None)  # ustawiamy placeholder

    def __post_init__(self):
        if self.note is None:  # jeśli nie podano, ustawiamy jak action
            self.note = self.action
