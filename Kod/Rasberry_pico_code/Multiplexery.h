#pragma once
#include "pico/stdlib.h"

// Inicjalizacja pinów multiplexerów
void mux_init(void);

// Ustawienie kanału na multiplexerze (0-15)
void mux_set_channel(uint8_t channel);

// Odczyt wszystkich stanów z jednego multiplexer (16 wejść)
void mux_read_all(uint mux_sig_pin, uint8_t *states);

// Odczyt wszystkich stanów z 4 multiplexerów (4x16 wejść)
void mux_read_4(uint8_t states[4][16]);

//Odczytanie stanu planszy ale w formacie 8x8
void mux_read_8x8(uint8_t states[8][8]);

// Wypisanie wszystkich stanów do konsoli (debug)