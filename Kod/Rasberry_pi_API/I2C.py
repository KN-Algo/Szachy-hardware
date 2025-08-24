import smbus2
import struct
import time

I2C_BUS = 1
PICO_ADDR = 0x42  # adres slave Pico

bus = smbus2.SMBus(I2C_BUS)

# ============================ FUNKCJA POMOCNICZA ============================
def wait_for_response(expected_char, timeout=10.0):
    """
    Czeka na odpowiedź od Pico.
    expected_char - znak, którego oczekujemy ('H' lub 'M')
    timeout - maksymalny czas oczekiwania w sekundach
    """
    start = time.time()
    while True:
        try:
            resp = bus.read_byte(PICO_ADDR)
            if chr(resp) == expected_char:
                return True
        except OSError:
            # Brak danych, spróbuj ponownie
            pass

        if time.time() - start > timeout:
            print(f"❌ Timeout oczekiwania na {expected_char}")
            return False

        time.sleep(0.01)  # krótka przerwa między próbami

# ============================ HOMING ============================
def send_homing():
    """Wyślij komendę homingu do Pico i poczekaj na potwierdzenie"""
    bus.write_byte(PICO_ADDR, ord('H'))
    if wait_for_response('H'):
        print("✅ Homing wykonany")
    else:
        print("❌ Homing nie powiódł się")

# ============================ RUCH ============================
def send_move(x_start, y_start, x_end, y_end):
    """
    Wyślij komendę ruchu do Pico.
    Parametry: współrzędne start i end (float)
    """
    data = struct.pack('<cffff', b'M', x_start, y_start, x_end, y_end)
    bus.write_byte(PICO_ADDR, data[0])
    bus.write_i2c_block_data(PICO_ADDR, 0, list(data[1:]))

    if wait_for_response('M'):
        print(f"✅ Ruch {x_start},{y_start} -> {x_end},{y_end} wykonany")
    else:
        print(f"❌ Ruch {x_start},{y_start} -> {x_end},{y_end} nie powiódł się")

# ============================ ODCZYT PLANSZY ============================
def read_board():
    """Wyślij komendę B i odczytaj 64 bajty tablicy 8x8"""
    bus.write_byte(PICO_ADDR, ord('B'))
    time.sleep(0.05)  # krótka przerwa, żeby Pico przygotowało dane
    try:
        data = bus.read_i2c_block_data(PICO_ADDR, 0, 64)
    except OSError:
        print("❌ Błąd odczytu planszy")
        return None

    board = [[data[row * 8 + col] for col in range(8)] for row in range(8)]
    print("✅ Aktualna plansza:")
    for row in board:
        print(row)
    return board

# ============================ TEST ============================
if __name__ == "__main__":
    # Homing
    send_homing()

    # Ruch przykładowy
    send_move(0.0, 0.0, 3.0, 4.0)

    # Odczyt planszy
    board = read_board()
