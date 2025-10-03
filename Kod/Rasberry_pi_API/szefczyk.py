import json
import config

from obstacles import obstacles
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple
from capture import capture_move
from castle import castling_move
from promotion import promotion_move
from promotion_capture import promotion_capture_move
from square_to_cords import square_to_coords
from standard_move import standard_move
from steps import Step

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
    controller.send_homing()
    for move in GAME:
        move_type = move["type"]
        obstacles_list = None
        obstacles_list = obstacles(move)
        match move_type:
                    case None:
                        print("✅standard✅")
                        steps = standard_move(move, obstacles_list)
                    case "capture":
                        print("capture move")
                        steps = capture_move(move, obstacles_list)
                    case "castling":
                        print("roszada")
                        steps = castling_move(move)
                    case "promotion":
                        print("promotion")
                        steps = promotion_move(move)
                    case "promotion_capture":
                        print("promotion capture")
                        steps = promotion_capture_move(move)
                    case _:
                        pass
            
        for step in steps:
            print(f"➡️ {step.note}")

            ok = controller.send_move_command(step.f_x, step.f_y, step.t_x, step.t_y)
            controller.send_homing()
            #print(step.f_x, step.f_y, step.t_x, step.t_y)
            if not ok:
                print("❌ Błąd ruchu I2C")
                break           

    print("\n♟️ reset!")

    RESET = [
        {
            "from": "f7",
            "to": "d1",
            "fen": "r1bqkb1r/pppp2pp/2n2n2/4p3/2B1P3/8/PPPP1PPP/RNBQK1NR b KQkq - 0 4",
            "type": None,
        },
        {
            "from": "c4",
            "to": "f1",
            "fen": "r1bqkb1r/pppp2pp/2n2n2/4p3/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 4",
            "type": None,
        },
        {
            "from": "c6",
            "to": "b8",
            "fen": "rnbqkb1r/pppp2pp/5n2/4p3/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 4",
            "type": None,
        },
        {
            "from": "f6",
            "to": "g8",
            "fen": "rnbqkbnr/pppp2pp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 4",
            "type": None,
        },
                {
            "from": "e4",
            "to": "e2",
            "fen": "rnbqkbnr/pppp2pp/8/4p3/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 4",
            "type": None,
        },
                {
            "from": "e5",
            "to": "e7",
            "fen": "rnbqkbnr/ppppp1pp/8/8/8/8/PPPP1PPP/RNBQKBNR b KQkq - 0 4",
            "type": None,
        },
    ]

    for move in RESET:
        move_type = move["type"]
        obstacles_list = None
        obstacles_list = obstacles(move)
        match move_type:
                    case None:
                        print("✅standard✅")
                        steps = standard_move(move, obstacles_list)
                    case "capture":
                        print("capture move")
                        steps = capture_move(move, obstacles_list)
                    case "castling":
                        print("roszada")
                        steps = castling_move(move)
                    case "promotion":
                        print("promotion")
                        steps = promotion_move(move)
                    case "promotion_capture":
                        print("promotion capture")
                        steps = promotion_capture_move(move)
                    case _:
                        pass
        
        for step in steps:
            print(f"➡️ {step.note}")

            ok = controller.send_move_command(step.f_x, step.f_y, step.t_x, step.t_y)
            controller.send_homing()
            #print(step.f_x, step.f_y, step.t_x, step.t_y)
            if not ok:
                print("❌ Błąd ruchu I2C")
                break

    ok = controller.send_move_command(431.4, 373.2, 278.8, 307.8)   

    print("\n✅ Koniec pokazu — mat + reset!")

if __name__ == "__main__":
    main()
