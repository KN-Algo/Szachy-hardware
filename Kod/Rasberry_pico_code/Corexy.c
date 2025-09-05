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

// --- Pojedynczy krok silników A i B ---
static void corexy_step_AB(bool dirA, bool dirB, uint32_t step_delay_us) {
    gpio_put(DIR_PIN_X, dirA);   // silnik A
    gpio_put(DIR_PIN_Y, dirB);   // silnik B

    gpio_put(STEP_PIN_X, 1);
    gpio_put(STEP_PIN_Y, 1);
    sleep_us(5);   // krótki impuls STEP
    gpio_put(STEP_PIN_X, 0);
    gpio_put(STEP_PIN_Y, 0);

    sleep_us(step_delay_us);
}

// --- Ruch CoreXY z rampą ---
// wejście: kroki w osiach kartezjańskich (X, Y)
void corexy_move_ramp(int dx_steps, int dy_steps) {
    // przelicz na ruchy silników A i B
    int a_steps = dx_steps + dy_steps;
    int b_steps = dx_steps - dy_steps;

    int da = abs(a_steps), sa = (a_steps >= 0) ? 1 : -1;
    int db = abs(b_steps), sb = (b_steps >= 0) ? 1 : -1;

    int err = (da > db ? da : -db) / 2, e2;
    int steps = (da > db ? da : db);

    for (int i = 0; i < steps; i++) {
        // rampowanie prędkości
        uint delay = MAX_SPEED_US;
        if (i < ACCEL_STEPS)
            delay = MIN_SPEED_US - (MIN_SPEED_US - MAX_SPEED_US) * i / ACCEL_STEPS;
        else if (i > steps - DECEL_STEPS)
            delay = MIN_SPEED_US - (MIN_SPEED_US - MAX_SPEED_US) * (steps - i) / DECEL_STEPS;

        if (delay < MAX_SPEED_US) delay = MAX_SPEED_US;
        if (delay > MIN_SPEED_US) delay = MIN_SPEED_US;

        // kierunki A i B
        bool dirA = (sa > 0);
        bool dirB = (sb > 0);

        // wykonaj krok
        corexy_step_AB(dirA, dirB, delay);

        // Bresenham między A i B
        e2 = err;
        if (e2 > -da) { err -= db; a_steps -= sa; }
        if (e2 < db)  { err += da; b_steps -= sb; }
    }
}

// --- Homing ---
void corexy_home(void) {
    printf("Homing X...\n");
    while (!gpio_get(ENDSTOP_X_PIN)) {
        // X- ruch = A- + B- (czyli w praktyce dobierz zgodnie z geometrią)
        corexy_step_AB(0, 0, MIN_SPEED_US);
    }
    sleep_ms(200);

    printf("Homing Y...\n");
    while (!gpio_get(ENDSTOP_Y_PIN)) {
        // Y- ruch = A- + B+ (do sprawdzenia kierunki!)
        corexy_step_AB(0, 1, MIN_SPEED_US);
    }
    sleep_ms(200);

    current_x = 0.0f;
    current_y = 0.0f;

    printf("Homing done! Aktualna pozycja: (%.2f, %.2f)\n", current_x, current_y);
}

// --- Ruch do pozycji ---
void corexy_move_to(float start_x, float start_y, float end_x, float end_y, bool enable_electromagnet) {
    int dx_steps = (int)((end_x - start_x) * steps_per_mm);
    int dy_steps = (int)((end_y - start_y) * steps_per_mm);

    if (enable_electromagnet) {
        elektromagnes_set_power(100);
    } else {
        elektromagnes_off();
    }

    corexy_move_ramp(dx_steps, dy_steps);

    current_x = end_x;
    current_y = end_y;

    printf("Move done! Now at: (%.2f, %.2f)\n", current_x, current_y);
}
