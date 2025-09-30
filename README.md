# 🏁 Robot szachowy z napędem CoreXY - Instrukcja użycia

## `move_to(start_x, start_y, end_x, end_y, electromagnet=False)`

Przesuwa głowicę od pozycji startowej do końcowej. Opcjonalnie włącza elektromagnes podczas ruchu.

**Argumenty:**

* `start_x` (float): Pozycja startowa X w mm
* `start_y` (float): Pozycja startowa Y w mm
* `end_x` (float): Pozycja końcowa X w mm
* `end_y` (float): Pozycja końcowa Y w mm
* `electromagnet` (bool): Włącz elektromagnes jeśli True

**Zwraca:**
`True` jeśli ruch zakończony sukcesem, `False` w przeciwnym wypadku.

**Przykład użycia:**

```python
pico.move_to(0, 0, 50, 50, electromagnet=True)
```

---

## `homing()`

Wykonuje procedurę homing, ustawiając głowicę w pozycji (0,0).

**Argumenty:** Brak

**Zwraca:**
`True` jeśli homing zakończony sukcesem, `False` w przeciwnym wypadku.

**Przykład użycia:**

```python
pico.homing()
```

---

## `read_board()`

Pobiera status wszystkich pól szachownicy.

**Argumenty:** Brak

**Zwraca:**
Lista słowników w formacie:

```python
[{'field': 'A1', 'status': True}, {'field': 'B1', 'status': False}, ...]
```

**Przykład użycia:**

```python
board = pico.read_board()
for field in board:
    print(field['field'], 'AKTYWNE' if field['status'] else 'NIEAKTYWNE')
```

---

## `set_led(color, state)`

Steruje LEDami dla figur białych lub czarnych.

**Argumenty:**

* `color` (str): `'WHITE'` lub `'BLACK'`
* `state` (str): `'ON'` lub `'OFF'`

**Zwraca:**
`True` po wysłaniu komendy.

**Przykład użycia:**

```python
pico.set_led('WHITE', 'ON')
pico.set_led('BLACK', 'OFF')
```

---

## `get_status()`

Pobiera aktualną pozycję głowicy.

**Argumenty:** Brak

**Zwraca:**
Słownik z aktualnymi współrzędnymi:

```python
{'x': float, 'y': float}
```

lub `None` jeśli odczyt nie powiódł się.

**Przykład użycia:**

```python
pos = pico.get_status()
print(f"X: {pos['x']}, Y: {pos['y']}")
```

---

## `close()`

Zamyka połączenie z Raspberry Pi Pico.

**Argumenty:** Brak

**Zwraca:** Brak

**Przykład użycia:**

```python
pico.close()
```

---

## Przykładowy program demonstracyjny

```python
pico = PicoController()

# Homing
pico.homing()

# Sprawdzenie pozycji
status = pico.get_status()
print(status)

# Ruch z elektromagnesem
pico.move_to(0, 0, 50, 50, electromagnet=True)

# Sterowanie LEDami
pico.set_led('WHITE','ON')
pico.set_led('BLACK','OFF')

# Pobranie statusu szachownicy
board = pico.read_board()
for field in board[:5]:
    print(field['field'], 'AKTYWNE' if field['status'] else 'NIEAKTYWNE')

# Zamknięcie połączenia
pico.close()
```

---


