import serial
import time

class PicoController:
    def __init__(self, port='/dev/ttyAMA0', baudrate=115200):
        """
        Inicjalizacja połączenia z Raspberry Pi Pico.

        Args:
            port (str): Port szeregowy do komunikacji z Pico.
            baudrate (int): Prędkość transmisji szeregowej.
        """
        self.serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=2
        )
        time.sleep(2)  # Daj czas na inicjalizację
        print(f"✅ Połączono z Pico na {port}")

        # Odczytaj wiadomość READY
        response = self.wait_for_response()
        print(f"Pico: {response}")

    def send_command(self, command):
        """
        Wyślij komendę do Pico.

        Args:
            command (str): Komenda w formacie tekstowym.
        """
        cmd = f"{command}\n"
        self.serial.write(cmd.encode('utf-8'))
        print(f"📤 Wysłano: {command}")

    def wait_for_response(self, timeout=5):
        """
        Czekaj na odpowiedź od Pico.

        Args:
            timeout (float): Maksymalny czas oczekiwania w sekundach.

        Returns:
            str: Odpowiedź od Pico lub "TIMEOUT" jeśli nie otrzymano odpowiedzi.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.serial.in_waiting > 0:
                response = self.serial.readline().decode('utf-8').strip()
                return response
            time.sleep(0.01)
        return "TIMEOUT"

    def move_to(self, start_x, start_y, end_x, end_y, electromagnet=False):
        """
        Przesuń głowicę od pozycji startowej do końcowej.

        Args:
            start_x (float): Pozycja startowa X w mm.
            start_y (float): Pozycja startowa Y w mm.
            end_x (float): Pozycja końcowa X w mm.
            end_y (float): Pozycja końcowa Y w mm.
            electromagnet (bool): True jeśli elektromagnes ma być włączony podczas ruchu.

        Returns:
            bool: True jeśli ruch zakończony sukcesem, False w przeciwnym wypadku.
        """
        magnet_flag = 1 if electromagnet else 0
        command = f"MOVE:{start_x},{start_y},{end_x},{end_y},{magnet_flag}"
        self.send_command(command)

        # Czekaj na MOVE_ACK
        ack = self.wait_for_response()
        print(f"📥 Pico: {ack}")

        if ack == "MOVE_ACK":
            done = self.wait_for_response(timeout=30)
            print(f"📥 Pico: {done}")
            return done == "MOVE_DONE"
        return False

    def homing(self):
        """
        Wykonaj procedurę homing, ustawiając głowicę w pozycji (0,0).

        Returns:
            bool: True jeśli homing zakończony sukcesem, False w przeciwnym wypadku.
        """
        print("🏠 Rozpoczynam homing...")
        self.send_command("HOMING")

        ack = self.wait_for_response()
        print(f"📥 Pico: {ack}")

        if ack == "HOMING_ACK":
            # Czekaj na start
            start = self.wait_for_response(timeout=10)
            print(f"📥 Pico: {start}")

            # Czekaj na zakończenie
            done = self.wait_for_response(timeout=30)
            print(f"📥 Pico: {done}")
            return done == "HOMING_DONE"
        return False

    def read_board(self):
        """
        Pobierz status wszystkich pól szachownicy.

        Returns:
            list: Lista słowników [{'field': 'A1', 'status': True/False}, ...] 
                  lub None jeśli wystąpił problem z odczytem.
        """
        print("📋 Pobieram status szachownicy...")
        self.send_command("SEND_BOARD")

        ack = self.wait_for_response()
        print(f"📥 Pico: {ack}")

        if ack != "BOARD_ACK":
            return None

        board_data = []

        # Czekaj na BOARD_START
        start = self.wait_for_response()
        print(f"📥 Pico: {start}")

        if start != "BOARD_START":
            return None

        # Odczytuj dane pól
        while True:
            response = self.wait_for_response(timeout=10)
            print(f"📥 Pico: {response}")

            if response == "BOARD_END":
                break

            if response.startswith("FIELD:"):
                try:
                    field_str, status_str = response[6:].split(",")
                    status = bool(int(status_str))
                    board_data.append({'field': field_str, 'status': status})
                except Exception as e:
                    print(f"⚠️ Błąd parsowania: {response} ({e})")

        return board_data

    def set_led(self, color, state):
        """
        Sterowanie LEDami dla figur białych lub czarnych.

        Args:
            color (str): 'WHITE' lub 'BLACK'
            state (str): 'ON' lub 'OFF'

        Returns:
            bool: True po wysłaniu komendy.
        """
        command = f"LED:{color},{state}"
        self.send_command(command)

        ack = self.wait_for_response()
        print(f"📥 Pico: {ack}")

        response = self.wait_for_response()
        print(f"📥 Pico: {response}")
        return True

    def get_status(self):
        """
        Pobierz aktualną pozycję głowicy.

        Returns:
            dict: {'x': float, 'y': float} z aktualnymi współrzędnymi,
                  None jeśli odczyt nie powiódł się.
        """
        self.send_command("STATUS")
        response = self.wait_for_response()
        print(f"📥 Pico: {response}")

        if response.startswith("POS:"):
            coords = response.split(":")[1].split(",")
            return {'x': float(coords[0]), 'y': float(coords[1])}
        return None

    def close(self):
        """
        Zamknij połączenie z Raspberry Pi Pico.
        """
        self.serial.close()
        print("🔌 Połączenie zamknięte")


def demo_program():
    """Program demonstracyjny pokazujący użycie klasy PicoController."""
    pico = PicoController()

    try:
        # 1. Homing
        print("\n=== TEST 1: HOMING ===")
        pico.homing()
        time.sleep(1)

        # 2. Sprawdź pozycję
        print("\n=== TEST 2: SPRAWDZENIE POZYCJI ===")
        status = pico.get_status()
        print(f"Aktualna pozycja: {status}")
        time.sleep(1)

        # 3. Ruch bez elektromagnesu
        print("\n=== TEST 3: RUCH BEZ ELEKTROMAGNESU ===")
        pico.move_to(0.0, 0.0, 50.0, 50.0, electromagnet=False)
        time.sleep(1)

        # 4. Włącz białe LEDy
        print("\n=== TEST 4: BIAŁE LEDY ===")
        pico.set_led('WHITE', 'ON')
        time.sleep(2)
        pico.set_led('WHITE', 'OFF')
        time.sleep(1)

        # 5. Ruch z elektromagnesem
        print("\n=== TEST 5: RUCH Z ELEKTROMAGNESEM ===")
        pico.move_to(50.0, 50.0, 100.0, 100.0, electromagnet=True)
        time.sleep(1)

        # 6. Włącz czarne LEDy
        print("\n=== TEST 6: CZARNE LEDY ===")
        pico.set_led('BLACK', 'ON')
        time.sleep(2)
        pico.set_led('BLACK', 'OFF')
        time.sleep(1)

        # 7. Pobierz status szachownicy
        print("\n=== TEST 7: STATUS SZACHOWNICY ===")
        board = pico.read_board()
        if board:
            print(f"Otrzymano dane dla {len(board)} pól")
            for field in board[:64]:
                print(f"  Pole {field['field']}: {'AKTYWNE' if field['status'] else 'NIEAKTYWNE'}")

        # 8. Powrót do (0,0)
        print("\n=== TEST 8: POWRÓT DO HOME ===")
        pico.homing()

        print("\n✅ Demo zakończone!")

    except KeyboardInterrupt:
        print("\n⚠️ Przerwano przez użytkownika")
    finally:
        pico.close()


if __name__ == "__main__":
    print("=== RASPBERRY PI 5 - MASTER CONTROL ===\n")
    demo_program()
