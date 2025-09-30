# 🏁 Robot szachowy z napędem CoreXY - Instrukcja użycia

***move_to***
-------------
Opis: Przesuwa głowicę od zadanej pozycji startowej do końcowej, opcjonalnie włączając elektromagnes.
Argumenty:
    start_x: Pozycja startowa X w mm
    start_y: Pozycja startowa Y w mm
    end_x: Pozycja końcowa X w mm
    end_y: Pozycja końcowa Y w mm
    electromagnet: True/False - czy włączyć elektromagnes
Zwraca: True jeśli ruch zakończony sukcesem, False w przeciwnym wypadku
Przykład użycia:
    pico.move_to(0,0,50,50, electromagnet=True)

***homing***
-------------
Opis: Wykonuje procedurę homing, ustawiając głowicę w pozycji (0,0)
Argumenty: Brak
Zwraca: True jeśli homing zakończony sukcesem, False w przeciwnym wypadku
Przykład użycia:
    pico.homing()

***read_board***
----------------
Opis: Pobiera status wszystkich pól szachownicy.
Argumenty: Brak
Zwraca: Lista słowników [{'field': 'A1', 'status': True/False}, ...]
Przykład użycia:
    board = pico.read_board()
    for field in board:
        print(field['field'], field['status'])

***set_led***
------------
Opis: Steruje LEDami dla figur białych lub czarnych.
Argumenty:
    color: 'WHITE' lub 'BLACK'
    state: 'ON' lub 'OFF'
Zwraca: True po wysłaniu komendy
Przykład użycia:
    pico.set_led('WHITE', 'ON')

***get_status***
----------------
Opis: Pobiera aktualną pozycję głowicy.
Argumenty: Brak
Zwraca: Słownik {'x': float, 'y': float} z aktualnymi współrzędnymi lub None przy błędzie
Przykład użycia:
    pos = pico.get_status()
    print(pos['x'], pos['y'])

***close***
-----------
Opis: Zamyka połączenie z Raspberry Pi Pico.
Argumenty: Brak
Zwraca: Brak
Przykład użycia:
    pico.close()

