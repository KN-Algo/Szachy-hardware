#include "pico/stdlib.h"
#include "Piny.h"

// Inicjalizacja pinów
void mux_init() {
    // Linie adresowe wspólne
    gpio_init(MUX_S0); gpio_set_dir(MUX_S0, GPIO_OUT);
    gpio_init(MUX_S1); gpio_set_dir(MUX_S1, GPIO_OUT);
    gpio_init(MUX_S2); gpio_set_dir(MUX_S2, GPIO_OUT);
    gpio_init(MUX_S3); gpio_set_dir(MUX_S3, GPIO_OUT);

    // Linie EN – osobne dla każdego MUX
    gpio_init(MUX1_EN); gpio_set_dir(MUX1_EN, GPIO_OUT); gpio_put(MUX1_EN, 0);
    gpio_init(MUX2_EN); gpio_set_dir(MUX2_EN, GPIO_OUT); gpio_put(MUX2_EN, 0);
    gpio_init(MUX3_EN); gpio_set_dir(MUX3_EN, GPIO_OUT); gpio_put(MUX3_EN, 0);
    gpio_init(MUX4_EN); gpio_set_dir(MUX4_EN, GPIO_OUT); gpio_put(MUX4_EN, 0);

    // Wspólna linia SIG
    gpio_init(MUX_SIG); 
    gpio_set_dir(MUX_SIG, GPIO_IN); 
    gpio_pull_up(MUX_SIG);
}

// Ustaw adres na liniach S0–S3
static inline void mux_set_channel(uint8_t channel) {
    gpio_put(MUX_S0, channel & 0x01);
    gpio_put(MUX_S1, (channel >> 1) & 0x01);
    gpio_put(MUX_S2, (channel >> 2) & 0x01);
    gpio_put(MUX_S3, (channel >> 3) & 0x01);
    sleep_us(2); // krótka stabilizacja
}

// Włącz jeden multiplexer (aktywny = 1), resztę wyłącz
static inline void mux_enable(int mux_num) {
    gpio_put(MUX1_EN, (mux_num == 1));
    gpio_put(MUX2_EN, (mux_num == 2));
    gpio_put(MUX3_EN, (mux_num == 3));
    gpio_put(MUX4_EN, (mux_num == 4));
}

// Odczytaj wszystkie kanały z jednego muxa
void mux_read_all(int mux_num, uint8_t *states) {
    for (uint8_t ch = 0; ch < 16; ch++) {
        mux_enable(mux_num);         // włącz tylko wybrany mux
        mux_set_channel(ch);         // ustaw adres
        states[ch] = gpio_get(MUX_SIG);
    }
    mux_enable(0); // wyłącz wszystkie na koniec
}

// Odczytaj wszystkie 4 muxy (4x16 = 64 stany)
void mux_read_4(uint8_t states[4][16]) {
    mux_read_all(1, states[0]);
    mux_read_all(2, states[1]);
    mux_read_all(3, states[2]);
    mux_read_all(4, states[3]);
}

// Odczytaj w postaci 8x8
void mux_read_8x8(uint8_t states[8][8]) {
    uint8_t temp[4][16];
    mux_read_4(temp);

    for (int mux = 0; mux < 4; mux++) {
        for (int ch = 0; ch < 16; ch++) {
            int idx = mux * 2 + (ch / 8); // 0..7
            int subidx = ch % 8;          // 0..7
            // Figura = 1, brak figury = 0
            states[idx][subidx] = (temp[mux][ch] == 0) ? 1 : 0;
        }
    }
}
