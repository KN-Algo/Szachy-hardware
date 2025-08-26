# 🏁 Robot szachowy z napędem CoreXY - Instrukcja użycia

Tu masz wszystko łopatologicznie rozpisane, coby każdy kumaty na Ślōnsku mógł to ogarnąć.

---

## 1️⃣ Homing – `send_homing()`

Funkcja, co robi kalibrację osi CoreXY, czyli ustawia nasze silniki na początkowe pozycje.  
Po wysłaniu komendy `'H'` do Pico funkcja czeka, aż Pico potwierdzi, że homing się skończył.

**Przykład użycia:**
```python
controller.send_homing()
```

**Działanie:**
* wysyła `'H'` do Pico
* czeka w pętli na odpowiedź `'H'`
* jeśli odbierze – zwraca `True` ✅ 
* jeśli nie odbierze w zadanym czasie – zwraca `False` ❌

---

## 2️⃣ Ruch figur – `send_move(x_start, y_start, x_end, y_end)`

Ta funkcja przesuwa figurę po planszy.
Parametry to współrzędne startu i końca w milimetrach.

**Przykład użycia:**
```python
controller.send_move(0.0, 0.0, 30.0, 40.0)
```

**Działanie:**
* wysyła komendę **`'M'`** + 4 floaty w **little endian**
* najpierw ruch na pozycję startową, potem na docelową
* Pico potwierdza wykonanie odpowiedzią `'M'`
* funkcja zwraca `True`/`False` (✅ albo ❌)

**Parametry:**
* `x_start`, `y_start` – pozycja początkowa figury (mm)
* `x_end`, `y_end` – pozycja końcowa figury (mm)

---

## 3️⃣ Odczyt stanu planszy – `read_board()`

Funkcja do pobrania aktualnego stanu planszy 8x8, gdzie każda komórka to 8-bitowa liczba.

**Przykład użycia:**
```python
board = controller.read_board()
print("Stan planszy:")
for row in board:
    print(row)
```

**Działanie:**
* wysyła `'B'` do Pico
* odbiera 64 bajty odpowiadające planszy
* zwraca macierz 8x8 (lista list)
* każdy element to liczba 0-255 oznaczająca typ figury

---

## 4️⃣ Test połączenia – `test_connection()`

Sprawdza czy komunikacja I2C działa.

**Przykład użycia:**
```python
if controller.test_connection():
    print("Połączenie OK!")
else:
    print("Brak połączenia!")
```

---

## 5️⃣ Status urządzenia – `get_device_status()`

Odczytuje aktualny status robota.

**Przykład użycia:**
```python
status_byte, opis = controller.get_device_status()
print(f"Status: {opis}")
```

**Kody statusu:**
* `'M'` – Ruch zakończony
* `'H'` – Homing zakończony  
* `'W'` – Praca w toku
* `'E'` – Błąd
* `'I'` – Bezczynny/Gotowy

---

## 🚀 Jak to używać w praktyce

```python
from chess_library import create_chess_controller

# Stwórz kontroler
controller = create_chess_controller()

# 1. Najpierw homing, coby wiedzieć gdzie startujemy
if controller.send_homing():
    print("✅ Homing OK")
else:
    print("❌ Homing nieudany")
    exit()

# 2. Potem ruch figury
success = controller.send_move(0.0, 0.0, 30.0, 40.0)
if success:
    print("✅ Figura przesunięta")
else:
    print("❌ Ruch nieudany")

# 3. I odczyt stanu planszy
try:
    board = controller.read_board()
    print("📋 Plansza odczytana:")
    for i, row in enumerate(board):
        print(f"Rząd {i}: {row}")
except Exception as e:
    print(f"❌ Błąd odczytu planszy: {e}")

# 4. Zamknij połączenie
controller.close()
```

---

## 🧪 Szybki test całego systemu

```python
from chess_library import run_chess_system_test

# Uruchom wszystkie testy
results = run_chess_system_test(verbose=True)

# Sprawdź czy wszystko działa
if all(result['success'] for result in results.values()):
    print("🎉 Wszystkie testy OK!")
else:
    print("⚠️ Niektóre testy nieudane")
```

---

## 💡 **Tip dla kumatych:**

Nie trzeba się martwić, jak Pico coś długo robi – funkcje same czekają w pętli, aż odpowiedź przyjdzie.
Nie ma tu żadnych magicznych `sleep(0.05)` blokujących wszystko na amen.

**Kolejność zawsze taka:**
1. `send_homing()` – kalibracja
2. `send_move()` – ruchy figur  
3. `read_board()` – sprawdzenie planszy
4. `controller.close()` – sprzątanie

---

## 🔧 Rozwiązywanie problemów

**Jeśli coś nie działa:**
* Sprawdź połączenia I2C (SDA, SCL)  
* Zweryfikuj adres urządzenia (domyślnie 0x42)
* Upewnij się, że Pico jest zasilane
* Użyj `run_chess_system_test()` do diagnozy

**Typowe błędy:**
* `❌ Połączenie nieudane` → Sprawdź kable I2C
* `❌ Homing timeout` → Pico może być zajęte lub zablokowane
* `❌ Ruch nieudany` → Współrzędne poza zakresem lub kolizja
