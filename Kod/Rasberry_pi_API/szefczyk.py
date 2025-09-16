# Samowystarczalny pokaz „mat szewczyka” + RESET do pozycji startowej

import time
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

try:
    import I2C

    ControllerClass = I2C.I2CMoveController
    HW_AVAILABLE = True
except Exception as e:
    print("⚠️  I2C niedostępne w tym środowisku:", e)
    HW_AVAILABLE = False

    class DummyI2CMoveController:
        def __init__(self, *args, **kwargs):
            print("🧪 Używam atrapy I2CMoveController (bez sprzętu).")

        def send_move_command(self, fx, fy, tx, ty) -> bool:
            # tylko log – tu można też dodać zapis do pliku
            print(f"[I2C:DUMMY] {fx:.1f} {fy:.1f} -> {tx:.1f} {ty:.1f}")
            return True

    ControllerClass = DummyI2CMoveController
# ================== KONFIGURACJA FIZYCZNA ==================
SQUARE_SIZE = 43.6  # mm
# Środek pola a1 względem homingu:
BOARD_ORIGIN_X_MM = 60.8  # X (kolumny a..h)
BOARD_ORIGIN_Y_MM = 46.2  # Y (rząd 1..8)

X_DIR = +1  # +X idzie od 'a' do 'h'
Y_DIR = +1  # +Y idzie od '1' do '8'

LANE_OFFSET = SQUARE_SIZE / 2  # 21.8 mm — tor głównej figury (pół pola)
OBSTACLE_SLIDE = 9.0  # 9 mm — rozsunięcie przeszkody prostopadle
MM_RESOLUTION = 0.1  # kwantyzacja mm

# ================== DANE SZACHOWE ==================
START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

START_COUNTS = {
    "pawn": 8,
    "rook": 2,
    "knight": 2,
    "bishop": 2,
    "queen": 1,
    "king": 1,
}
FEN_SYMBOLS = {
    "P": ("white", "pawn"),
    "R": ("white", "rook"),
    "N": ("white", "knight"),
    "B": ("white", "bishop"),
    "Q": ("white", "queen"),
    "K": ("white", "king"),
    "p": ("black", "pawn"),
    "r": ("black", "rook"),
    "n": ("black", "knight"),
    "b": ("black", "bishop"),
    "q": ("black", "queen"),
    "k": ("black", "king"),
}
FILES = "abcdefgh"


# ================== POMOCNICZE ==================
def q(x: float, qv: float = MM_RESOLUTION) -> float:
    return round(x / qv) * qv


@dataclass
class Step:
    f_x: float
    f_y: float
    t_x: float
    t_y: float
    note: str = ""

    def quantize(self):
        self.f_x = q(self.f_x)
        self.f_y = q(self.f_y)
        self.t_x = q(self.t_x)
        self.t_y = q(self.t_y)
        return self


def algebraic_to_idx(square: str) -> Tuple[int, int]:
    f = ord(square[0].lower()) - ord("a")  # 0..7
    r = int(square[1]) - 1  # 0..7
    return f, r


def idx_to_algebraic(f: int, r: int) -> str:
    return chr(ord("a") + f) + str(r + 1)


def grid_to_mm(file_idx: int, rank_idx: int) -> Tuple[float, float]:
    x = BOARD_ORIGIN_X_MM + X_DIR * (file_idx * SQUARE_SIZE)
    y = BOARD_ORIGIN_Y_MM + Y_DIR * (rank_idx * SQUARE_SIZE)
    return float(x), float(y)


def square_to_coords(square: str) -> Tuple[float, float]:
    f, r = algebraic_to_idx(square)
    return grid_to_mm(f, r)


def nearest_grid_idx(x_mm: float, y_mm: float) -> Tuple[int, int]:
    fx = round((x_mm - BOARD_ORIGIN_X_MM) / (X_DIR * SQUARE_SIZE))
    ry = round((y_mm - BOARD_ORIGIN_Y_MM) / (Y_DIR * SQUARE_SIZE))
    return int(fx), int(ry)


def get_occupied_from_fen(fen: str) -> Set[Tuple[int, int]]:
    board = fen.split()[0]
    occ: Set[Tuple[int, int]] = set()
    rank = 7
    file = 0
    for ch in board:
        if ch == "/":
            rank -= 1
            file = 0
        elif ch.isdigit():
            file += int(ch)
        else:
            if ch in FEN_SYMBOLS:
                occ.add((file, rank))
            file += 1
    return occ


def counts_from_fen(fen: str) -> Dict[str, Dict[str, int]]:
    board = fen.split()[0]
    counts = {
        "white": {k: 0 for k in START_COUNTS},
        "black": {k: 0 for k in START_COUNTS},
    }
    for ch in board:
        if ch in ("/",) or ch.isdigit():
            continue
        if ch in FEN_SYMBOLS:
            color, piece = FEN_SYMBOLS[ch]
            counts[color][piece] += 1
    return counts


# ================== PARKING WG ZASAD ==================
def starting_files_for_piece(piece: str, color: str) -> List[int]:
    base = {
        "rook": [0, 7],
        "knight": [1, 6],
        "bishop": [2, 5],
        "queen": [3],
        "king": [4],
    }.get(piece.lower(), list(range(8)))
    # preferencja „lewej” dla koloru: u czarnych lewy to wyższy indeks
    return sorted(base, reverse=(color == "black"))


def pawn_parking_slot_xy(color: str, slot_idx: int) -> Tuple[float, float]:
    """
    Pionki odkładamy: lewa krawędź gracza, w głąb.
    - białe: file = -1, rank: 0 + slot_idx
    - czarne: file = 8,  rank: 7 - slot_idx
    """
    x_file = -1 if color == "white" else 8
    y_rank = (0 + slot_idx) if color == "white" else (7 - slot_idx)
    return grid_to_mm(x_file, y_rank)


def special_parking_slot_xy(
    piece: str, color: str, slot_idx: int
) -> Tuple[float, float]:
    """
    Figury specjalne: przed planszą (rank = -1 białe, 8 czarne),
    na relatywnych plikach z preferencją lewej.
    """
    files_pref = starting_files_for_piece(piece, color)
    file_idx = files_pref[min(slot_idx, len(files_pref) - 1)]
    y_rank = -1 if color == "white" else 8
    return grid_to_mm(file_idx, y_rank)


# ================== MECHANIKA: SLIDE + LANE ==================
def slide_steps_at(x: float, y: float, axis: str, direction: int) -> List[Step]:
    s: List[Step] = []
    if axis == "x":
        dx = direction * OBSTACLE_SLIDE
        s.append(Step(x, y, x + dx, y, "Slide obstacle").quantize())
        s.append(Step(x + dx, y, x, y, "Recenter obstacle").quantize())
    else:
        dy = direction * OBSTACLE_SLIDE
        s.append(Step(x, y, x, y + dy, "Slide obstacle").quantize())
        s.append(Step(x, y + dy, x, y, "Recenter obstacle").quantize())
    return s


def v_segment_with_slides(frm_sq: str, to_sq: str, fen: str) -> List[Step]:
    steps: List[Step] = []
    fx, fy = square_to_coords(frm_sq)
    tx, ty = square_to_coords(to_sq)
    f_idx, r_from = algebraic_to_idx(frm_sq)
    _, r_to = algebraic_to_idx(to_sq)
    occupied = get_occupied_from_fen(fen)
    dir_x = +1 if f_idx < 4 else -1
    x_lane = fx + dir_x * LANE_OFFSET
    lo, hi = sorted((r_from, r_to))
    for r in range(lo + 1, hi):
        if (f_idx, r) in occupied:
            ox, oy = grid_to_mm(f_idx, r)
            steps.append(
                Step(
                    fx, fy, ox, oy, f"Approach {idx_to_algebraic(f_idx, r)}"
                ).quantize()
            )
            fx, fy = ox, oy
            for st in slide_steps_at(ox, oy, "x", dir_x):
                steps.append(st)
                fx, fy = st.t_x, st.t_y
            ofx, ofy = square_to_coords(frm_sq)
            steps.append(Step(fx, fy, ofx, ofy, "Back to piece").quantize())
            fx, fy = ofx, ofy
    steps.append(Step(fx, fy, x_lane, fy, "V: offset").quantize())
    fx = x_lane
    steps.append(Step(fx, fy, x_lane, ty, "V: lane").quantize())
    fy = ty
    steps.append(Step(fx, fy, tx, ty, "V: recenter").quantize())
    return steps


def h_segment_with_slides(frm_sq: str, to_sq: str, fen: str) -> List[Step]:
    steps: List[Step] = []
    fx, fy = square_to_coords(frm_sq)
    tx, ty = square_to_coords(to_sq)
    f_from, r_idx = algebraic_to_idx(frm_sq)
    f_to, _ = algebraic_to_idx(to_sq)
    occupied = get_occupied_from_fen(fen)
    dir_y = +1 if r_idx < 4 else -1
    y_lane = fy + dir_y * LANE_OFFSET
    lo, hi = sorted((f_from, f_to))
    for f in range(lo + 1, hi):
        if (f, r_idx) in occupied:
            ox, oy = grid_to_mm(f, r_idx)
            steps.append(
                Step(
                    fx, fy, ox, oy, f"Approach {idx_to_algebraic(f, r_idx)}"
                ).quantize()
            )
            fx, fy = ox, oy
            for st in slide_steps_at(ox, oy, "y", dir_y):
                steps.append(st)
                fx, fy = st.t_x, st.t_y
            ofx, ofy = square_to_coords(frm_sq)
            steps.append(Step(fx, fy, ofx, ofy, "Back to piece").quantize())
            fx, fy = ofx, ofy
    steps.append(Step(fx, fy, fx, y_lane, "H: offset").quantize())
    fy = y_lane
    steps.append(Step(fx, fy, tx, y_lane, "H: lane").quantize())
    fx = tx
    steps.append(Step(fx, fy, tx, ty, "H: recenter").quantize())
    return steps


def move_between_squares(frm_sq: str, to_sq: str, fen: str) -> List[Step]:
    f_from, r_from = algebraic_to_idx(frm_sq)
    f_to, r_to = algebraic_to_idx(to_sq)
    s: List[Step] = []
    if f_from == f_to:
        s += v_segment_with_slides(frm_sq, to_sq, fen)
    elif r_from == r_to:
        s += h_segment_with_slides(frm_sq, to_sq, fen)
    else:
        mid = f"{to_sq[0]}{frm_sq[1]}"
        s += h_segment_with_slides(frm_sq, mid, fen)
        s += v_segment_with_slides(mid, to_sq, fen)
    return s


# ================== OPERACJE: FIELD <-> PARKING ==================
def field_to_parking(square: str, park_x: float, park_y: float, fen: str) -> List[Step]:
    steps: List[Step] = []
    f_idx, r_idx = algebraic_to_idx(square)
    px_idx, py_idx = nearest_grid_idx(park_x, park_y)
    if py_idx in (-1, 8):
        # do pionowej krawędzi nad/poniżej tego samego file
        ex, ey = grid_to_mm(f_idx, py_idx)
        s1 = v_segment_with_slides(
            square, idx_to_algebraic(f_idx, max(0, min(7, py_idx))), fen
        )
        if s1:
            s1[-1] = Step(s1[-2].t_x, s1[-2].t_y, ex, ey, "V: to edge").quantize()
        steps += s1
        steps.append(Step(ex, ey, park_x, park_y, "Offboard: to parking").quantize())
    else:
        ex, ey = grid_to_mm(px_idx, r_idx)
        s1 = h_segment_with_slides(
            square, idx_to_algebraic(max(0, min(7, px_idx)), r_idx), fen
        )
        if s1:
            s1[-1] = Step(s1[-2].t_x, s1[-2].t_y, ex, ey, "H: to edge").quantize()
        steps += s1
        steps.append(Step(ex, ey, park_x, park_y, "Offboard: to parking").quantize())
    return steps


def parking_to_field(park_x: float, park_y: float, to_sq: str, fen: str) -> List[Step]:
    steps: List[Step] = []
    f_idx, r_idx = algebraic_to_idx(to_sq)
    px_idx, py_idx = nearest_grid_idx(park_x, park_y)
    if py_idx in (-1, 8):
        ex, ey = grid_to_mm(f_idx, py_idx)
        steps.append(Step(park_x, park_y, ex, ey, "Offboard: from parking").quantize())
        s2 = v_segment_with_slides(
            idx_to_algebraic(f_idx, max(0, min(7, py_idx))), to_sq, fen
        )
        if s2:
            s2[0] = Step(ex, ey, s2[0].t_x, s2[0].t_y, "V: from edge").quantize()
        steps += s2
    else:
        ex, ey = grid_to_mm(px_idx, r_idx)
        steps.append(Step(park_x, park_y, ex, ey, "Offboard: from parking").quantize())
        s2 = h_segment_with_slides(
            idx_to_algebraic(max(0, min(7, px_idx)), r_idx), to_sq, fen
        )
        if s2:
            s2[0] = Step(ex, ey, s2[0].t_x, s2[0].t_y, "H: from edge").quantize()
        steps += s2
    return steps


# ================== RUCHY PARTII ==================
def standard_move(msg: dict) -> List[Step]:
    return move_between_squares(msg["from"], msg["to"], msg["fen"])


def compute_capture_parking(
    piece_captured: str, color_captured: str, fen: str
) -> Tuple[float, float]:
    if piece_captured.lower() == "pawn":
        # liczba pionków już zbitych wg fen → slot
        # tu uproszczenie: kolejny slot = liczba brakujących pionków (start - present) - 1
        present = counts_from_fen(fen)
        missing = START_COUNTS["pawn"] - present[color_captured]["pawn"]
        slot = max(0, missing - 1)
        return pawn_parking_slot_xy(color_captured, slot)
    # specjalne: ile brakujących typu → slot wg lewych plików
    present = counts_from_fen(fen)
    piece = piece_captured.lower()
    missing = START_COUNTS[piece] - present[color_captured][piece]
    slot = max(0, missing - 1)
    return special_parking_slot_xy(piece, color_captured, slot)


def capture_move(msg: dict) -> List[Step]:
    frm, to, fen = msg["from"], msg["to"], msg["fen"]
    piece_captured = msg.get("piece_captured", "piece")
    color_captured = msg.get("color_captured", "white")
    park_x, park_y = compute_capture_parking(piece_captured, color_captured, fen)
    steps: List[Step] = []
    steps += field_to_parking(to, park_x, park_y, fen)
    steps += move_between_squares(frm, to, fen)
    return steps


# ================== RESET: z bieżącego FEN do startu ==================
def parse_fen_pieces(fen: str) -> List[Tuple[str, str, str]]:
    """
    Zwraca listę (square, color, piece) dla wszystkich figur na planszy wg FEN.
    """
    board = fen.split()[0]
    out: List[Tuple[str, str, str]] = []
    rank = 7
    file = 0
    for ch in board:
        if ch == "/":
            rank -= 1
            file = 0
            continue
        if ch.isdigit():
            file += int(ch)
            continue
        if ch in FEN_SYMBOLS:
            color, piece = FEN_SYMBOLS[ch]
            sq = idx_to_algebraic(file, rank)
            out.append((sq, color, piece))
            file += 1
        else:
            file += 1
    return out


def reset_steps(current_fen: str, target_fen: str = START_FEN) -> List[Step]:
    """
    1) Zdejmij WSZYSTKIE figury z aktualnej pozycji na parkingi (wg zasad slotów, lewa preferencja).
    2) Z parkingów rozstaw na pozycji startowej.
    (Używa lokalnych liczników slotów, nie FEN-u, żeby było deterministycznie.)
    """
    steps: List[Step] = []

    # 1) OPRÓŻNIANIE — liczniki slotów dla parkingów
    pawn_slots = {"white": 0, "black": 0}
    spec_slots: Dict[str, Dict[str, int]] = {"white": {}, "black": {}}

    for sq, color, piece in parse_fen_pieces(current_fen):
        if piece == "pawn":
            px, py = pawn_parking_slot_xy(color, pawn_slots[color])
            pawn_slots[color] += 1
        else:
            spec_slots[color].setdefault(piece, 0)
            idx = spec_slots[color][piece]
            px, py = special_parking_slot_xy(piece, color, idx)
            spec_slots[color][piece] += 1

        steps += field_to_parking(sq, px, py, current_fen)

    # 2) ROZSTAWIENIE — liczniki slotów do pobierania z parkingu
    pawn_take = {"white": 0, "black": 0}
    spec_take: Dict[str, Dict[str, int]] = {"white": {}, "black": {}}

    for sq, color, piece in parse_fen_pieces(target_fen):
        if piece == "pawn":
            px, py = pawn_parking_slot_xy(color, pawn_take[color])
            pawn_take[color] += 1
        else:
            spec_take[color].setdefault(piece, 0)
            idx = spec_take[color][piece]
            px, py = special_parking_slot_xy(piece, color, idx)
            spec_take[color][piece] += 1

        steps += parking_to_field(px, py, sq, target_fen)

    return steps


# ================== I2C WYKONANIE ==================
def print_step(s: Step):
    print(f"➡️ {s.note:18s}  {s.f_x:.1f} {s.f_y:.1f}  →  {s.t_x:.1f} {s.t_y:.1f}")


def compress_zero_len(steps: List[Step], eps: float = 1e-6) -> List[Step]:
    return [s for s in steps if abs(s.f_x - s.t_x) > eps or abs(s.f_y - s.t_y) > eps]


def execute_steps(controller, steps: List[Step], delay_s: float = 0.03):
    steps = compress_zero_len(steps)
    last_to = None
    for s in steps:
        s.quantize()
        if last_to and (
            abs(last_to[0] - s.f_x) > 1e-6 or abs(last_to[1] - s.f_y) > 1e-6
        ):
            sync = Step(last_to[0], last_to[1], s.f_x, s.f_y, "Sync").quantize()
            print_step(sync)
            ok = controller.send_move_command(
                q(sync.f_x), q(sync.f_y), q(sync.t_x), q(sync.t_y)
            )
            if not ok:
                print("❌ I2C error (sync)")
                return
            time.sleep(delay_s)
        print_step(s)
        ok = controller.send_move_command(q(s.f_x), q(s.f_y), q(s.t_x), q(s.t_y))
        if not ok:
            print("❌ I2C error")
            return
        time.sleep(delay_s)
        last_to = (s.t_x, s.t_y)


# ================== POKAZ: MAT SZEWCZYKA + RESET ==================
def main():
    controller = ControllerClass(bus_number=1, slave_address=0x42)
    GAME = [
        {
            "from": "e2",
            "to": "e4",
            "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
            "type": None,
        },
        {
            "from": "e7",
            "to": "e5",
            "fen": "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",
            "type": None,
        },
        {
            "from": "d1",
            "to": "h5",
            "fen": "rnbqkbnr/pppp1ppp/8/4p2Q/4P3/8/PPPP1PPP/RNB1KBNR b KQkq - 1 2",
            "type": None,
        },
        {
            "from": "b8",
            "to": "c6",
            "fen": "r1bqkbnr/pppp1ppp/2n5/4p2Q/4P3/8/PPPP1PPP/RNB1KBNR w KQkq - 2 3",
            "type": None,
        },
        {
            "from": "f1",
            "to": "c4",
            "fen": "r1bqkbnr/pppp1ppp/2n5/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 3 3",
            "type": None,
        },
        {
            "from": "g8",
            "to": "f6",
            "fen": "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4",
            "type": None,
        },
        {
            "from": "h5",
            "to": "f7",  # Qxf7#
            "fen": "r1bqkb1r/pppp1Qpp/2n2n2/4p3/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 4",
            "type": "capture",
            "piece_captured": "pawn",
            "color_captured": "black",
        },
    ]

    print("♟️ Start pokazu: mat szewczyka")
    current_fen = START_FEN
    for i, msg in enumerate(GAME, 1):
        print("\n" + "=" * 60)
        print(f"Ruch {i}: {msg['from']} → {msg['to']}  (type={msg.get('type')})")
        if msg.get("type") == "capture":
            steps = capture_move(msg)
        else:
            steps = standard_move(msg)
        execute_steps(controller, steps, delay_s=0.03)
        current_fen = msg["fen"]

    print("\n🔄 RESET do pozycji startowej…")
    steps_reset = reset_steps(current_fen, START_FEN)
    execute_steps(controller, steps_reset, delay_s=0.03)

    print("\n✅ Koniec pokazu — mat + reset!")


if __name__ == "__main__":
    main()
