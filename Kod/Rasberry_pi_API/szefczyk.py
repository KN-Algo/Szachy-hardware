# Samowystarczalny pokaz „mat szewczyka” + RESET do pozycji startowej

import time
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

# globalna lista na przesunięte przeszkody
slid_obstacles: List[Tuple[float, float, int]] = []

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

        def send_homing(self):
            print("homing")
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


def slide_obstacle_at(
    file_idx: int, rank_idx: int, axis: str, direction: int, steps: List[Step]
):
    """
    Dodaje krok odsunięcia przeszkadzającej figury wzdłuż osi X lub Y.
    - file_idx, rank_idx -> współrzędne przeszkadzającej figury
    - axis -> "x" (ruch w poziomie) lub "y" (ruch w pionie)
    - direction -> w którą stronę przesunąć figurę (±1)
    - steps -> lista Step, do której dodajemy ruch Slide
    """
    x, y = square_to_coords(idx_to_algebraic(file_idx, rank_idx))
    if axis == "x":
        dx = -direction * OBSTACLE_SLIDE
        steps.append(
            Step(
                x, y, x + dx, y, f"Slide {idx_to_algebraic(file_idx, rank_idx)}"
            ).quantize()
        )
    else:
        dy = -direction * OBSTACLE_SLIDE
        steps.append(
            Step(
                x, y, x, y + dy, f"Slide {idx_to_algebraic(file_idx, rank_idx)}"
            ).quantize()
        )

    # przesunięta figura zostanie wycentrowana na końcu w execute_steps
    slid_obstacles.append((x, y, 0 if axis == "x" else 1))


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


def hv_slide_with_obstacles(frm_sq: str, to_sq: str, fen: str) -> List[Step]:
    """
    Ruch figury z torowaniem przez przesunięcie przeszkód.
    1. Przesuwa przeszkody w osi X i Y (start + cel segmentów).
    2. Nasza figura porusza się: V → H → recenter.
    3. Na końcu przesunięte figury wracają na miejsca w execute_steps.
    """
    steps: List[Step] = []
    fx, fy = square_to_coords(frm_sq)
    tx, ty = square_to_coords(to_sq)
    f_idx_from, r_idx_from = algebraic_to_idx(frm_sq)
    f_idx_to, r_idx_to = algebraic_to_idx(to_sq)
    dir_x = +1 if f_idx_from < 4 else -1
    dir_y = +1 if r_idx_from < 4 else -1
    # Zajęte pola wg aktualnego FEN
    occupied = get_occupied_from_fen(fen)

    if (f_idx_to, r_idx_to) in occupied:
        occupied.discard((f_idx_to, r_idx_to))
    # =================== Zbieranie przeszkód ===================
    # Przeszkody w osi X (H)
    x_obstacles = [
        (f, r_idx_from)
        for f in range(min(f_idx_from, f_idx_to) + 1, max(f_idx_from, f_idx_to))
        if (f, r_idx_from) in occupied
    ] + [
        (f_idx_to, r)
        for r in range(min(r_idx_from, r_idx_to), max(r_idx_from, r_idx_to) + 1)
        if (f_idx_to, r) in occupied
    ]

    # Przeszkody w osi Y (V)
    y_obstacles = [
        (f_idx_to, r)
        for r in range(min(r_idx_from, r_idx_to) + 1, max(r_idx_from, r_idx_to))
        if (f_idx_to, r) in occupied
    ] + [
        (f, r_idx_from)
        for f in range(min(f_idx_from, f_idx_to), max(f_idx_from, f_idx_to) + 1)
        if (f, r_idx_from) in occupied
    ]

    # =================== Slide przeszkód ===================
    for f, r in x_obstacles:
        slide_obstacle_at(
            f, r, "x", 1, steps
        )  # kierunek +1, można dynamicznie dobierać
    for f, r in y_obstacles:
        slide_obstacle_at(f, r, "y", 1, steps)

    if not x_obstacles and not y_obstacles:
        steps.append(Step(fx, fy, tx, ty, "Direct move").quantize())
        return steps
    # =================== Ruch naszej figury ===================
    # 1️⃣ Ze startu zejście na szynę poziomą (H)
    # przesunięcie w osi X do poziomu startu szyny pionowej (poziom lane H)
    y_lane = (
        fy + dir_y * -LANE_OFFSET
    )  # można tu dopasować offset lane, jeśli używasz LANE_OFFSET
    steps.append(Step(fx, fy, fx, y_lane, "H: descend to H lane").quantize())

    # 2️⃣ Jazda pozioma wzdłuż szyny H do kolumny startu segmentu pionowego
    x_lane = tx + dir_x * LANE_OFFSET  # kolumna docelowa lane H
    steps.append(Step(fx, y_lane, x_lane, y_lane, "H: lane horizontal").quantize())

    # 3️⃣ Jazda pionowa wzdłuż szyny V do docelowego rzędu
    steps.append(Step(x_lane, y_lane, x_lane, ty, "V: lane vertical").quantize())

    # 4️⃣ Recenter na finalnym polu
    steps.append(Step(x_lane, ty, tx, ty, "Recenter").quantize())

    return steps


def move_between_squares(frm_sq: str, to_sq: str, fen: str) -> List[Step]:
    """
    Zastępuje poprzednie segmenty H/V jednym ruchem z torowaniem przeszkód.
    Funkcja korzysta z hv_slide_with_obstacles.
    """
    return hv_slide_with_obstacles(frm_sq, to_sq, fen)


# ================== OPERACJE: FIELD <-> PARKING ==================


def field_to_parking(square: str, park_x: float, park_y: float, fen: str) -> List[Step]:
    """
    Funkcja przesuwa figurę z pola planszy do slotu parkingowego.
    Wykorzystuje nową funkcję hv_slide_with_obstacles, zamiast
    osobnych segmentów H/V.
    """
    steps: List[Step] = []
    f_idx, r_idx = algebraic_to_idx(square)
    px_idx, py_idx = nearest_grid_idx(park_x, park_y)

    # docelowy punkt w gridzie (przy krawędzi planszy lub w pobliżu parkingu)
    ex, ey = grid_to_mm(px_idx, py_idx)

    # generujemy tor z uwzględnieniem przeszkód w obu osiach
    # od pola źródłowego do docelowego punktu na planszy (przed offboard)
    target_sq = idx_to_algebraic(max(0, min(7, px_idx)), max(0, min(7, py_idx)))
    steps += hv_slide_with_obstacles(square, target_sq, fen)

    # następnie ruch poza planszę do dokładnego slotu parkingowego
    steps.append(Step(ex, ey, park_x, park_y, "Offboard: to parking").quantize())

    return steps


def parking_to_field(park_x: float, park_y: float, to_sq: str, fen: str) -> List[Step]:
    """
    Funkcja przesuwa figurę z parkingu z powrotem na planszę.
    Wykorzystuje nową funkcję hv_slide_with_obstacles zamiast
    osobnych segmentów H/V.
    """
    steps: List[Step] = []

    # 1️⃣ Offboard: z parkingu do najbliższego punktu na planszy
    px_idx, py_idx = nearest_grid_idx(park_x, park_y)
    f_idx, r_idx = algebraic_to_idx(to_sq)
    ex, ey = grid_to_mm(px_idx, py_idx)
    steps.append(Step(park_x, park_y, ex, ey, "Offboard: from parking").quantize())

    # 2️⃣ Ruch po planszy z uwzględnieniem przeszkód
    start_sq = idx_to_algebraic(max(0, min(7, px_idx)), max(0, min(7, py_idx)))
    steps += hv_slide_with_obstacles(start_sq, to_sq, fen)

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
    global slid_obstacles
    steps = compress_zero_len(steps)

    for s in steps:
        s.quantize()
        print_step(s)

        ok = controller.send_move_command(q(s.f_x), q(s.f_y), q(s.t_x), q(s.t_y))
        if not ok:
            print("❌ I2C error")
            return
        time.sleep(delay_s)
        controller.send_homing()

    # 👇 dopiero teraz recenter wszystkich przesuniętych przeszkód
    for ox, oy, axis in slid_obstacles:
        if axis == 0:  # X-axis
            dx = OBSTACLE_SLIDE
            ok = controller.send_move_command(ox + dx, oy, ox, oy)
        else:  # Y-axis
            dy = OBSTACLE_SLIDE
            ok = controller.send_move_command(ox, oy + dy, ox, oy)

        if not ok:
            print("❌ I2C error (recenter)")
            return
        time.sleep(delay_s)
        controller.send_homing()

    slid_obstacles = []


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
    controller.send_homing()
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
