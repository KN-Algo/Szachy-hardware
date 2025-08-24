#include "corexy.h"
#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include "pico/stdlib.h"
#include "hardware/gpio.h"

// --- Parametry ruchu ---
const uint32_t ACCEL_STEPS = 1000;
const uint32_t DECEL_STEPS = 1000;
const uint32_t MAX_SPEED_US = 100;
const uint32_t MIN_SPEED_US = 1200;

const float steps_per_mm = (STEPS_PER_REV * MICROSTEPS) / (PULLEY_TEETH * PITCH);

// --- Globalna pozycja aktualna ---
float current_x = 0.0f;
float current_y = 0.0f;

// --- Inicjalizacja GPIO ---
void corexy_init_gpio() {
    gpio_init(STEP_PIN_X); gpio_set_dir(STEP_PIN_X, GPIO_OUT);
    gpio_init(DIR_PIN_X);  gpio_set_dir(DIR_PIN_X, GPIO_OUT);
    gpio_init(STEP_PIN_Y); gpio_set_dir(STEP_PIN_Y, GPIO_OUT);
    gpio_init(DIR_PIN_Y);  gpio_set_dir(DIR_PIN_Y, GPIO_OUT);

    gpio_init(ENDSTOP_X_PIN); gpio_set_dir(ENDSTOP_X_PIN, GPIO_IN); gpio_pull_up(ENDSTOP_X_PIN);
    gpio_init(ENDSTOP_Y_PIN); gpio_set_dir(ENDSTOP_Y_PIN, GPIO_IN); gpio_pull_up(ENDSTOP_Y_PIN);
}

// --- Pojedynczy krok CoreXY ---
void corexy_step(bool dir_a, bool dir_b, uint32_t step_delay_us) {
    gpio_put(DIR_PIN_X, dir_a);
    gpio_put(DIR_PIN_Y, dir_b);

    gpio_put(STEP_PIN_X, 1);
    gpio_put(STEP_PIN_Y, 1);
    sleep_us(100);
    gpio_put(STEP_PIN_X, 0);
    gpio_put(STEP_PIN_Y, 0);
    sleep_us(step_delay_us);
}

// --- Ruch CoreXY z rampą ---
void corexy_move_ramp(int x_steps, int y_steps) {
    int dx = abs(x_steps), sx = x_steps >= 0 ? 1 : -1;
    int dy = abs(y_steps), sy = y_steps >= 0 ? 1 : -1;
    int err = (dx > dy ? dx : -dy) / 2, e2;
    int steps = dx > dy ? dx : dy;

    for (int i = 0; i < steps; i++) {
        uint delay = MAX_SPEED_US;
        if (i < ACCEL_STEPS)
            delay = MIN_SPEED_US - (MIN_SPEED_US - MAX_SPEED_US) * i / ACCEL_STEPS;
        else if (i > steps - DECEL_STEPS)
            delay = MIN_SPEED_US - (MIN_SPEED_US - MAX_SPEED_US) * (steps - i) / DECEL_STEPS;
        if (delay < MAX_SPEED_US) delay = MAX_SPEED_US;
        if (delay > MIN_SPEED_US) delay = MIN_SPEED_US;

        int a_dir = ((sx + sy) >= 0) ? 1 : 0;
        int b_dir = ((sx - sy) >= 0) ? 1 : 0;
        corexy_step(a_dir, b_dir, delay);

        e2 = err;
        if (e2 > -dx) { err -= dy; x_steps += sx; }
        if (e2 < dy)  { err += dx; y_steps += sy; }
    }
}

// --- Homing ---
void corexy_home(void) {
    printf("Homing X...\n");
    gpio_put(DIR_PIN_X, 0);
    gpio_put(DIR_PIN_Y, 1);

    while (!gpio_get(ENDSTOP_X_PIN)) {
        corexy_step(0, 1, MIN_SPEED_US);
    }
    sleep_ms(200);

    printf("Homing Y...\n");
    gpio_put(DIR_PIN_X, 1);
    gpio_put(DIR_PIN_Y, 0);

    while (!gpio_get(ENDSTOP_Y_PIN)) {
        corexy_step(1, 0, MIN_SPEED_US);
    }
    sleep_ms(200);

    current_x = 0.0f;
    current_y = 0.0f;

    printf("Homing done! Aktualna pozycja: (%.2f, %.2f)\n", current_x, current_y);
}

// --- Ruch do pozycji ---
void corexy_move_to(float start_x, float start_y, float end_x, float end_y, bool enable_electromagnet) {
    // Ustal różnicę w krokach
    int dx_steps = (int)((end_x - start_x) * steps_per_mm);
    int dy_steps = (int)((end_y - start_y) * steps_per_mm);

    // Elektromagnes
    if (enable_electromagnet) {
        elektromagnes_set_power(100); // np. pełna moc
    } else {
        elektromagnes_off();
    }

    // Ruch
    corexy_move_ramp(dx_steps, dy_steps);

    // Aktualizacja pozycji globalnej
    current_x = end_x;
    current_y = end_y;

    printf("Move done! Now at: (%.2f, %.2f)\n", current_x, current_y);
}
