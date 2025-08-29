#include "hardware/gpio.h"
#include "Piny.h"
// Inicjalizacja pinów LED
void led_init() {
    gpio_init(LED_CZARNE);
    gpio_set_dir(LED_CZARNE, GPIO_OUT);
    gpio_init(LED_BIALE);
    gpio_set_dir(LED_BIALE, GPIO_OUT);
}

// Włączenie LED
void led_czarny_on() {
    gpio_put(LED_CZARNE, 1);
}

// Wyłączenie LED
void led_czarny_off() {
    gpio_put(LED_CZARNE, 0);
}

// Włączenie LED
void led_bialy_on() {
    gpio_put(LED_BIALE, 1);
}

// Wyłączenie LED
void led_bialy_off() {
    gpio_put(LED_BIALE, 0);
}
