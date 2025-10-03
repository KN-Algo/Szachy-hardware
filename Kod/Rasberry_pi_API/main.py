import json
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

import config
import paho.mqtt.client as mqtt
from capture import capture_move
from castle import castling_move
from obstacles import obstacles
from promotion import promotion_move
from promotion_capture import promotion_capture_move
from square_to_cords import square_to_coords
from standard_move import standard_move
from steps import Step

# controller = I2C.I2CMoveController(bus_number=1, slave_address=0x42)


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
            print(f"[I2C:DUMMY] {fx:.1f} {fy:.1f} -> {tx:.1f} {ty:.1f}")
            return True

        def homing(self):
            print("homing")
            return True

    PicoClass = DummyI2CMoveController

pico = PicoClass()

pico.homing()


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        data = json.loads(payload)
        print("✅ Otrzymano:", data)

        steps = None
        move_type = None
        move_type = data.get("type")

        obstacles_list = None
        obstacles_list = obstacles(data)
        match move_type:
            case None:
                print("✅standard✅")
                steps = standard_move(data, obstacles_list)
            case "capture":
                print("capture move")
                steps = capture_move(data, obstacles_list)
            case "castling":
                print("roszada")
                steps = castling_move(data)
            case "promotion":
                print("promotion")
                steps = promotion_move(data)
            case "promotion_capture":
                print("promotion capture")
                steps = promotion_capture_move(data)
            case _:
                pass

        for step in steps:
            print(f"➡️ {step.note}")

            # ok = controller.send_move_command(step.f_x, step.f_y, step.t_x, step.t_y)
            ok = True
            print(step.f_x, step.f_y, step.t_x, step.t_y)
            if not ok:
                print("❌ Błąd ruchu I2C")
                break

    except Exception as e:
        print(e)


# Konfiguracja klienta MQTT
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect("localhost", 1883)
client.subscribe("move/raspi")
client.on_message = on_message

print("🔄 Nasłuchiwanie na topicu: move/raspi...")

try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\nPrzerwano przez użytkownika (Ctrl+C). Zamykam...")
finally:
    client.disconnect()
    print("MQTT client odłączony. Do zobaczenia 👋")
