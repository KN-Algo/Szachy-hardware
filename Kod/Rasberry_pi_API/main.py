import json
import threading
import time
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

import chess
import config
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
from board_reset import reset_pieces_to_start
from capture import capture_move
from castle import castling_move
from promotion import promotion_move
from promotion_capture import promotion_capture_move
from square_to_cords import square_to_coords
from standard_move import standard_move
from steps import Step

status_msg = {"status": "ready"}
last_board = dict()
board = dict()
from_field = []
to_field = None
current_fen = config.START_FEN

try:
    import UART

    PicoClass = UART.PicoController
    HW_AVAILABLE = True
except Exception as e:
    print("⚠️  PICO niedostępne w tym środowisku:", e)
    HW_AVAILABLE = False

    class DummyI2CMoveController:
        def __init__(self, *args, **kwargs):
            print("🧪 Używam atrapy I2CMoveController (bez sprzętu).")

        def move_to(self, fx, fy, tx, ty, electromagnet=True) -> bool:
            # tylko log – tu można też dodać zapis do pliku
            print(f"[DUMMY] {fx:.1f} {fy:.1f} -> {tx:.1f} {ty:.1f}")
            return True

        def homing(self):
            print("homing")
            return True

        def get_statu(self):
            print("status")
            return True

        def read_board(self):
            return dict()

        def set_led(self, color, state):
            print(f"kolor {color} ustawiony na {state}")
            return True

        def close(self):
            print("pico con close")
            return True

    PicoClass = DummyI2CMoveController

pico = PicoClass()

led_color = "BLACK"
new_color = "WHITE"

pico.set_led(led_color, "ON")
pico.set_led(new_color, "ON")

pico.homing()
pico.move_to(0, 0, 60.8, 46.2)
pico.get_status()

pico.set_led(led_color, "OFF")
pico.set_led(new_color, "OFF")


def color_swap():
    global led_color
    global new_color
    pico.set_led(led_color, "OFF")
    new_color, led_color = led_color, new_color
    pico.set_led(led_color, "ON")


def board_compare():
    global last_board
    global board
    global from_field
    global to_field

    # Zmieniamy listy na słowniki { 'A1': True, ... } dla szybszego porównania
    prev_map = {item["field"].upper(): item["status"] for item in last_board}
    new_map = {item["field"].upper(): item["status"] for item in board}

    # Przeglądamy wszystkie pola
    for field in prev_map:
        prev_status = prev_map[field]
        new_status = new_map.get(field)

        if prev_status != new_status:
            if prev_status is True and new_status is False:
                from_field.append(field.lower())
            elif prev_status is False and new_status is True:
                to_field = field.lower()

    return 0


def board_status():

    global status_msg
    global last_board
    global board
    global from_field
    global to_field
    global current_fen

    board = pico.read_board()
    last_board = board

    while True:

        board_compare()

        # Jeśli wykryto ruch
        if from_field:
            fen_board = chess.Board(current_fen)
            while True:
                last_board = board
                time.sleep(0.3)
                board = pico.read_board()

                board_compare()

                if to_field:
                    status_msg = {"from": from_field[0], "to": to_field}
                    last_board = board
                    from_field = []
                    to_field = None
                    client.publish("move/player", status_msg)

                    fen_move = chess.Move.from_uci(
                        status_msg["from"] + status_msg["to"]
                    )
                    try:
                        fen_board.push(fen_move)
                    except ValueError:
                        print("Nielegalny ruch, FEN nie zmieniony.")

                    break

                if len(from_field) >= 2:
                    last_board = board
                    while True:
                        time.sleep(0.3)
                        board = pico.read_board()

                        board_compare()

                        if to_field:
                            status_msg = {"from": from_field[1], "to": to_field}
                            last_board = board
                            from_field = []
                            to_field = None
                            client.publish("move/player", status_msg)

                            fen_move = chess.Move.from_uci(
                                status_msg["from"] + status_msg["to"]
                            )
                            try:
                                fen_board.push(fen_move)
                            except ValueError:
                                print("Nielegalny ruch, FEN nie zmieniony.")

                            break

                    break
            current_fen = fen_board
        board = pico.read_board()
        time.sleep(0.3)


def on_message(client, userdata, msg):

    global status_msg
    global current_fen

    try:
        if msg.topic == "control/restart/external":
            payload = msg.payload.decode()
            data = json.loads(payload)
            print(data)
            data["type"] = "reset"
            print("Wykryto reset")
            pico.set_led(new_color, "ON")
        else:
            if msg.topic != "move/raspi/rejected":
                color_swap()
            payload = msg.payload.decode()
            data = json.loads(payload)
            print("✅ Otrzymano:", data)

        steps = []
        move_type = None
        move_type = data.get("type")

        match move_type:
            case None:
                print("✅standard✅")
                frm = data["from"]
                to = data["to"]
                fen = data["fen"]
                if "action" == data:
                    frm, to = to, frm
                steps = standard_move(frm, to, fen)
            case "capture":
                print("capture move")
                steps = capture_move(data)
            case "castling":
                print("roszada")
                steps = castling_move(data)
            case "promotion":
                print("promotion")
                steps = promotion_move(data)
            case "promotion_capture":
                print("promotion capture")
                steps = promotion_capture_move(data)
            case "reset":
                print("reset")
                steps = reset_pieces_to_start(current_fen)
            case _:
                pass

        status_msg["status"] = "moving"
        client.publish("status/raspi", json.dumps(status_msg))

        for step in steps:
            print(f"➡️ {step.note}")

            ok = pico.move_to(
                round(step.f_x, 2),
                round(step.f_y, 2),
                round(step.t_x, 2),
                round(step.t_y, 2),
                True,
            )
            ok = True
            if not ok:
                print("❌ Błąd ruchu I2C")
                break

        current_fen = data["fen"]
        time.sleep(2)
        status_msg["status"] = "ready"
        client.publish("status/raspi", json.dumps(status_msg))

    except Exception as e:
        status_msg["status"] = "error"
        client.publish("status/raspi", json.dumps(status_msg))
        print(e)


# Konfiguracja klienta MQTT
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect("localhost", 1883)
client.subscribe("move/raspi")
client.subscribe("move/raspi/rejected")
client.subscribe("control/restart/external")
client.on_message = on_message

status_msg["status"] = "ready"
client.publish("status/raspi", json.dumps(status_msg))

print("🔄 Nasłuchiwanie na topicu: move/raspi...")


# board_thread = threading.Thread(target=board_status, daemon=True)

# board_thread.start()

try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\nPrzerwano przez użytkownika (Ctrl+C). Zamykam...")
finally:
    pico.set_led(led_color, "OFF")
    pico.set_led(new_color, "OFF")
    pico.close()
    client.disconnect()
    print("MQTT client odłączony. Do zobaczenia 👋")
