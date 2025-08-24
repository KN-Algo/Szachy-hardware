
# Szachy z napędem CoreXY

Tu miołech Wam wszystko łopatologicznie rozpisać, coby każdy kumaty na Ślōnsku mógł to ogarnąć.

---

## 1️⃣ Homing – `send_homing()`

Funkcja, co robi kalibrycję osi CoreXY, czyli ustawia nasze silniki na początkowe pozycje.  
Po wysłaniu komendy `'H'` do Pico funkcja czeka, aż Pico potwierdzi, że homing się skończył.

**Przykład użycia:**
```python
send_homing()
````

**Działanie:**

* wysyła `'H'` do Pico
* czeka w pętli na odpowiedź `'H'`
* jeśli odbierze – wypisuje `✅ Homing wykonany`
* jeśli nie odbierze w zadanym czasie – `❌ Homing nie powiódł się`

---

## 2️⃣ Ruch figur – `send_move(x_start, y_start, x_end, y_end)`

Ta funkcja przesuwa figurę po planszy.
Parametry to współrzędne startu i końca w milimetrach.

**Przykład użycia:**

```python
send_move(0.0, 0.0, 3.0, 4.0)
```

**Działanie:**

* wysyła komendę `'M'` + 4 floaty w **little endian**
* najpierw ruch na pozycję startową, potem na docelową
* Pico potwierdza wykonanie ruchem `'M'`
* funkcja wypisuje status (✅ albo ❌)

**Parametry:**

* `x_start`, `y_start` – pozycja początkowa figury
* `x_end`, `y_end` – pozycja końcowa figury

---

## 3️⃣ Odczyt stanu planszy – `read_board()`

Funkcja do pobrania aktualnego stanu planszy 8x8, gdzie każda komórka to 8-bitowa liczba.

**Przykład użycia:**

```python
board = read_board()
```

**Działanie:**

* wysyła `'B'` do Pico
* odbiera 64 bajty odpowiadające planszy
* zwraca listę list 8x8
* wypisuje planszę w konsoli, coby widzieć co się dzieje

---

## 4️⃣ Jak to używać w praktyce

```python
# Najpierw homing, coby wiedzieć gdzie startujemy
send_homing()

# Potem ruch figury
send_move(0.0, 0.0, 3.0, 4.0)

# I odczyt stanu planszy
board = read_board()
```

---

💡 **Tip dla Ślōnskich kumatych:**
Nie trzeba się martwić, jak Pico coś długo robi – funkcje same czekają w pętli, aż odpowiedź przyjdzie.
Nie ma tu żadnych magicznych `sleep(0.05)` blokujących wszystko na amen.

```

Jeżeli chcesz, mogę teraz zrobić **wersję jeszcze bardziej „czytelną” z nagłówkami, emoji i tabelką parametrów funkcji**, żeby wyglądało profesjonalnie na GitHubie. Chcesz, żebym taką zrobił?
```
