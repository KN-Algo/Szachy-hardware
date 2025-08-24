#include "pico/stdlib.h"
#include "Piny.h"


// Inicjalizacja pinów
void mux_init() {
    gpio_init(MUX_S0); gpio_set_dir(MUX_S0, GPIO_OUT);
    gpio_init(MUX_S1); gpio_set_dir(MUX_S1, GPIO_OUT);
    gpio_init(MUX_S2); gpio_set_dir(MUX_S2, GPIO_OUT);
    gpio_init(MUX_S3); gpio_set_dir(MUX_S3, GPIO_OUT);

    gpio_init(MUX1_SIG); gpio_set_dir(MUX1_SIG, GPIO_IN); gpio_pull_up(MUX1_SIG);
    gpio_init(MUX2_SIG); gpio_set_dir(MUX2_SIG, GPIO_IN); gpio_pull_up(MUX2_SIG);
    gpio_init(MUX3_SIG); gpio_set_dir(MUX3_SIG, GPIO_IN); gpio_pull_up(MUX3_SIG);
    gpio_init(MUX4_SIG); gpio_set_dir(MUX4_SIG, GPIO_IN); gpio_pull_up(MUX4_SIG);
}

// Ustaw adres na multiplexerze
void mux_set_channel(uint8_t channel) {
    gpio_put(MUX_S0, channel & 0x01);
    gpio_put(MUX_S1, (channel >> 1) & 0x01);
    gpio_put(MUX_S2, (channel >> 2) & 0x01);
    gpio_put(MUX_S3, (channel >> 3) & 0x01);
    sleep_us(2); // krótka stabilizacja
}

// Odczytaj wszystkie stany z jednego multiplexer
void mux_read_all(uint mux_sig_pin, uint8_t *states) {
    for (uint8_t ch = 0; ch < 16; ch++) {
        mux_set_channel(ch);
        states[ch] = gpio_get(mux_sig_pin);
    }
}

// Odczytaj wszystkie stany z 4 multiplexerów
void mux_read_4(uint8_t states[4][16]) {
    mux_read_all(MUX1_SIG, states[0]);
    mux_read_all(MUX2_SIG, states[1]);
    mux_read_all(MUX3_SIG, states[2]);
    mux_read_all(MUX4_SIG, states[3]);
}

// Odczytaj stany jako 8 tablic po 8 elementów
void mux_read_8x8(uint8_t states[8][8]) {
    uint8_t temp[4][16];
    mux_read_4(temp);

    for (int mux = 0; mux < 4; mux++) {
        for (int ch = 0; ch < 16; ch++) {
            int idx = mux * 2 + (ch / 8);      // 0..7 (wiersz)
            int subidx = ch % 8;               // 0..7 (kolumna)

            // Figura = 1, brak figury = 0
            states[idx][subidx] = (temp[mux][ch] == 0) ? 1 : 0;
        }
    }
}

